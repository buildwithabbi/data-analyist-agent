"""Workflow node that prepares a retry after a recoverable failure."""

from ..state import AgentState


def repair_node(state: AgentState) -> dict:
    """Record the failed execution and expose repair guidance to the executor."""
    decision = state.get("repair_decision")
    if decision is None:
        return {}

    attempt = state.get("repair_attempts", 0) + 1
    failure_reason = decision.failure_reason
    repair_context = decision.repair_instruction

    return {
        "repair_attempts": attempt,
        "repair_history": [*state.get("repair_history", []), failure_reason],
        "last_failure_reason": failure_reason,
        "repair_context": repair_context,
        "trace": [*state.get("trace", []), f"Repair attempt {attempt}"],
    }
