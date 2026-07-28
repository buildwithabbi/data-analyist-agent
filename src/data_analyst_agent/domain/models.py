from pydantic.dataclasses import dataclass
from pydantic import BaseModel, Field
from enum import Enum
from .enums import ErrorCategory, ExecutionStatus, StepAction, StepStatus

@dataclass
class ToolResult:
    tool: str
    status: str
    result: dict | None = None
    message: str | None = None
    typed_result: "SQLResult | ChartResult | None" = None


class SQLResult(BaseModel):
    query: str = ""
    row_count: int = 0
    rows: list[dict] = Field(default_factory=list)


class ChartResult(BaseModel):
    chart_path: str
    chart_type: str
    title: str
    series_count: int = 1
    series: list[str] = Field(default_factory=list)


class Artifact(BaseModel):
    """A typed output that later steps may consume by identifier."""

    id: str
    type: str
    producer: str
    payload: dict = Field(default_factory=dict)


@dataclass
class ExecutionRecord:
    """Auditable outcome of a single planned execution step."""

    step_number: int
    step: str
    tool: str | None
    tool_input: dict | None
    output: dict | None
    success: bool
    duration_seconds: float | None = None


class PlanStep(BaseModel):
    """A deterministic contract for one unit of plan execution."""

    id: int = 0
    action: StepAction
    description: str
    expected_tool: str | None = None
    expected_output: str = ""
    requires: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    dependencies: list[int] = Field(default_factory=list)
    status: StepStatus = StepStatus.PENDING

    def model_post_init(self, __context) -> None:
        """Supply a safe contract when a planner omits multi-chart inputs."""
        if self.expected_output == "multi_series_line_chart" and not self.inputs:
            known_metrics = ("sales", "profit", "quantity", "discount")
            description = self.description.lower()
            self.inputs = [metric for metric in known_metrics if metric in description]


@dataclass
class Plan:
    goal: str
    # ``str`` remains accepted so existing callers can construct legacy plans;
    # it is normalized immediately into an executable PlanStep contract.
    steps: list[PlanStep | str]
    current_step: int = 0

    def __post_init__(self) -> None:
        self.steps = [_normalise_step(step) for step in self.steps]
        for index, step in enumerate(self.steps, start=1):
            if step.id == 0:
                step.id = index


def _normalise_step(step: PlanStep | str) -> PlanStep:
    if isinstance(step, PlanStep):
        return step

    description = str(step).strip()
    lowered = description.lower()
    if any(word in lowered for word in ("chart", "visual", "plot")):
        return PlanStep(
            action="GENERATE_CHART",
            description=description,
            expected_tool="generate_chart",
            expected_output="chart",
            requires=["run_sql"],
        )
    if any(word in lowered for word in ("summary", "summar", "insight", "report")):
        return PlanStep(
            action="SUMMARIZE",
            description=description,
            expected_output="natural-language summary grounded in prior results",
        )
    return PlanStep(
        action="QUERY",
        description=description,
        expected_tool="run_sql",
            expected_output="structured SQL result",
    )


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
