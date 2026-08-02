"""Executor workflow node."""

from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ...core.llm import llm, safe_invoke
from ...domain.enums import StepStatus
from ...domain.models import Artifact, ExecutionRecord, Plan
from ...services.context import build_context
from ...services.execution import current_step, missing_dependencies, required_chart_metrics
from ...domain.contracts import contract_for
from ...tools import TOOLS
from ..state import AgentState


def _chart_data_from_results(state: AgentState, title: str = "") -> list[dict] | None:
    """Project the latest SQL result into chart points without model-copied data."""
    for result in reversed(state.get("tool_results", [])):
        rows = (result.result or {}).get("rows") if result.tool == "run_sql" else None
        if not isinstance(rows, list) or not rows or not all(isinstance(row, dict) for row in rows):
            continue

        if all({"label", "value"}.issubset(row) for row in rows):
            return [{"label": row["label"], "value": row["value"]} for row in rows]

        first_row = rows[0]
        label_key = next(
            (key for key in ("month", "date", "order_date") if key in first_row), None
        )
        numeric_keys = [
            key
            for key, value in first_row.items()
            if key != label_key and isinstance(value, (int, float)) and not isinstance(value, bool)
        ]
        if not label_key or not numeric_keys:
            continue

        title_words = title.lower().replace("_", " ").split()
        value_key = next(
            (key for key in numeric_keys if any(word in key.lower() for word in title_words)),
            numeric_keys[0],
        )
        if all(label_key in row and value_key in row for row in rows):
            return [{"label": row[label_key], "value": row[value_key]} for row in rows]
    return None


def _chart_series_from_results(state: AgentState, metrics: list[str]) -> list[dict] | None:
    """Build multi-series chart arguments directly from the latest SQL rows."""
    for result in reversed(state.get("tool_results", [])):
        rows = (result.result or {}).get("rows") if result.tool == "run_sql" else None
        if not isinstance(rows, list) or not rows or not all(isinstance(row, dict) for row in rows):
            continue

        first_row = rows[0]
        label_key = next(
            (key for key in ("label", "month", "date", "order_date") if key in first_row), None
        )
        if not label_key:
            continue

        series = []
        for metric in metrics:
            metric_key = next(
                (key for key in first_row if metric.lower() in key.lower()), None
            )
            if not metric_key or not all(metric_key in row and label_key in row for row in rows):
                return None
            series.append(
                {
                    "name": metric.replace("_", " ").title(),
                    "data": [
                        {"label": row[label_key], "value": row[metric_key]}
                        for row in rows
                    ],
                }
            )
        return series
    return None


