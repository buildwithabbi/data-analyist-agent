from tools import TOOLS, get_schema_text
from console_output import pretty_json

def build_context(state):

    question = state["messages"][0].content
    plan = state.get("plan", "")

    schema = get_schema_text()

    tool_names = "\n".join(
        f"- {tool.name}" for tool in TOOLS if tool.name != "get_schema"
    )

    sections = []

    # ---------------------------------------------------------
    # System Prompt
    # ---------------------------------------------------------

    sections.append(f"""
You are an expert SQLite Data Analyst.

Database Schema:

{schema}

Available Tools:

{tool_names}

Execution Plan:

{plan}

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

Tool Usage Rules:
1. Call ONLY ONE tool at a time.
2. Wait for the tool result before deciding the next tool.
3. Never call multiple dependent tools in one response.
4. Think → Tool → Observe → Think Again.
""")

    # ---------------------------------------------------------
    # Session Memory
    # ---------------------------------------------------------

    memory = state.get("memory", [])

    if memory:

        sections.append("Session Memory:")

        for item in memory:
            sections.append(f"- {item}")

    # ---------------------------------------------------------
    # Previous Tool Results
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