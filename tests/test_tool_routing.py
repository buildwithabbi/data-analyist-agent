from langchain_core.messages import AIMessage

from data_analyst_agent.agent.tool_routing import route_tools


def test_route_tools_continues_to_tool_node_when_model_calls_a_tool():
    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "run_sql", "args": {"query": "SELECT 1"}, "id": "1"}
                ],
            )
        ]
    }

    assert route_tools(state) == "tool"


def test_route_tools_marks_final_model_response_for_persistence():
    state = {"messages": [AIMessage(content="Analysis complete.")]}

    assert route_tools(state) == "final"
