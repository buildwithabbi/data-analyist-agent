from data_analyst_agent.memory.short_term import ShortTermMemory
from data_analyst_agent.services.memory_manager import MemoryManager


def test_remember_routes_memories_by_importance(ltm, memory_factory):
    stm = ShortTermMemory()
    manager = MemoryManager(stm=stm, ltm=ltm)
    short = memory_factory("Temporary context", importance=0.7)
    long = memory_factory("Durable preference", importance=0.8)

    manager.remember(short)
    manager.remember(long)

    assert stm.get_last() is not None and stm.get_last().id == short.id
    assert ltm.get_last() is not None and ltm.get_last().id == long.id


def test_manager_ignores_blank_and_can_forget_and_clear(ltm, memory_factory):
    stm = ShortTermMemory()
    manager = MemoryManager(stm=stm, ltm=ltm)
    blank = memory_factory(" ")
    temporary = memory_factory("Temporary", memory_id="temporary")
    durable = memory_factory("Durable", importance=0.9, memory_id="durable")

    manager.remember(blank)
    manager.remember(temporary)
    manager.remember(durable)
    manager.forget("temporary")
    manager.forget("durable", long_term=True)

    assert stm.count() == 0
    assert ltm.count() == 0

    manager.remember(temporary)
    manager.remember(durable)
    manager.clear()
    assert manager.retrieve() == []


def test_manager_update_and_score(ltm, memory_factory):
    stm = ShortTermMemory()
    manager = MemoryManager(stm=stm, ltm=ltm)
    original = memory_factory("Original", memory_id="short")
    updated = memory_factory("Updated", importance=0.4, memory_id="short")
    manager.remember(original)

    manager.update(updated)

    assert stm.get_last() is not None and stm.get_last().content == "Updated"
    assert manager.score(updated) == 0.4
