from __future__ import annotations
from .memory_classifier import MemoryClassifier
from ..domain.models import MemoryItem
from ..memory.long_term import LongTermMemory
from ..memory.short_term import ShortTermMemory
from .memory_retriever import MemoryRetriever
from .memory_consolidator import MemoryConsolidator

class MemoryManager:
    """
    Coordinates all memory operations for the agent.

    The manager acts as the single entry point for the graph,
    delegating work to Short-Term Memory (STM),
    Long-Term Memory (LTM), and the MemoryRetriever.

    Graph nodes should never interact directly with STM or LTM.
    """

    def __init__(
        self,
        stm: ShortTermMemory | None = None,
        ltm: LongTermMemory | None = None,
    ) -> None:
        self._stm = stm or ShortTermMemory()
        self._ltm = ltm or LongTermMemory()
        self._classifier = MemoryClassifier()
        self._consolidator = MemoryConsolidator()
        self._retriever = MemoryRetriever(
            self._stm,
            self._ltm,
        )

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(
        self,
        *,
        max_long_term: int = 10,
    ) -> list[MemoryItem]:

        memories = self._retriever.retrieve(
            max_long_term=max_long_term,
        )

        return self._consolidator.consolidate(memories)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def remember(
        self,
        memory: MemoryItem,
        *,
        unique: bool = False,
    ) -> None:

        if not self._classifier.should_store(memory):
            return

        store = (
            self._ltm
            if self._classifier.is_long_term(memory)
            else self._stm
        )

        if unique:
            store.add_unique(memory)
        else:
            store.add(memory)
    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        memory: MemoryItem,
        *,
        long_term: bool = False,
    ) -> None:
        """
        Update an existing memory.
        """

        store = self._ltm if long_term else self._stm
        store.update(memory)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def forget(
        self,
        memory_id: str,
        *,
        long_term: bool = False,
    ) -> None:
        """
        Remove a memory.
        """

        store = self._ltm if long_term else self._stm
        store.remove(memory_id)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """
        Remove all memories.
        """

        self._stm.clear()
        self._ltm.clear()

    def score(self, memory: MemoryItem) -> float:
        """
        Return the memory score.

        Phase 3 returns the importance value.
        Future phases will calculate dynamic scores
        using importance, recency, and relevance.
        """

        return memory.importance