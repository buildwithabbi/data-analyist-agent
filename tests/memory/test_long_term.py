from datetime import datetime, timedelta, timezone


def test_add_and_read_memories(ltm, memory_factory):
    oldest = memory_factory(
        "Old preference",
        timestamp=datetime.now(timezone.utc) - timedelta(days=1),
    )
    newest = memory_factory("New preference")
    ltm.add(oldest)
    ltm.add(newest)

    assert ltm.count() == 2
    assert [item.id for item in ltm.get_all()] == [oldest.id, newest.id]
    assert ltm.get_last() is not None
    assert ltm.get_last().id == newest.id


def test_add_unique_and_blank_content(ltm, memory_factory):
    ltm.add_unique(memory_factory("Use concise answers"))
    ltm.add_unique(memory_factory("Use concise answers"))
    ltm.add(memory_factory("  "))

    assert ltm.count() == 1


def test_update_upserts_and_remove(ltm, memory_factory):
    memory = memory_factory("First version", memory_id="one")
    ltm.add(memory)
    updated = memory_factory("Second version", memory_id="one", importance=0.9)

    ltm.update(updated)
    ltm.update(memory_factory("Created by update", memory_id="two"))
    ltm.remove("one")

    stored = ltm.get_last()
    assert ltm.count() == 1
    assert stored is not None
    assert stored.id == "two"


def test_clear_removes_every_memory(ltm, memory_factory):
    ltm.add(memory_factory("One"))
    ltm.add(memory_factory("Two"))

    ltm.clear()

    assert ltm.count() == 0
    assert ltm.get_all() == []
