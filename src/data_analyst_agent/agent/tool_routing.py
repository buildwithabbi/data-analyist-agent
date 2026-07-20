from langchain_core.messages import AIMessage
from ..utils.console import print_json


def route_tools(state):
    last_message = state["messages"][-1]

    if isinstance(last_message, AIMessage):
        print_json(
            "ROUTER",
            {
                "message_type": type(last_message).__name__,
                "tool_calls": last_message.tool_calls,
            },
        )

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tool"

    # The model has produced its final natural-language answer.  Persist any
    # successful work from the run before ending the graph.
    return "final"
