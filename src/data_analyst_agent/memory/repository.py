"""Abstract persistence boundary for memory backends."""

from abc import ABC, abstractmethod

from .enums import MemoryKind, MemoryLifecycle
from .models import Memory


class MemoryRepository(ABC):
    @abstractmethod
    def store(self, memory: Memory) -> Memory: ...

    @abstractmethod
    def get(self, memory_id: str) -> Memory | None: ...

    @abstractmethod
    def search(
        self,
        *,
        kind: MemoryKind | None = None,
        tags: list[str] | None = None,
        dataset: str | None = None,
        tool_chain: list[str] | None = None,
        lifecycle: MemoryLifecycle = MemoryLifecycle.ACTIVE,
    ) -> list[Memory]: ...

    @abstractmethod
    def update(self, memory: Memory) -> Memory: ...

    @abstractmethod
    def delete(self, memory_id: str) -> bool: ...
