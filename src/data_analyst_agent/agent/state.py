from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import NotRequired, TypedDict

from ..domain.models import (
    MemoryItem,
    Plan,
    RepairDecision,
    RepairRecord,
    ToolResult,
)


class AgentState(TypedDict):
    """
    Shared state passed between all LangGraph nodes.
    """

    # ------------------------------------------------------------------
    # Conversation
    # ------------------------------------------------------------------

    messages: Annotated[list[BaseMessage], add_messages]

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------

    plan: NotRequired[Plan]

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    memory: NotRequired[list[MemoryItem]]

    # ------------------------------------------------------------------
    # Tool Execution
    # ------------------------------------------------------------------

    tool_results: NotRequired[list[ToolResult]]

    # ------------------------------------------------------------------
    # Execution Trace
    # ------------------------------------------------------------------

    trace: NotRequired[list[str]]

    # ------------------------------------------------------------------
    # Repair Loop
    # ------------------------------------------------------------------

    repair_decision: NotRequired[RepairDecision]

    repair_attempts: NotRequired[int]

    repair_history: NotRequired[list[RepairRecord]]

    last_failed_tool: NotRequired[str]

    last_failure_reason: NotRequired[str]

    repair_context: NotRequired[str]