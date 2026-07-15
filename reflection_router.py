MAX_RETRIES = 3


def route_reflection(state):

    if not state.get("tool_results"):
        return "executor"

    latest = state["tool_results"][-1]

    if latest.status == "success":
        return "memory_update"

    if state.get("retry_count", 0) >= MAX_RETRIES:
        return "end"

    return "executor"
