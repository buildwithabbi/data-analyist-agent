"""Builds and persists memories only when an execution is worth retaining."""

from datetime import datetime, timezone

from .deduplicator import MemoryDeduplicator
from .models import EpisodeMemory, MemoryMetadata
from .scorer import MemoryScorer


class MemoryWriter:
    def __init__(self, repository, scorer: MemoryScorer | None = None, deduplicator: MemoryDeduplicator | None = None) -> None:
        self.repository = repository
        self.scorer = scorer or MemoryScorer()
        self.deduplicator = deduplicator or MemoryDeduplicator()

    def write_episode(self, state: dict) -> EpisodeMemory | None:
        results = state.get("tool_results", [])
        success = bool(results) and all(item.status == "success" for item in results)
        if not success:
            return None
        messages = state.get("messages", [])
        query = next((str(item.content) for item in messages if getattr(item, "type", None) == "human"), "")
        plan = state.get("plan")
        summary = next((str(item.content) for item in reversed(messages) if getattr(item, "type", None) == "ai" and item.content), "")
        tools = [item.tool for item in results]
        score = self.scorer.score(success=True, tool_count=len(tools), has_summary=bool(summary), novel=True)
        memory = EpisodeMemory(
            content=f"Successful analysis for: {query}. {summary}".strip(),
            user_query=query,
            plan=plan.__dict__ if plan else {},
            tool_results=[{"tool": item.tool, "status": item.status, "result": item.result} for item in results],
            summary=summary,
            artifacts=[item.model_dump() for item in state.get("artifacts", [])],
            execution_trace=list(state.get("trace", [])),
            metadata=MemoryMetadata(tool_chain=tools, dataset="sales", success=True, tags=["execution", *tools]),
            score=score,
        )
        memory.content_hash = self.deduplicator.fingerprint(memory)
        if score.overall_score < 0.55 or self.deduplicator.is_duplicate(self.repository, memory):
            return None
        return self.repository.store(memory)
