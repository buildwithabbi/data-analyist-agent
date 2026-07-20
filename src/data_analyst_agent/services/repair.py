from data_analyst_agent.agent.state import AgentState
from data_analyst_agent.domain.enums import ErrorCategory, ExecutionStatus
from data_analyst_agent.domain.models import RepairDecision
from data_analyst_agent.domain.models import Plan
from constants import MAX_REPAIR_ATTEMPTS


class RepairService:

    def __init__(self, llm, context_builder):
        self.llm = llm
        self.context_builder = context_builder

    async def repair_plan(
        self,
        state: AgentState,
    ) -> Plan:
        """
        Analyze a failed execution and generate a corrected execution plan.
        """

        repair_context = self.context_builder.build_repair_context(state)

        structured_llm = self.llm.with_structured_output(Plan)

        corrected_plan = await structured_llm.ainvoke(repair_context)

        return corrected_plan


def analyze_execution(state: AgentState) -> RepairDecision:
    """Classify the latest tool result for the existing reflection workflow."""
    tool_results = state.get("tool_results", [])
    if not tool_results or tool_results[-1].status == "success":
        return RepairDecision(status=ExecutionStatus.SUCCESS)

    latest = tool_results[-1]
    retry_count = state.get("repair_attempts", 0)
    retry_allowed = retry_count < MAX_REPAIR_ATTEMPTS
    failure_reason = latest.message or "Unknown execution failure"

    return RepairDecision(
        status=(
            ExecutionStatus.RECOVERABLE_FAILURE
            if retry_allowed
            else ExecutionStatus.NON_RECOVERABLE_FAILURE
        ),
        requires_repair=retry_allowed,
        retry_allowed=retry_allowed,
        error_category=classify_error(failure_reason),
        failure_reason=failure_reason,
        failed_tool=latest.tool,
        retry_count=retry_count,
        repair_instruction=build_repair_instruction(failure_reason) if retry_allowed else "",
    )


def classify_error(message: str) -> ErrorCategory:
    """Map common tool failures to the standard error taxonomy."""
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
    """Create guidance for the compatibility repair workflow."""
    return f"Analyze the failed execution and correct this error: {message}"
