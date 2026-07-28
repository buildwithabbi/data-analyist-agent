"""Contract for future vector-store adapters."""

from abc import ABC, abstractmethod

from .models import Memory


class VectorMemoryRepository(ABC):
    @abstractmethod
    def upsert(self, memory: Memory, embedding: list[float]) -> None: ...

    @abstractmethod
    def similarity_search(self, embedding: list[float], limit: int) -> list[str]: ...
