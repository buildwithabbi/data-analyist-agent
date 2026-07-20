from data_analyst_agent.services.memory_classifier import MemoryClassifier


def test_should_store_rejects_blank_content(memory_factory):
    classifier = MemoryClassifier()

    assert classifier.should_store(memory_factory(" meaningful ")) is True
    assert classifier.should_store(memory_factory("  ")) is False


def test_importance_threshold_controls_long_term_classification(memory_factory):
    classifier = MemoryClassifier()

    assert classifier.is_long_term(memory_factory(importance=0.8)) is True
    assert classifier.is_long_term(memory_factory(importance=0.79)) is False
