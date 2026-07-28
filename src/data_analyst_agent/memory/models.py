"""Storage-neutral models for reusable and episodic agent memory."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import MemoryKind, MemoryLifecycle


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryMetadata(BaseModel):
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    tags: list[str] = Field(default_factory=list)
    domain: str = "data_analytics"
    dataset: str | None = None
    owner: str | None = None
    tool_chain: list[str] = Field(default_factory=list)
    success: bool = True
    version: int = 1


class MemoryScore(BaseModel):
    importance: float = Field(ge=0, le=1)
    novelty: float = Field(ge=0, le=1)
    reuse_probability: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    quality: float = Field(ge=0, le=1)
    overall_score: float = Field(ge=0, le=1)


class MemoryRecord(BaseModel):
    """A persistable memory record; implementations never expose DB rows."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    kind: MemoryKind
    content: str = Field(min_length=1)
    metadata: MemoryMetadata = Field(default_factory=MemoryMetadata)
    score: MemoryScore
    lifecycle: MemoryLifecycle = MemoryLifecycle.ACTIVE
    last_accessed_at: datetime | None = None
    access_count: int = 0
    expires_at: datetime | None = None
    content_hash: str = ""


class EpisodeMemory(MemoryRecord):
    kind: MemoryKind = MemoryKind.EPISODE
    user_query: str
    plan: dict[str, Any] = Field(default_factory=dict)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    summary: str = ""
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    execution_trace: list[str] = Field(default_factory=list)


class SemanticMemory(MemoryRecord):
    kind: MemoryKind = MemoryKind.SEMANTIC
    knowledge_type: str = "insight"
    source_episode_id: str | None = None


Memory = EpisodeMemory | SemanticMemory
