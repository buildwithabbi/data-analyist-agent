from datetime import datetime, timedelta, timezone

from data_analyst_agent.services.memory_ranker import MemoryRanker


def test_score_favors_important_and_recent_memories(memory_factory):
    ranker = MemoryRanker()
    recent = memory_factory("Recent", importance=0.6)
    old = memory_factory(
        "Old",
        importance=0.6,
        timestamp=datetime.now(timezone.utc) - timedelta(days=8),
    )

    assert ranker.score(recent) > ranker.score(old)


def test_rank_orders_and_limits_memories(memory_factory):
    ranker = MemoryRanker()
    memories = [
        memory_factory("Low", importance=0.1),
        memory_factory("High", importance=0.9),
        memory_factory("Medium", importance=0.5),
    ]

    ranked = ranker.rank(memories, limit=2)

    assert [memory.content for memory in ranked] == ["High", "Medium"]
