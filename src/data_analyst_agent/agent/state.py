from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from ..domain.models import MemoryItem, Plan, ToolResult, RepairDecision
from typing import Annotated
from typing_extensions import NotRequired, TypedDict
from langgraph.graph.message import add_messages



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

    # Tool execution
    tool_results: NotRequired[list[ToolResult]]

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