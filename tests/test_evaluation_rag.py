"""Unit tests for RAGEvaluator metrics."""

from data_analyst_agent.platform.evaluation import RAGEvaluator


def test_rag_evaluator_metrics():
    query = "What is total sales by region?"
    answer = "The total sales by region shows Technology leading with 40%."
    contexts = [
        "Sales by category shows Technology leading sales with high profit margins.",
        "Region sales metrics include North America, Europe, and Asia.",
    ]

    res = RAGEvaluator.evaluate_rag(query, answer, contexts)

    assert "faithfulness" in res
    assert "answer_relevance" in res
    assert "context_recall" in res
    assert "overall_rag_score" in res
    assert res["faithfulness"] > 0.0
    assert res["answer_relevance"] > 0.0
    assert res["context_recall"] > 0.0
    assert res["retrieved_chunks_count"] == 2


def test_rag_evaluator_empty_context():
    res = RAGEvaluator.evaluate_rag("Test query", "Test answer", [])
    assert res["faithfulness"] == 0.0
    assert res["overall_rag_score"] == 0.0
