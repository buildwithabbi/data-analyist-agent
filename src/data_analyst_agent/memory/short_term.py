from __future__ import annotations

from ..domain.models import MemoryItem


class ShortTermMemory:
    """
    In-memory storage for the current agent session.

    This class encapsulates all Short-Term Memory (STM) operations.
    It intentionally has no knowledge of Long-Term Memory,
    retrieval strategies, or persistence.
    """

    def __init__(self) -> None:
        self._memory: list[MemoryItem] = []

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def add(self, memory: MemoryItem) -> None:
        """
        Store a memory.
        """

        if not memory.content.strip():
            return

        # Preserve the original MemoryItem (including its id).
        self._memory.append(memory.model_copy(deep=True))

    def add_unique(self, memory: MemoryItem) -> None:
        """
        Store a memory only if an equivalent memory
        does not already exist.
        """

        if not memory.content.strip():
            return

        exists = any(
            item.category == memory.category
            and item.content == memory.content
            for item in self._memory
        )

        if not exists:
            self.add(memory)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_all(self) -> list[MemoryItem]:
        """
        Return all session memories.
        """

        return self._memory.copy()

    def get_last(self) -> MemoryItem | None:
        """
        Return the most recently stored memory.
        """

        return self._memory[-1] if self._memory else None

    def count(self) -> int:
        """
        Return the number of stored memories.
        """

        return len(self._memory)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, memory: MemoryItem) -> None:
        """
        Update an existing memory.

        If the memory does not exist,
        it is added to the session.
        """

        for index, existing in enumerate(self._memory):
            if existing.id == memory.id:
                self._memory[index] = memory.model_copy(deep=True)
                return

        self.add(memory)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def remove(self, memory_id: str) -> None:
        """
        Remove a memory by its identifier.
        """

        self._memory = [
            memory
            for memory in self._memory
            if memory.id != memory_id
        ]

    def clear(self) -> None:
        """
        Remove all session memories.
        """

        self._memory.clear()