from langchain_core.messages import HumanMessage

from ..tools import get_schema_text
from ..utils.console import pretty_json


def _compact(value: object, limit: int = 900) -> str:
    text = str(value)
    return text if len(text) <= limit else f"{text[:limit]}… [truncated]"


def build_context(state):
    question = next(
        (
            message.content
            for message in reversed(state["messages"])
            if isinstance(message, HumanMessage)
        ),
        "",
    )

    plan = state.get("plan")

    if plan:
        if plan.current_step < len(plan.steps):
            current_step = plan.steps[plan.current_step]
            plan_text = (
                f"Goal: {plan.goal}\n"
                f"Current step ({plan.current_step + 1} of {len(plan.steps)}): "
                f"{current_step.description}\n"
                f"Action: {current_step.action}\n"
                f"Expected tool: {current_step.expected_tool or 'none'}\n"
                f"Required prior tools: {', '.join(current_step.requires) or 'none'}\n"
                f"Required inputs/metrics: {', '.join(current_step.inputs) or 'none'}\n"
                f"Expected output: {current_step.expected_output}\n\n"
                "Execute only this contract. Use prior tool results as the source "
                "of truth; never invent or manually reconstruct their data."
            )
        else:
            plan_text = f"Goal: {plan.goal}\nAll planned steps are complete."
    else:
        plan_text = "No plan created yet."

    schema = get_schema_text()

    sections = []

    # ---------------------------------------------------------
    # System Prompt
    # ---------------------------------------------------------

    sections.append(
        f"""
You are an expert SQLite Data Analyst.

Database Schema:

{schema}

Execution Plan:

{plan_text}

User Question:

{question}

Rules:
- Only use the table 'sales'
- Never invent table names
- Never invent columns
- Only generate SQLite SQL.
- Always present final results as a natural-language summary or markdown table, never raw JSON.
- Generate charts using 'generate_chart' if the user requests a chart.
- Use only one tool call at a time and wait for its result.
- For ordinary charts, query `label` and numeric `value`; use explicit metric
  aliases when the plan requires a multi-series chart.
"""
    )

    # ---------------------------------------------------------
    # Repair Context
    # ---------------------------------------------------------

    repair_attempts = state.get("repair_attempts", 0)

    if repair_attempts:

        sections.append(
            f"""
Repair Attempt: {repair_attempts}

Previous Failure:

{state.get("last_failure_reason", "Unknown")}

Repair Guidance:

{state.get("repair_context", "")}

Repair Rules:
- Do NOT repeat the previous failed tool call unchanged.
- Analyze the previous failure before acting.
- Correct the root cause.
- Reuse successful previous tool results whenever possible.
- Continue the existing execution plan instead of restarting.
"""
        )

    # ---------------------------------------------------------
    # Session Memory
    # ---------------------------------------------------------

    memory = state.get("memory", [])

    if memory:

        sections.append("Relevant Long-Term Memory:")

        for item in memory[:3]:
            # Durable records are the primary shape. The fallback keeps
            # context construction compatible with older in-session items.
            if hasattr(item, "metadata"):
                sections.append(
                    f"- [{item.kind.value}, importance={item.score.importance:.2f}, "
                    f"confidence={item.score.confidence:.2f}] {_compact(item.content, 350)}"
                )
            else:
                sections.append(
                    f"- [{item.category}, importance={item.importance:.2f}] "
                    f"{_compact(item.content, 350)} ({item.timestamp})"
                )

    knowledge = state.get("knowledge", [])
    if knowledge:
        sections.append("Relevant Knowledge (cite these sources in final responses):")
        sections.extend(
            f"- [{hit.citation}; confidence={hit.score:.2f}] {_compact(hit.chunk.text, 450)}"
            for hit in knowledge[:3]
        )

    # ---------------------------------------------------------
    # Execution History
    # ---------------------------------------------------------

    tool_results = state.get("tool_results", [])

    if tool_results:

        sections.append("Execution History:")

        for tool in tool_results:

            section = f"""
Tool   : {tool.tool}
Status : {tool.status}
"""

            if tool.result:
                section += f"\nResult:\n{_compact(pretty_json(tool.result), 1200)}\n"

            if tool.message:
                section += f"""

Error:
{tool.message}
"""

            sections.append(section)

    return "\n\n".join(sections)
