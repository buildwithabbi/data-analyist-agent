from typing import List

# In-memory storage for the current session
_MEMORY: List[str] = []


def add_memory(memory: str) -> None:
    """
    Add a new memory to the current session.
    """
    memory = memory.strip()

    if memory:
        _MEMORY.append(memory)


def get_memory() -> List[str]:
    """
    Return all memories for the current session.
    """
    return list(_MEMORY)


def clear_memory() -> None:
    """
    Remove all memories from the current session.
    """
    _MEMORY.clear()


def last_memory() -> str | None:
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


def add_unique_memory(memory: str) -> None:
    """
    Add a memory only if it does not already exist.
    """
    memory = memory.strip()

    if memory and memory not in _MEMORY:
        _MEMORY.append(memory)