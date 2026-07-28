"""Memory-persistence workflow node."""

from ...memory.manager import memory_manager
from ..state import AgentState


def memory_update_node(state: AgentState) -> dict:
    print("➡️ Memory Update")
    memory = memory_manager.write(state)
    trace = list(state.get("trace", []))
    trace.append("🧠 Stored durable episode memory" if memory else "🧠 Execution not retained as durable memory")
    return {"trace": trace}
