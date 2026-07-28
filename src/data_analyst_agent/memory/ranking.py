"""Backend-neutral lexical ranking used until an embedding provider is configured."""

from datetime import datetime, timezone
import re

from .models import Memory


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", value.lower()))


class MemoryRanker:
    def score(self, query: str, memory: Memory) -> float:
        query_tokens, memory_tokens = _tokens(query), _tokens(memory.content)
        similarity = len(query_tokens & memory_tokens) / len(query_tokens | memory_tokens) if query_tokens else 0.0
        age_days = max(0.0, (datetime.now(timezone.utc) - memory.metadata.updated_at).total_seconds() / 86400)
        recency = 1 / (1 + age_days / 30)
        return 0.45 * similarity + 0.25 * memory.score.importance + 0.15 * memory.score.confidence + 0.15 * recency

    def rank(self, query: str, memories: list[Memory], limit: int) -> list[Memory]:
        return sorted(memories, key=lambda item: self.score(query, item), reverse=True)[:limit]
