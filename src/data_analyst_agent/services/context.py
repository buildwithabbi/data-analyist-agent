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
You are a SQLite data analyst. Use only table `sales` and the schema below;
write SQLite SELECT queries only. Give final answers as prose or a Markdown
table, never raw JSON.

SQLite date rule: never use `EXTRACT`. Use `strftime('%Y', order_date)`,
`strftime('%m', order_date)`, or `strftime('%Y-%m', order_date)`.

Schema: {schema}
Tools: {tool_names}
Plan: {plan_text}
Question: {question}

For a requested chart: query `label` (text) and `value` (number), then call
`generate_chart` using exactly the returned values; include its path in the
answer. Complete one measure at a time and never invent chart data.
Call exactly one tool, wait for its result, then follow the current plan step.
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




def build_repair_context(state) -> str:
    """
    Build a dedicated context for repairing a failed execution plan.
    """

    plan = state.get("plan")

    if plan:
        plan_text = "\n".join(
            f"{idx + 1}. {step}"
            for idx, step in enumerate(plan.steps)
        )
    else:
        plan_text = "No execution plan available."

    tool_results = state.get("tool_results", [])

    latest_result = tool_results[-1] if tool_results else None

    latest_error = latest_result.message if latest_result else "Unknown"

    latest_tool = latest_result.tool if latest_result else "Unknown"

    schema = get_schema_text()

    tool_names = "\n".join(
        f"- {tool.name}"
        for tool in TOOLS
        if tool.name != "get_schema"
    )

    return f"""
You are repairing an execution plan.

Do NOT create a completely new strategy.

Only modify the part of the plan that caused the failure.

Original Plan

Goal:
{plan.goal if plan else "Unknown"}

Steps

{plan_text}

Failed Tool

{latest_tool}

Failure

{latest_error}

Retry Attempt

{state.get("repair_attempts",0)}

Available Tools

{tool_names}

Database Schema

{schema}

Instructions

1. Preserve successful work.
2. Do not restart the workflow.
3. Fix only the failed step.
4. Prefer minimal changes.
5. Return a corrected execution plan.
"""
