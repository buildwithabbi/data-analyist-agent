"""Memory retrieval and ranking service."""

from datetime import datetime, timezone

from .models import Memory
from .ranking import MemoryRanker
from .repository import MemoryRepository


class MemoryRetriever:
    def __init__(self, repository: MemoryRepository, ranker: MemoryRanker | None = None) -> None:
        self.repository, self.ranker = repository, ranker or MemoryRanker()

    def retrieve(self, query: str, *, limit: int = 5, **filters) -> list[Memory]:
        candidates = self.repository.search(**filters)
        ranked = self.ranker.rank(query, candidates, limit)
        now = datetime.now(timezone.utc)
        for memory in ranked:
            memory.access_count += 1
            memory.last_accessed_at = now
            self.repository.update(memory)
        return ranked
