from data_analyst_agent.agent.nodes.repair_node import repair_node
from data_analyst_agent.domain.enums import ExecutionStatus
from data_analyst_agent.domain.models import RepairDecision


def test_repair_node_updates_state():

    state = {
        "repair_attempts": 0,
        "repair_history": [],
        "trace": [],
        "repair_decision": RepairDecision(
            status=ExecutionStatus.RECOVERABLE_FAILURE,
            failure_reason="SQL Error",
            repair_instruction="Fix SQL",
        ),
    }

    updated = repair_node(state)

    assert updated["repair_attempts"] == 1

    assert updated["last_failure_reason"] == "SQL Error"

    assert updated["repair_context"] == "Fix SQL"

    assert len(updated["repair_history"]) == 1

def test_repair_node_appends_history():

    state = {
        "repair_attempts": 2,
        "repair_history": [
            "Failure One",
            "Failure Two",
        ],
        "trace": [
            "Executor",
        ],
        "repair_decision": RepairDecision(
            status=ExecutionStatus.RECOVERABLE_FAILURE,
            failure_reason="Failure Three",
            repair_instruction="Fix SQL",
        ),
    }

    result = repair_node(state)

    assert result["repair_attempts"] == 3

    assert result["repair_history"] == [
        "Failure One",
        "Failure Two",
        "Failure Three",
    ]

    assert result["trace"][-1] == "Repair attempt 3"