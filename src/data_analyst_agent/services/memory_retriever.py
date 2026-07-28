from __future__ import annotations
from .memory_ranker import MemoryRanker
from ..domain.models import MemoryItem
from ..memory.long_term import LongTermMemory
from ..memory.short_term import ShortTermMemory


class MemoryRetriever:
    """
    Retrieves memories for the current agent context.

    Phase 3:
        - Return all STM memories.
        - Return the most recent LTM memories.
        - Future phases will support semantic search,
          hybrid search, and ranking.
    """

    def __init__(
        self,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
    ) -> None:
        self._stm = stm
        self._ltm = ltm
        self._ranker = MemoryRanker()

    def retrieve(
        self,
        *,
        max_long_term: int = 10,
    ) -> list[MemoryItem]:
        """
        Retrieve memories for the current execution.
        """

        short_term = self._stm.get_all()
        long_term = self._ltm.get_all()

        if len(long_term) > max_long_term:
            long_term = long_term[-max_long_term:]

        memories = [
            *long_term,
            *short_term,
            ]

        return self._ranker.rank(
            memories,
            limit=max_long_term + len(short_term),
)