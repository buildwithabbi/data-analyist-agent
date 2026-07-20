from __future__ import annotations

from langchain_core.embeddings import Embeddings


class EmbeddingService:
    """
    Generates vector embeddings for memories.

    This class abstracts the embedding provider so it can
    be swapped without affecting the rest of the system.
    """

    def __init__(self, embeddings: Embeddings) -> None:
        self._embeddings = embeddings

    def embed_text(self, text: str) -> list[float]:
        """
        Generate an embedding for a single text.
        """

        return self._embeddings.embed_query(text)

    def embed_documents(
        self,
        documents: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple documents.
        """

        return self._embeddings.embed_documents(documents)