from __future__ import annotations

from datetime import datetime

from ..domain.models import MemoryItem


class MemoryRanker:
    """
    Ranks memories before they are sent to the LLM.

    Phase 3:
        Score = Importance + Recency

    Future phases will incorporate:
        - Semantic similarity
        - Keyword overlap
        - Conversation context
        - User preferences
    """

    def score(self, memory: MemoryItem) -> float:
        """
        Compute a ranking score for a memory.
        """

        now = datetime.now(tz=memory.timestamp.tzinfo)
        age_hours = (now - memory.timestamp).total_seconds() / 3600

        recency_score = max(0.0, 1.0 - age_hours / 168)

        return memory.importance + recency_score

    def rank(
        self,
        memories: list[MemoryItem],
        *,
        limit: int = 10,
    ) -> list[MemoryItem]:
        """
        Return the highest ranked memories.
        """

        ranked = sorted(
            memories,
            key=self.score,
            reverse=True,
        )

        return ranked[:limit]
