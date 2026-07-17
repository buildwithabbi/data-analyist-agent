from data_analyst_agent.domain.enums import ExecutionStatus


def route_reflection(state):
    """
    Route execution based on the RepairDecision
    produced by the Reflection node.
    """

    decision = state.get("repair_decision")

    if decision is None:
        return "end"

    if decision.status == ExecutionStatus.SUCCESS:
        return "memory_update"

    if decision.status == ExecutionStatus.RECOVERABLE_FAILURE:
        return "repair"

    if decision.status == ExecutionStatus.NON_RECOVERABLE_FAILURE:
        return "end"

    return "end"