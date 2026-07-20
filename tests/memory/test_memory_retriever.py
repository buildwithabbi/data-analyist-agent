from datetime import datetime, timedelta, timezone

from data_analyst_agent.memory.short_term import ShortTermMemory
from data_analyst_agent.services.memory_retriever import MemoryRetriever


def test_retrieve_includes_all_stm_and_limited_recent_ltm(ltm, memory_factory):
    stm = ShortTermMemory()
    oldest = memory_factory(
        "Old long term",
        importance=0.1,
        timestamp=datetime.now(timezone.utc) - timedelta(days=3),
    )
    recent = memory_factory("Recent long term", importance=0.9)
    ltm.add(oldest)
    ltm.add(recent)
    short_term = memory_factory("Current task", importance=0.3)
    stm.add(short_term)

    memories = MemoryRetriever(stm, ltm).retrieve(max_long_term=1)

    assert {memory.id for memory in memories} == {recent.id, short_term.id}


def test_retrieve_ranks_results(memory_factory, ltm):
    stm = ShortTermMemory()
    stm.add(memory_factory("Lower score", importance=0.1))
    high = memory_factory("Higher score", importance=0.9)
    ltm.add(high)

    memories = MemoryRetriever(stm, ltm).retrieve()

    assert memories[0].id == high.id
