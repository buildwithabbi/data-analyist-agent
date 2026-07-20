from __future__ import annotations

from collections import defaultdict

from ..domain.models import MemoryItem


class MemoryConsolidator:
    """
    Consolidates related memories to reduce redundancy.

    Phase 5 performs simple rule-based consolidation.
    Future phases will use an LLM to generate semantic summaries.
    """

    def consolidate(
        self,
        memories: list[MemoryItem],
    ) -> list[MemoryItem]:
        """
        Merge duplicate memories by category and content.
        """

        grouped: dict[tuple[str, str], MemoryItem] = {}

        for memory in memories:
            key = (
                memory.category.lower(),
                memory.content.strip().lower(),
            )

            existing = grouped.get(key)

            if existing is None:
                grouped[key] = memory
                continue

            if memory.importance > existing.importance:
                grouped[key] = memory

        return list(grouped.values())