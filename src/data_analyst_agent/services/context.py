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
        plan_text = "\n".join(
            f"{index + 1}. {step}"
            for index, step in enumerate(plan.steps)
        )

        plan_text = (
            f"Goal: {plan.goal}\n"
            f"Current step: {plan.current_step}\n"
            f"Steps:\n{plan_text}"
        )
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

        sections.append("Session Memory:")

        for item in memory:
            sections.append(
                f"- [{item.category}, importance={item.importance:.2f}] "
                f"{item.content} ({item.timestamp})"
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