import datetime
from typing import Optional
from uuid import uuid4
from pydantic.dataclasses import dataclass
from pydantic import BaseModel, Field
from enum import Enum

from .enums import ExecutionStatus, ErrorCategory

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
    Represents the outcome of execution analysis performed by the
    Reflection/RepairService.

    This model acts as the contract between Reflection and the LangGraph
    routing logic.
    """

    status: ExecutionStatus = Field(
        ...,
        description="Overall execution status."
    )

    requires_repair: bool = Field(
        default=False,
        description="Whether the execution should be repaired."
    )

    retry_allowed: bool = Field(
        default=False,
        description="Whether another repair attempt is permitted."
    )

    error_category: ErrorCategory = Field(
        default=ErrorCategory.UNKNOWN,
        description="Normalized category of the execution failure."
    )

    failure_reason: Optional[str] = Field(
        default=None,
        description="Human-readable explanation of the failure."
    )

    failed_tool: Optional[str] = Field(
        default=None,
        description="Name of the tool that failed."
    )

    retry_count: int = Field(
        default=0,
        ge=0,
        description="Current repair attempt count."
    )

    repair_instruction: str | None = Field(
        default=None,
        description="Guidance supplied to the repair workflow.",
    )

    class Config:
        frozen = True


class RepairRecord(BaseModel):

    attempt: int

    failure_reason: str

    previous_plan: Plan

    repaired_plan: Plan

    timestamp: datetime.datetime


class ExecutionRecord(BaseModel):

    step_number: int

    tool_name: str

    tool_input: dict

    tool_output: str

    success: bool

    started_at: datetime.datetime

    completed_at: datetime.datetime





class MemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    category: str
    importance: float
    timestamp: datetime.datetime
