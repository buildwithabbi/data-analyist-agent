"""
Repair Service

Owns execution analysis and determines whether a failed
execution should enter the Repair Loop.

This module contains business logic only.

No LangGraph dependencies.
"""

from data_analyst_agent.agent.state import AgentState
from data_analyst_agent.domain.enums import (
    ErrorCategory,
    ExecutionStatus,
)
from data_analyst_agent.domain.models import RepairDecision
from constants import MAX_REPAIR_ATTEMPTS


def analyze_execution(state: AgentState) -> RepairDecision:
    """
    Analyze the latest execution and determine
    whether repair is required.
    """

    tool_results = state.get("tool_results", [])

    if not tool_results:
        return RepairDecision(
            status=ExecutionStatus.SUCCESS,
            requires_repair=False,
            retry_allowed=False,
        )

    latest = tool_results[-1]

    if latest.status == "success":
        return RepairDecision(
            status=ExecutionStatus.SUCCESS,
            requires_repair=False,
            retry_allowed=False,
        )

    retry_count = state.get("repair_attempts", 0)

    retry_allowed = retry_count < MAX_REPAIR_ATTEMPTS

    if retry_allowed:
        return RepairDecision(
            status=ExecutionStatus.RECOVERABLE_FAILURE,
            error_category=classify_error(latest.message),
            requires_repair=True,
            retry_allowed=True,
            failure_reason=latest.message,
            repair_instruction=build_repair_instruction(latest.message),
        )

    return RepairDecision(
        status=ExecutionStatus.NON_RECOVERABLE_FAILURE,
        error_category=classify_error(latest.message),
        requires_repair=False,
        retry_allowed=False,
        failure_reason=latest.message,
    )


def classify_error(message: str) -> ErrorCategory:
    """
    Classify execution failure into a standard category.
    """

    error = message.lower()

    if "sqlite" in error or "database" in error:
        return ErrorCategory.DATABASE_ERROR

    if "validation" in error:
        return ErrorCategory.VALIDATION_ERROR

    if "parse" in error:
        return ErrorCategory.PARSING_ERROR

    if "timeout" in error:
        return ErrorCategory.TIMEOUT

    if "llm" in error:
        return ErrorCategory.LLM_ERROR

    return ErrorCategory.TOOL_ERROR


def build_repair_instruction(message: str) -> str:
    """
    Generate guidance for the Repair Node.
    """

    return (
        "Analyze the previous execution failure, "
        "identify the root cause, "
        "correct the execution plan, "
        f"and resolve this error: {message}"
    )