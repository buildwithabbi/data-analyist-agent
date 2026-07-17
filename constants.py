"""
Framework-wide constants.

These values are intentionally centralized so that retry
behaviour remains consistent across Reflection, Repair,
Executor and Graph routing.
"""

# Maximum repair attempts allowed for a single execution.

MAX_REPAIR_ATTEMPTS = 3

# Default message used when no repair guidance is available.

DEFAULT_REPAIR_INSTRUCTION = (
    "Analyze the previous failure and generate a corrected execution."
)

# Fallback error category.

UNKNOWN_ERROR_MESSAGE = "Unknown execution failure."

# Trace messages.

TRACE_REPAIR_STARTED = "Repair started"

TRACE_REPAIR_COMPLETED = "Repair completed"

TRACE_REPAIR_FAILED = "Repair failed"

TRACE_MAX_RETRIES_EXCEEDED = "Maximum repair attempts exceeded"