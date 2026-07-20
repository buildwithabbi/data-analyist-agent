from data_analyst_agent.core.llm import MAX_TOKENS, MODEL_NAME, llm


def test_llm_uses_a_bounded_completion_budget():
    assert llm.max_tokens == MAX_TOKENS
    assert MAX_TOKENS == (256 if MODEL_NAME == "llama-3.1-8b-instant" else 1024)
