from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import DocumentType, KnowledgeStatus


def now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentMetadata(BaseModel):
    source: str
    title: str = ""
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=now)
    dataset: str | None = None
    extra: dict[str, str] = Field(default_factory=dict)


class KnowledgeDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: DocumentType
    content: str
    metadata: DocumentMetadata
    status: KnowledgeStatus = KnowledgeStatus.ACTIVE


class KnowledgeChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    text: str = Field(min_length=1)
    heading: str = ""
    section: str = ""
    page: int | None = None
    index: int
    metadata: dict[str, str] = Field(default_factory=dict)
    embedding: list[float] = Field(default_factory=list)


class KnowledgeHit(BaseModel):
    chunk: KnowledgeChunk
    score: float
    dense_score: float = 0.0
    keyword_score: float = 0.0

    @property
    def citation(self) -> str:
        page = f", p. {self.chunk.page}" if self.chunk.page else ""
        return f"{self.chunk.metadata.get('source', self.chunk.document_id)}{page}, chunk {self.chunk.index}"
