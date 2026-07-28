from datetime import datetime, timedelta, timezone

from data_analyst_agent.memory.enums import MemoryLifecycle
from data_analyst_agent.memory.manager import MemoryManager
from data_analyst_agent.memory.models import MemoryMetadata, SemanticMemory
from data_analyst_agent.memory.scorer import MemoryScorer
from data_analyst_agent.memory.sqlite_repository import SQLiteMemoryRepository


def make_manager(tmp_path):
    return MemoryManager(SQLiteMemoryRepository(tmp_path / "memory.db"))


def semantic(content: str, *, tags=None):
    return SemanticMemory(
        content=content,
        metadata=MemoryMetadata(tags=tags or ["sales"], dataset="sales", tool_chain=["run_sql"]),
        score=MemoryScorer().score(success=True, tool_count=1, has_summary=True, novel=True),
    )


def test_memory_manager_persists_filters_and_ranks(tmp_path):
    manager = make_manager(tmp_path)
    stored = manager.store(semantic("Monthly sales SQL groups by strftime month."))
    manager.store(semantic("Customer segmentation insight.", tags=["customers"]))

    retrieved = manager.retrieve("monthly sales trend", limit=1, dataset="sales")

    assert retrieved[0].id == stored.id
    assert retrieved[0].access_count == 1
    assert manager.search(tags=["customers"])[0].content.startswith("Customer")


def test_memory_manager_rejects_duplicates_and_manages_lifecycle(tmp_path):
    manager = make_manager(tmp_path)
    first = manager.store(semantic("Reusable monthly sales query."))
    assert manager.store(semantic("Reusable monthly sales query.")) is None

    archived = manager.archive(first.id)
    assert archived.lifecycle == MemoryLifecycle.ARCHIVED
    assert manager.search() == []
    assert manager.delete(first.id) is True


def test_memory_manager_expires_records(tmp_path):
    manager = make_manager(tmp_path)
    memory = semantic("Expiring knowledge")
    memory.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    stored = manager.store(memory)

    assert manager.expire(datetime.now(timezone.utc)) == 1
    assert manager.repository.get(stored.id).lifecycle == MemoryLifecycle.EXPIRED
