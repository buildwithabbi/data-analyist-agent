from __future__ import annotations

from ..domain.models import MemoryItem


class MemoryClassifier:
    """
    Determines whether a memory should be stored and
    where it should be stored.

    Phase 4 uses rule-based classification.
    Future phases will use an LLM.
    """

    LONG_TERM_IMPORTANCE = 0.8

    def should_store(self, memory: MemoryItem) -> bool:
        """
        Decide whether the memory should be stored.
        """

        return bool(memory.content.strip())

    def is_long_term(self, memory: MemoryItem) -> bool:
        """
        Determine whether the memory belongs in LTM.
        """

        return memory.importance >= self.LONG_TERM_IMPORTANCE