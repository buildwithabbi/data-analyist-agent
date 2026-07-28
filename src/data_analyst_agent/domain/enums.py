from enum import Enum


class StepAction(str, Enum):
    QUERY = "QUERY"
    GENERATE_CHART = "GENERATE_CHART"
    SUMMARIZE = "SUMMARIZE"
    ANALYZE = "ANALYZE"
    EXPORT = "EXPORT"


class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ExecutionStatus(str, Enum):
    """
    Final execution status produced by the Reflection node.
    """

    SUCCESS = "SUCCESS"
    RECOVERABLE_FAILURE = "RECOVERABLE_FAILURE"
    NON_RECOVERABLE_FAILURE = "NON_RECOVERABLE_FAILURE"
    REPAIRING = "REPAIRING"


class ErrorCategory(str, Enum):
    """
    Standardized error taxonomy for execution failures.
    """

    TOOL_ERROR = "TOOL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PARSING_ERROR = "PARSING_ERROR"
    LLM_ERROR = "LLM_ERROR"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"
