from ..domain.models import MemoryItem

# In-memory storage for the current session
_MEMORY: list[MemoryItem] = []


def add_memory(memory: MemoryItem) -> None:
    """
    Add a new memory to the current session.
    """
    content = memory.content.strip()
    if content:
        _MEMORY.append(
            MemoryItem(
                content=content,
                importance=memory.importance,
                category=memory.category,
                timestamp=memory.timestamp,
            )
        )


def get_memory() -> list[MemoryItem]:
    """
    Return all memories for the current session.
    """
    return list(_MEMORY)


def clear_memory() -> None:
    """
    Remove all memories from the current session.
    """
    _MEMORY.clear()


def last_memory() -> MemoryItem | None:
    """
    Return the most recent memory.
    """
    if not _MEMORY:
        return None

    return _MEMORY[-1]


def memory_count() -> int:
    """
    Return the number of stored memories.
    """
    return len(_MEMORY)


def add_unique_memory(memory: MemoryItem) -> None:
    """
    Add a memory only if it does not already exist.
    """
    content = memory.content.strip()
    if content and not any(
        item.category == memory.category and item.content == content
        for item in _MEMORY
    ):
        add_memory(memory)
