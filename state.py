from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from models import ToolResult


class AgentState(TypedDict):
    # Conversation
    messages: Annotated[list, add_messages]

    # Planner
    plan: str

    # Logger
    trace: list[str]

    # Executor
    current_task: str

    completed_tasks: list[str]

    # Tool outputs
    tool_results: list[ToolResult]

    # Reflection
    last_error: str | None

    retry_count: int

    memory: list[str]
