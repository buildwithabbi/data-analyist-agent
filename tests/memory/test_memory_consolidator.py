from data_analyst_agent.services.memory_consolidator import MemoryConsolidator


def test_consolidate_merges_case_insensitive_duplicates(memory_factory):
    lower = memory_factory("use INR", category="Preference", importance=0.4)
    higher = memory_factory(" Use INR ", category="preference", importance=0.9)
    distinct = memory_factory("Use a table", category="format", importance=0.5)

    consolidated = MemoryConsolidator().consolidate([lower, higher, distinct])

    assert consolidated == [higher, distinct]


def test_consolidate_keeps_distinct_categories(memory_factory):
    first = memory_factory("Daily", category="schedule")
    second = memory_factory("Daily", category="frequency")

    assert MemoryConsolidator().consolidate([first, second]) == [first, second]
