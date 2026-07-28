"""Memory-loading workflow node."""

from langchain_core.messages import HumanMessage

from ...memory.manager import memory_manager
from ...knowledge.manager import knowledge_manager
from ..state import AgentState


def memory_node(state: AgentState) -> dict:
    print("➡️ Memory")
    query = next(
        (message.content for message in reversed(state.get("messages", [])) if isinstance(message, HumanMessage)),
        "",
    )
    memory = memory_manager.retrieve(query, limit=5) if query else []
    knowledge = knowledge_manager.retrieve(query, limit=5) if query else []
    trace = [*state.get("trace", []), f"🧠 Retrieved {len(memory)} relevant durable memories", f"📚 Retrieved {len(knowledge)} knowledge chunks"]
    return {"memory": memory, "knowledge": knowledge, "trace": trace}
