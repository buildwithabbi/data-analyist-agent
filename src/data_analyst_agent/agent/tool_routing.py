from langchain_core.messages import AIMessage
from ..utils.console import print_json


def route_tools(state):
    # The executor detected an invalid/missing call for the current step.
    # Send it to reflection so repair can handle it; do not execute the call.
    if state.get("step_validation_error"):
        return "end"

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
