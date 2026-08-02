"""Content-hash deduplication independent of the selected backend."""

import hashlib

from .models import Memory
from .repository import MemoryRepository


class MemoryDeduplicator:
    def fingerprint(self, memory: Memory) -> str:
        # Identical insights on separate datasets must be retained separately;
        # their evidence and applicability are dataset-specific.
        value = f"{memory.kind.value}:{memory.metadata.dataset}:{memory.content.strip().lower()}"
        return hashlib.sha256(value.encode()).hexdigest()

    def is_duplicate(self, repository: MemoryRepository, memory: Memory) -> bool:
        return any(item.content_hash == memory.content_hash for item in repository.search(kind=memory.kind))
