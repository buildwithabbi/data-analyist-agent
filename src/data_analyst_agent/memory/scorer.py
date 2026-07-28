"""Deterministic quality scoring for memory-write decisions."""

from .models import MemoryScore


class MemoryScorer:
    def score(self, *, success: bool, tool_count: int, has_summary: bool, novel: bool) -> MemoryScore:
        confidence = 0.9 if success else 0.2
        quality = min(1.0, 0.55 + 0.1 * min(tool_count, 3) + (0.15 if has_summary else 0)) if success else 0.1
        importance = min(1.0, 0.45 + 0.1 * min(tool_count, 4) + (0.15 if has_summary else 0))
        novelty = 0.85 if novel else 0.05
        reuse = 0.75 if success and tool_count else 0.25
        overall = round(0.30 * importance + 0.25 * novelty + 0.20 * reuse + 0.15 * confidence + 0.10 * quality, 4)
        return MemoryScore(importance=importance, novelty=novelty, reuse_probability=reuse, confidence=confidence, quality=quality, overall_score=overall)
