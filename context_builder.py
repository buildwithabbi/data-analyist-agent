from tools import TOOLS, get_schema_text


def build_context(state):

    question = state["messages"][0].content
    plan = state.get("plan", "")

    schema = get_schema_text()

    tool_names = "\n".join(
        f"- {tool.name}" for tool in TOOLS if tool.name != "get_schema"
    )

    return f"""
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
                - Only generate SQLite SQL
                - Always present final results as a natural-language summary or markdown table, never raw JSON.
                - generate charts using the 'generate_chart' if the user asks for a chart. The chart must be saved in the 'charts' directory and the path to the chart must be included in the final answer.
                
                IMPORTANT:
                Only call ONE tool at a time.
                Wait for the tool result before deciding the next action.
                Never call multiple dependent tools in one response.
                """
