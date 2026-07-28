from langchain_core.messages import HumanMessage

from ..tools import TOOLS, get_schema_text
from ..utils.console import pretty_json


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

    tool_names = "\n".join(
        f"- {tool.name}"
        for tool in TOOLS
        if tool.name != "get_schema"
    )

    sections = []

    # ---------------------------------------------------------
    # System Prompt
    # ---------------------------------------------------------

    sections.append(
        f"""
You are an expert SQLite Data Analyst.

Database Schema:

{schema}

Available Tools:

{tool_names}

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
- The chart must be saved in the 'charts' directory and the path included in the final answer.
- To prepare a chart, first query a compact dataset with exactly two aliases:
  `label` (text) and `value` (numeric). For example, use
  `strftime('%Y-%m', order_date) AS label, SUM(sales) AS value`.
- Call `generate_chart` only after that SQL result is available. Its `data`
  argument must be an array of {{"label": "...", "value": number}} objects.

Tool Usage Rules:
1. Call ONLY ONE tool at a time.
2. Wait for the tool result before deciding the next tool.
3. Never call multiple dependent tools in one response.
4. Think → Tool → Observe → Think Again.
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

        for item in memory:
            # Durable records are the primary shape. The fallback keeps
            # context construction compatible with older in-session items.
            if hasattr(item, "metadata"):
                sections.append(
                    f"- [{item.kind.value}, importance={item.score.importance:.2f}, "
                    f"confidence={item.score.confidence:.2f}] {item.content}"
                )
            else:
                sections.append(
                    f"- [{item.category}, importance={item.importance:.2f}] "
                    f"{item.content} ({item.timestamp})"
                )

    knowledge = state.get("knowledge", [])
    if knowledge:
        sections.append("Relevant Knowledge (cite these sources in final responses):")
        sections.extend(f"- [{hit.citation}; confidence={hit.score:.2f}] {hit.chunk.text}" for hit in knowledge)

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
                section += f"""

Result:
{pretty_json(tool.result)}
"""

            if tool.message:
                section += f"""

Error:
{tool.message}
"""

            sections.append(section)

    return "\n\n".join(sections)
