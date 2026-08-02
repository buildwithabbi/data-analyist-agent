from langchain_core.messages import AIMessage

from data_analyst_agent.agent.tool_routing import route_tools


def test_final_answer_routes_to_validator_path():
    assert route_tools({"messages": [AIMessage(content="Final answer")]}) == "end"
