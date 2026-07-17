from data_analyst_agent.agent.nodes.reflection_node import reflection_node
from data_analyst_agent.domain.models import ToolResult
from data_analyst_agent.domain.enums import ExecutionStatus


def test_reflection_node_success():

    state = {
        "tool_results": [
            ToolResult(
                tool="sql",
                status="success",
                result={},
                message=None,
            )
        ],
        "repair_attempts": 0,
    }

    result = reflection_node(state)

    assert "repair_decision" in result

    assert (
        result["repair_decision"].status
        == ExecutionStatus.SUCCESS
    )


def test_reflection_node_failure():

    state = {
        "tool_results": [
            ToolResult(
                tool="sql",
                status="error",
                result=None,
                message="SQL Error",
            )
        ],
        "repair_attempts": 0,
    }

    result = reflection_node(state)

    assert (
        result["repair_decision"].status
        == ExecutionStatus.RECOVERABLE_FAILURE
    )