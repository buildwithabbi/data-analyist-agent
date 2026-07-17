import pytest

from data_analyst_agent.services.repair import analyze_execution
from data_analyst_agent.domain.enums import (
    ExecutionStatus,
    ErrorCategory,
)
from data_analyst_agent.domain.models import ToolResult
from data_analyst_agent.services.repair import (
    analyze_execution,
    classify_error,
)




def test_success_execution():

    state = {
        "tool_results": [
            ToolResult(
                tool="run_sql",
                status="success",
                result={"rows": []},
                message=None,
            )
        ],
        "repair_attempts": 0,
    }

    decision = analyze_execution(state)

    assert decision.status == ExecutionStatus.SUCCESS
    assert decision.requires_repair is False


def test_recoverable_failure():

    state = {
        "tool_results": [
            ToolResult(
                tool="run_sql",
                status="error",
                result=None,
                message="no such column: revenue",
            )
        ],
        "repair_attempts": 0,
    }

    decision = analyze_execution(state)

    assert decision.status == ExecutionStatus.RECOVERABLE_FAILURE
    assert decision.requires_repair
    assert decision.retry_allowed
    assert decision.error_category == ErrorCategory.TOOL_ERROR


def test_max_retry_reached():

    state = {
        "tool_results": [
            ToolResult(
                tool="run_sql",
                status="error",
                result=None,
                message="SQL Error",
            )
        ],
        "repair_attempts": 3,
    }

    decision = analyze_execution(state)

    assert decision.status == ExecutionStatus.NON_RECOVERABLE_FAILURE
    assert decision.retry_allowed is False





def test_empty_tool_results_returns_success():
    state = {
        "tool_results": [],
        "repair_attempts": 0,
    }

    decision = analyze_execution(state)

    assert decision.status == ExecutionStatus.SUCCESS
    assert decision.requires_repair is False
    assert decision.retry_allowed is False


@pytest.mark.parametrize(
    "message,expected",
    [
        ("SQLite syntax error", ErrorCategory.DATABASE_ERROR),
        ("Database connection failed", ErrorCategory.DATABASE_ERROR),
        ("Validation failed", ErrorCategory.VALIDATION_ERROR),
        ("Parse error near FROM", ErrorCategory.PARSING_ERROR),
        ("Request timeout", ErrorCategory.TIMEOUT),
        ("LLM response malformed", ErrorCategory.LLM_ERROR),
        ("Some unknown failure", ErrorCategory.TOOL_ERROR),
    ],
)
def test_classify_error(message, expected):
    assert classify_error(message) == expected