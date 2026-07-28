"""The single public entry point for durable memory."""

from datetime import datetime, timezone
from pathlib import Path

from .compressor import MemoryCompressor
from .deduplicator import MemoryDeduplicator
from .enums import MemoryLifecycle
from .models import Memory
from .retriever import MemoryRetriever
from .sqlite_repository import SQLiteMemoryRepository
from .writer import MemoryWriter


class MemoryManager:
    def __init__(self, repository=None) -> None:
        self.repository = repository or SQLiteMemoryRepository(
            Path(__file__).resolve().parents[3] / "memory" / "agent_memory.db"
        )
        self.deduplicator = MemoryDeduplicator()
        self.retriever = MemoryRetriever(self.repository)
        self.writer = MemoryWriter(self.repository, deduplicator=self.deduplicator)
        self.compressor = MemoryCompressor()

    def store(self, memory: Memory) -> Memory | None:
        memory.content_hash = memory.content_hash or self.deduplicator.fingerprint(memory)
        if self.deduplicator.is_duplicate(self.repository, memory):
            return None
        return self.repository.store(memory)

    def write(self, state: dict):
        return self.writer.write_episode(state)

    def retrieve(self, query: str, *, limit: int = 5, **filters) -> list[Memory]:
        return self.retriever.retrieve(query, limit=limit, **filters)

    def search(self, **filters) -> list[Memory]:
        return self.repository.search(**filters)

    def archive(self, memory_id: str) -> Memory:
        memory = self._required(memory_id)
        memory.lifecycle = MemoryLifecycle.ARCHIVED
        memory.metadata.updated_at = datetime.now(timezone.utc)
        return self.repository.update(memory)

    def delete(self, memory_id: str) -> bool:
        return self.repository.delete(memory_id)

    def compress(self, memory_id: str) -> str:
        memory = self._required(memory_id)
        return self.compressor.compress_episode(memory) if hasattr(memory, "user_query") else memory.content

    def deduplicate(self) -> int:
        seen, removed = set(), 0
        for memory in self.repository.search(lifecycle=MemoryLifecycle.ACTIVE):
            if memory.content_hash in seen:
                self.repository.delete(memory.id)
                removed += 1
            else:
                seen.add(memory.content_hash)
        return removed

    def expire(self, before: datetime) -> int:
        changed = 0
        for memory in self.repository.search(lifecycle=MemoryLifecycle.ACTIVE):
            if memory.expires_at and memory.expires_at <= before:
                memory.lifecycle = MemoryLifecycle.EXPIRED
                self.repository.update(memory)
                changed += 1
        return changed

    def _required(self, memory_id: str) -> Memory:
        memory = self.repository.get(memory_id)
        if memory is None:
            raise KeyError(f"Memory {memory_id} does not exist.")
        return memory


memory_manager = MemoryManager()