def executor(state: AgentState) -> dict:
    print("➡️ Executor")

    trace = list(state.get("trace", []))

    if state.get("repair_attempts", 0):
        trace.append(
            f"🔁 Repair Attempt #{state['repair_attempts']}"
        )

    trace.append("🧠 Context built")

    plan = state.get("plan")
    step = current_step(plan)
    if step is None:
        return {"step_validation_error": "No executable plan step is available.", "trace": trace}

    contract = contract_for(step.expected_tool)
    if step.expected_tool and contract is None:
        return {
            "step_validation_error": f"No contract is registered for tool {step.expected_tool}.",
            "trace": trace,
        }
    if contract and step.action not in contract.supported_actions:
        return {
            "step_validation_error": (
                f"Tool contract violation: {step.expected_tool} cannot execute "
                f"{step.action.value}."
            ),
            "trace": trace,
        }

    missing = missing_dependencies(step, state.get("tool_results", []), plan)
    if missing:
        return {
            "step_validation_error": (
                f"Step '{step.description}' requires successful output from: "
                f"{', '.join(missing)}."
            ),
            "trace": trace,
        }

    response = None
    if step.expected_tool == "generate_chart":
        # Chart inputs are fully determined by the validated SQL artifact.
        # Calling the LLM again adds latency/cost without adding a decision.
        if step.expected_output == "multi_series_line_chart":
            chart_series = _chart_series_from_results(state, step.inputs)
            if not chart_series:
                return {
                    "step_validation_error": (
                        "Multi-series chart generation requires prior SQL rows for: "
                        f"{', '.join(step.inputs)}."
                    ),
                    "trace": trace,
                }
            chart_args = {"chart_type": "line", "title": step.description, "series": chart_series}
        else:
            chart_data = _chart_data_from_results(state, step.description)
            if not chart_data:
                return {
                    "step_validation_error": "Chart generation requires prior run_sql rows with label and value fields.",
                    "trace": trace,
                }
            chart_args = {"chart_type": "line", "title": step.description, "data": chart_data}
        response = AIMessage(
            content="",
            tool_calls=[{"name": "generate_chart", "args": chart_args, "id": f"chart_{uuid4().hex}", "type": "tool_call"}],
        )

    context = build_context(state)
    # The compact context already carries the relevant plan, results, memory,
    # and knowledge. Replaying every historical AI/tool message duplicates SQL
    # rows and quickly exhausts provider token-per-minute limits.
    user_message = next(
        (message for message in reversed(state["messages"]) if isinstance(message, HumanMessage)),
        HumanMessage(content="Continue the planned analysis."),
    )
    if step.expected_tool and response is None:
        # Tool selection is deterministic: the plan contract selects exactly
        # one tool. The model may provide only that tool's arguments.
        tool = next((candidate for candidate in TOOLS if candidate.name == step.expected_tool), None)
        if tool is None:
            return {
                "step_validation_error": f"Registered tool {step.expected_tool} is unavailable.",
                "trace": trace,
            }
        # Binding exactly one tool preserves deterministic routing. The
        # provider still needs an unambiguous instruction to serialize its
        # arguments as JSON (especially for SQL strings containing quotes).
        downstream_metrics = required_chart_metrics(plan, step)
        downstream_instruction = ""
        if downstream_metrics:
            aliases = ", ".join(downstream_metrics)
            downstream_instruction = (
                " The next step is a multi-series chart, so this SQL query must return "
                "a time/category label column plus numeric aggregate aliases for: "
                f"{aliases}. Do not return a single generic `value` column."
            )
        # Some smaller Groq models reject provider-level forced tool choice
        # even with a single bound tool. The executor still validates that the
        # only permitted tool is called, so leave selection to the model API.
        model = llm.bind_tools([tool])
        messages = [
            SystemMessage(
                content=(
                    f"{context}\n\n"
                    f"You must call `{step.expected_tool}` exactly once. Return its "
                    "arguments as a JSON object that matches the tool schema. "
                    'For `run_sql`, the only valid shape is {"query": "SELECT ..."}. '
                    "Never emit raw SQL as function content or outside the JSON argument object."
                    f"{downstream_instruction}"
                )
            ),
            user_message,
        ]
    elif not step.expected_tool:
        # Tool-call messages make providers treat a final synthesis as a tool
        # continuation. The full execution context already contains the user
        # question and tool outputs, so omit that protocol history here.
        model = llm
        messages = [
            SystemMessage(
                content=(
                    f"{context}\n\n"
                    "This is the final synthesis step. Do not call tools. "
                    "Answer the user directly using only the execution history, "
                    "with specific observations supported by the returned data."
                )
            ),
            HumanMessage(content="Provide the final answer now."),
        ]

    if response is None:
        response = safe_invoke(model, messages)

    print("\n===== TOOL CALLS =====")

    if response.tool_calls:
        for tool in response.tool_calls:
            print(f"Tool call -> {tool['name']}")

    updates: dict = {
        "messages": [response],
        "trace": trace,
        "step_validation_error": "",
    }

    if plan and step.expected_tool:
        step.status = StepStatus.RUNNING
        updates["plan"] = plan

    if step.expected_tool and not response.tool_calls:
        updates["step_validation_error"] = (
            f"Step '{step.description}' requires a {step.expected_tool} tool call."
        )
        updates["repair_needed"] = True
        updates["repair_reason"] = (
            f"The provider did not emit a tool call for {step.expected_tool}."
        )
        return updates

    if step.expected_tool and (
        len(response.tool_calls) != 1
        or response.tool_calls[0]["name"] != step.expected_tool
    ):
        updates["step_validation_error"] = (
            f"Step '{step.description}' permits exactly one "
            f"{step.expected_tool} call."
        )
        updates["repair_needed"] = True
        updates["repair_reason"] = (
            f"The provider returned an unexpected tool call for {step.expected_tool}."
        )
        return updates

    if not step.expected_tool and response.tool_calls:
        updates["step_validation_error"] = (
            f"Step '{step.description}' must produce a final response, not a tool call."
        )
        return updates

    if step.expected_tool == "generate_chart" and response.tool_calls:
        args = response.tool_calls[0]["args"]
        if step.expected_output == "multi_series_line_chart":
            chart_series = _chart_series_from_results(state, step.inputs)
            if not chart_series:
                updates["step_validation_error"] = (
                    "Multi-series chart generation requires prior SQL rows for: "
                    f"{', '.join(step.inputs)}."
                )
                return updates
            args["chart_type"] = "line"
            args["series"] = chart_series
            args.pop("data", None)
            return updates

        chart_data = _chart_data_from_results(state, args.get("title", ""))
        if not chart_data:
            updates["step_validation_error"] = (
                "Chart generation requires prior run_sql rows with label and value fields."
            )
            return updates
        # The model may choose presentation details, but dataset provenance is
        # deterministic: chart input always comes from the SQL tool result.
        args["data"] = chart_data

    # Only a contract with no expected tool may complete from an AI response.
    if not step.expected_tool and plan:
        step_number = plan.current_step + 1
        step = plan.steps[plan.current_step]
        step.status = StepStatus.COMPLETED
        updates["plan"] = Plan(
            goal=plan.goal,
            steps=plan.steps,
            current_step=plan.current_step + 1,
        )
        updates["execution_records"] = [
            *state.get("execution_records", []),
            ExecutionRecord(
                step_number=step_number,
                step=step.description,
                tool=None,
                tool_input=None,
                output={"response": str(response.content)},
                success=True,
            ),
        ]
        updates["artifacts"] = [
            *state.get("artifacts", []),
            Artifact(
                id=f"step_{step.id}_markdown",
                type="MARKDOWN_REPORT",
                producer="summarize",
                payload={"content": str(response.content)},
            ),
        ]
        updates["trace"] = [
            *trace,
            f"✅ Completed step {step_number}: {step.description}",
        ]

    return updates
