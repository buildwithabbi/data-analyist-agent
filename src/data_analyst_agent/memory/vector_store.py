from __future__ import annotations

from abc import ABC, abstractmethod

from ..domain.models import MemoryItem


class VectorStore(ABC):
    """
    Abstract vector database interface.
    """

    @abstractmethod
    def add(
        self,
        memory: MemoryItem,
        embedding: list[float],
    ) -> None:
        ...

    @abstractmethod
    def search(
        self,
        embedding: list[float],
        *,
        k: int = 5,
    ) -> list[MemoryItem]:
        ...