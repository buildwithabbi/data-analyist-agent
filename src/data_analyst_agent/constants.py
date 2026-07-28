"""Framework-wide constants available to every packaged entry point."""

MAX_REPAIR_ATTEMPTS = 3

DEFAULT_REPAIR_INSTRUCTION = (
    "Analyze the previous failure and generate a corrected execution."
)

UNKNOWN_ERROR_MESSAGE = "Unknown execution failure."

TRACE_REPAIR_STARTED = "Repair started"
TRACE_REPAIR_COMPLETED = "Repair completed"
TRACE_REPAIR_FAILED = "Repair failed"
TRACE_MAX_RETRIES_EXCEEDED = "Maximum repair attempts exceeded"
