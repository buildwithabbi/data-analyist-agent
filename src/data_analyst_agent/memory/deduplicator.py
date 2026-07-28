"""Content-hash deduplication independent of the selected backend."""

import hashlib

from .models import Memory
from .repository import MemoryRepository


class MemoryDeduplicator:
    def fingerprint(self, memory: Memory) -> str:
        return hashlib.sha256(f"{memory.kind.value}:{memory.content.strip().lower()}".encode()).hexdigest()

    def is_duplicate(self, repository: MemoryRepository, memory: Memory) -> bool:
        return any(item.content_hash == memory.content_hash for item in repository.search(kind=memory.kind))
