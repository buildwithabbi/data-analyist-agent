from data_analyst_agent.agent.reflection_routing import route_reflection
from data_analyst_agent.agent.nodes.repair_node import repair_node
from data_analyst_agent.domain.enums import ExecutionStatus
from data_analyst_agent.domain.models import RepairDecision


def test_complete_repair_flow():

    state = {
        "repair_attempts": 0,
        "repair_history": [],
        "trace": [],
        "repair_decision": RepairDecision(
            status=ExecutionStatus.RECOVERABLE_FAILURE,
            failure_reason="Missing column",
            repair_instruction="Correct SQL",
        ),
    }

    assert route_reflection(state) == "repair"

    repaired_state = repair_node(state)

    assert repaired_state["repair_attempts"] == 1
    assert repaired_state["repair_context"] == "Correct SQL"
