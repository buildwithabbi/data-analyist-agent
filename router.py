def route_tools(state):

    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tool"

    return "end"