from pathlib import Path

from .embedding.local import HashEmbeddingProvider
from .enums import DocumentType
from .ingestion.cleaner import clean
from .ingestion.chunker import chunk
from .ingestion.parser import parse
from .models import DocumentMetadata, KnowledgeDocument
from .retrieval.hybrid import HybridRetriever
from .retrieval.reranker import Reranker
from .sqlite_repository import SQLiteKnowledgeRepository

class KnowledgeManager:
    def __init__(self, repository=None, embedding_provider=None):
        self.repository = repository or SQLiteKnowledgeRepository(Path(__file__).resolve().parents[3] / "knowledge" / "knowledge.db")
        self.embedding_provider = embedding_provider or HashEmbeddingProvider()
        self.retriever = HybridRetriever(self.repository, self.embedding_provider)
        self.reranker = Reranker()
    def ingest(self, path, *, tags=None, dataset=None):
        content, kind = parse(path); source = str(Path(path))
        document = KnowledgeDocument(type=DocumentType(kind), content=clean(content), metadata=DocumentMetadata(source=source, title=Path(path).name, tags=tags or [], dataset=dataset))
        chunks = chunk(document.id, document.content, {"source": source, "tags": ",".join(document.metadata.tags)})
        for item, embedding in zip(chunks, self.embedding_provider.embed([item.text for item in chunks])): item.embedding = embedding
        self.repository.store_document(document); self.repository.store_chunks(chunks)
        return document, chunks
    def add_text(self, text, *, source="inline", title="", tags=None, dataset=None):
        document = KnowledgeDocument(type=DocumentType.TXT, content=clean(text), metadata=DocumentMetadata(source=source, title=title or source, tags=tags or [], dataset=dataset))
        chunks = chunk(document.id, document.content, {"source": source, "tags": ",".join(document.metadata.tags)})
        for item, embedding in zip(chunks, self.embedding_provider.embed([item.text for item in chunks])): item.embedding = embedding
        self.repository.store_document(document); self.repository.store_chunks(chunks)
        return document, chunks
    def retrieve(self, query, *, limit=5, **filters):
        return self.reranker.rerank(query, self.retriever.retrieve(query, limit=max(limit*4, 20), **filters), limit)

knowledge_manager = KnowledgeManager()
