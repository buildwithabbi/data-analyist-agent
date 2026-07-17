from pydantic.dataclasses import dataclass
from pydantic import BaseModel, Field
from enum import Enum
from .enums import ErrorCategory, ExecutionStatus

@dataclass
class ToolResult:
    tool: str
    status: str
    result: dict | None = None
    message: str | None = None


@dataclass
class Plan:
    goal: str
    steps: list[str]
    current_step: int = 0


@dataclass(kw_only=True)
class MemoryItem:
    content: str
    importance: float = Field(ge=0.0, le=1.0)
    category: str
    timestamp: str




class RepairDecision(BaseModel):
    """
    Structured output produced by the Reflection node.

    Reflection is responsible for deciding whether the
    execution should continue, terminate, or enter the
    Repair Loop.

    This model serves as the contract between Reflection
    and the Repair node.
    """

    status: ExecutionStatus = Field(
        description="Overall execution status."
    )

    error_category: ErrorCategory = Field(
        default=ErrorCategory.UNKNOWN,
        description="Classification of the detected failure."
    )

    requires_repair: bool = Field(
        default=False,
        description="Whether execution should be routed to the Repair node."
    )

    retry_allowed: bool = Field(
        default=False,
        description="Whether another repair attempt is permitted."
    )

    failure_reason: str = Field(
        default="",
        description="Human-readable explanation of the failure."
    )

    repair_instruction: str = Field(
        default="",
        description="Guidance for the Repair node to generate a corrected execution."
    )
