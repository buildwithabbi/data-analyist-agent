from langchain_core.messages import AIMessage


def route_tools(state):
    print("➡️ Router")

    last_message = state["messages"][-1]

    print(type(last_message))

    if isinstance(last_message, AIMessage):
        print("Tool calls:", last_message.tool_calls)

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tool"

    return "end"
