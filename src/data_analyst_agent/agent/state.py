from typing import Annotated
from typing_extensions import NotRequired, TypedDict
from langgraph.graph.message import add_messages

from ..domain.models import (
    Artifact,
    ExecutionRecord,
    MemoryItem,
    Plan,
    RepairDecision,
    ToolResult,
)



class AgentState(TypedDict):
    """
    Shared state passed between all LangGraph nodes.
    """

    # Conversation
    messages: Annotated[list, add_messages]

    # Planner
    plan: NotRequired[Plan]

    # Memory
    memory: NotRequired[list[MemoryItem]]

    # Stable content fingerprint of the database used by this run.
    dataset_id: NotRequired[str]

    # Retrieved, citable external knowledge for the current run.
    knowledge: NotRequired[list]

    # Tool execution
    tool_results: NotRequired[list[ToolResult]]

    # Completed plan steps, including their tool inputs and outputs.
    execution_records: NotRequired[list[ExecutionRecord]]

    artifacts: NotRequired[list[Artifact]]

    # A deterministic validation failure awaiting reflection/repair.
    step_validation_error: NotRequired[str]

    validation_complete: NotRequired[bool]

    evaluation_error: NotRequired[str]

    # Execution trace
    trace: NotRequired[list[str]]

    # -----------------------------
    # Repair Loop State
    # -----------------------------

    repair_decision: NotRequired[RepairDecision]

    repair_attempts: NotRequired[int]

    repair_history: NotRequired[list[str]]

    last_failed_tool: NotRequired[str]

    last_failure_reason: NotRequired[str]

    repair_context: NotRequired[str]
