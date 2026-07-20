"""Executor workflow node."""

import json
from dataclasses import replace

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from ...core.llm import llm_with_required_tool, llm_with_tools, safe_invoke
from ...domain.models import ToolResult
from ...services.context import build_context
from ..state import AgentState


def _parse_tool_result(payload: dict, fallback_tool: str | None) -> ToolResult:
    """Convert a raw tool JSON response to the internal ToolResult shape."""
    result = payload.get("result")
    if result is None and payload.get("status") == "success":
        result = {
            key: value
            for key, value in payload.items()
            if key not in {"status", "tool", "message"}
        }

    if result is None and payload.get("query"):
        # Keep failed SQL visible to the repair prompt. The model otherwise
        # sees only a database error and can repeat the same query.
        result = {"query": payload["query"]}

    return ToolResult(
        tool=payload.get("tool", fallback_tool or "unknown"),
        status=payload.get("status", "error"),
        result=result,
        message=payload.get("message"),
    )


def _advance_plan_after_success(state: AgentState, tool_result: ToolResult):
    """Move to the next planned action after a successful tool observation."""
    plan = state.get("plan")
    if tool_result.status != "success" or not plan:
        return plan

    next_step = min(plan.current_step + 1, len(plan.steps) - 1)
    if next_step == plan.current_step:
        return plan

    return replace(plan, current_step=next_step)


def _plan_requires_another_tool(plan) -> bool:
    """Whether the current plan step precedes the final answer step."""
    return bool(plan and plan.steps and plan.current_step < len(plan.steps) - 1)


def executor(state: AgentState) -> dict:
    print("➡️ Executor")

    trace = list(state.get("trace", []))

    if state.get("repair_attempts", 0):
        trace.append(
            f"🔁 Repair Attempt #{state['repair_attempts']}"
        )

    trace.append("🧠 Context built")

    tool_results = [*state.get("tool_results", [])]
    plan = state.get("plan")
    last_message = state["messages"][-1]

    if isinstance(last_message, ToolMessage):
        try:
            payload = json.loads(last_message.content)

            tool_result = _parse_tool_result(payload, last_message.name)
            tool_results.append(tool_result)
            plan = _advance_plan_after_success(state, tool_result)

            trace.append(
                f"📊 {payload['tool']} -> {payload['status']}"
            )

        except json.JSONDecodeError:
            tool_results.append(
                ToolResult(
                    tool=last_message.name,
                    status="error",
                    result=None,
                    message="Tool returned invalid JSON.",
                )
            )

            trace.append("⚠️ Failed to parse tool output.")

    context = build_context(
        {
            **state,
            "tool_results": tool_results,
            "plan": plan,
        }
    )

    question = next(
        (
            message.content
            for message in reversed(state["messages"])
            if isinstance(message, HumanMessage)
        ),
        "Continue the analysis using the execution history.",
    )

    # ``context`` already contains the user question and compact execution
    # history. Re-sending every prior AI/tool message duplicates SQL rows and
    # can exceed smaller models' request-token limits.
    model = llm_with_required_tool if _plan_requires_another_tool(plan) else llm_with_tools
    response = safe_invoke(
        model,
        [
            SystemMessage(content=context),
            HumanMessage(content=question),
        ],
    )

    # Keep the graph safe if a provider ignores ``parallel_tool_calls=False``.
    # Later steps will be chosen after observing this first call's result.
    if len(response.tool_calls) > 1:
        trace.append("⚠️ Model requested multiple tools; executing the first call only.")
        response = response.model_copy(update={"tool_calls": response.tool_calls[:1]})

    print("\n===== TOOL CALLS =====")

    if response.tool_calls:
        for tool in response.tool_calls:
            print(f"Tool call -> {tool['name']}")

    result = {
        "messages": [response],
        "trace": trace,
        "tool_results": tool_results,
    }
    if plan is not None:
        result["plan"] = plan
    return result
