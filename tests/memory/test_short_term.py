from data_analyst_agent.memory.short_term import ShortTermMemory


def test_add_returns_a_copy_of_the_memory(stm, memory_factory):
    memory = memory_factory("User prefers weekly reports")

    stm.add(memory)
    memory.content = "Changed outside storage"

    stored = stm.get_last()
    assert stored is not None
    assert stored.content == "User prefers weekly reports"
    assert stored.id == memory.id


def test_blank_memory_is_not_stored(stm, memory_factory):
    stm.add(memory_factory("   "))

    assert stm.count() == 0


def test_add_unique_deduplicates_category_and_content(stm, memory_factory):
    stm.add_unique(memory_factory("Use INR", category="preference"))
    stm.add_unique(memory_factory("Use INR", category="preference"))
    stm.add_unique(memory_factory("Use INR", category="format"))

    assert stm.count() == 2


def test_update_replaces_existing_memory_and_upserts_new_one(stm, memory_factory):
    original = memory_factory("Initial", memory_id="known")
    replacement = memory_factory("Updated", memory_id="known")
    new_memory = memory_factory("New", memory_id="new")
    stm.add(original)

    stm.update(replacement)
    stm.update(new_memory)

    assert [item.content for item in stm.get_all()] == ["Updated", "New"]


def test_remove_and_clear(stm, memory_factory):
    first = memory_factory("First", memory_id="first")
    stm.add(first)
    stm.add(memory_factory("Second", memory_id="second"))

    stm.remove("first")
    assert [item.id for item in stm.get_all()] == ["second"]

    stm.clear()
    assert stm.get_last() is None
    assert stm.count() == 0
