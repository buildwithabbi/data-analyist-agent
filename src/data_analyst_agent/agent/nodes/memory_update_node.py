"""Memory-persistence workflow node."""

from datetime import datetime, timezone

from ...domain.models import MemoryItem
from .memory_node import memory_manager
from ..state import AgentState


def memory_update_node(state: AgentState) -> dict:
    print("➡️ Memory Update")
    tool_results = state.get("tool_results", [])

    if not tool_results:
        return {}

    latest = tool_results[-1]
    if latest.status != "success":
        return {}

    if latest.tool == "run_sql":
        row_count = latest.result.get("row_count", 0)
        memory_manager.remember(
            MemoryItem(
                content=f"Executed SQL successfully and returned {row_count} rows.",
                importance=0.80,
                category="tool",
                timestamp=datetime.now(timezone.utc),
            )
        )
    elif latest.tool == "generate_chart":
        title = latest.result.get("title", "Chart")
        memory_manager.remember(
            MemoryItem(
                content=f"Generated chart '{title}'.",
                importance=0.92,
                category="tool",
                timestamp=datetime.now(timezone.utc),
            )
        )

    return {}
