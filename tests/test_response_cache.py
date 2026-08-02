from data_analyst_agent.services.response_cache import ResponseCache, normalize_question


def test_response_cache_is_normalized_and_dataset_scoped(tmp_path):
    cache = ResponseCache(tmp_path / "responses.db")
    payload = {"answer": "January had the highest sales."}
    cache.put("sha256:first", "  Show   monthly SALES ", payload)

    assert cache.get("sha256:first", "show monthly sales") == payload
    assert cache.get("sha256:second", "show monthly sales") is None


def test_question_normalization_keeps_words_but_removes_formatting_noise():
    assert normalize_question(" Sales\n  by month ") == "sales by month"
