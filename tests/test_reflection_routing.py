from data_analyst_agent.agent.reflection_routing import route_reflection
from data_analyst_agent.domain.enums import ExecutionStatus
from data_analyst_agent.domain.models import Plan, RepairDecision


def test_route_success():

    state = {
        "repair_decision": RepairDecision(
            status=ExecutionStatus.SUCCESS
        )
    }

    assert route_reflection(state) == "memory_update"


def test_route_repair():

    state = {
        "repair_decision": RepairDecision(
            status=ExecutionStatus.RECOVERABLE_FAILURE
        )
    }

    assert route_reflection(state) == "repair"


def test_route_continues_when_plan_has_more_steps():
    state = {
        "plan": Plan(goal="Analyze sales", steps=["Run SQL", "Summarize"]),
        "repair_decision": RepairDecision(status=ExecutionStatus.SUCCESS),
    }

    assert route_reflection(state) == "continue_execution"


def test_route_end():

    state = {
        "repair_decision": RepairDecision(
            status=ExecutionStatus.NON_RECOVERABLE_FAILURE
        )
    }

    assert route_reflection(state) == "end"

def test_route_none_decision():

    state = {}

    assert route_reflection(state) == "end"
