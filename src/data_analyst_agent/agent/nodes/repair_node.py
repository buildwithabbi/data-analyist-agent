from data_analyst_agent.agent.state import AgentState
from data_analyst_agent.services.repair import RepairService


class RepairNode:

    def __init__(self, repair_service: RepairService):
        self._repair_service = repair_service

    async def __call__(self, state: AgentState):

        corrected_plan = await self._repair_service.repair_plan(state)

        return {
            "plan": corrected_plan,
            "repair_attempts": state["repair_attempts"] + 1,
            "repair_history": [
                *state.get("repair_history", []),
                corrected_plan,
            ],
        }


def repair_node(state: AgentState) -> dict:
    """Compatibility callable used by the existing LangGraph definition."""
    decision = state.get("repair_decision")
    if decision is None:
        return {}

    attempt = state.get("repair_attempts", 0) + 1
    failure_reason = decision.failure_reason or "Unknown execution failure"
    return {
        "repair_attempts": attempt,
        "repair_history": [*state.get("repair_history", []), failure_reason],
        "last_failed_tool": decision.failed_tool,
        "last_failure_reason": failure_reason,
        "repair_context": decision.repair_instruction,
        "trace": [*state.get("trace", []), f"Repair attempt {attempt}"],
    }
