"""Memory-loading workflow node."""

from ...services.memory_manager import MemoryManager
from ..state import AgentState

memory_manager = MemoryManager()


def memory_node(state: AgentState) -> dict:
    """
    Load relevant memories into the current workflow state.
    """

    print("➡️ Memory")

    memory = memory_manager.retrieve()

    trace = [
        *state.get("trace", []),
        f"🧠 Loaded {len(memory)} memory item(s)",
    ]

    return {
        "memory": memory,
        "trace": trace,
    }