from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

import pytest

from data_analyst_agent.domain.models import MemoryItem
from data_analyst_agent.memory.long_term import LongTermMemory
from data_analyst_agent.memory.short_term import ShortTermMemory


@pytest.fixture
def memory_factory() -> Callable[..., MemoryItem]:
    """Build memory records with predictable defaults for tests."""

    def build(
        content: str = "Remember this",
        *,
        category: str = "preference",
        importance: float = 0.5,
        timestamp: datetime | None = None,
        memory_id: str | None = None,
    ) -> MemoryItem:
        values = {
            "content": content,
            "category": category,
            "importance": importance,
            "timestamp": timestamp or datetime.now(timezone.utc),
        }
        if memory_id is not None:
            values["id"] = memory_id
        return MemoryItem(**values)

    return build


@pytest.fixture
def stm() -> ShortTermMemory:
    return ShortTermMemory()


@pytest.fixture
def ltm(tmp_path, monkeypatch) -> LongTermMemory:
    """Return an LTM instance backed by a per-test SQLite database."""

    monkeypatch.chdir(tmp_path)
    memory = LongTermMemory()
    yield memory
    memory.clear()
