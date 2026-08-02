"""Lightweight evaluation primitives for platform-level quality scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationResult:
    task: str
    answer: str
    accuracy: float = 0.0
    completeness: float = 0.0
    hallucination_rate: float = 0.0
    citation_quality: float = 0.0
    tool_efficiency: float = 0.0
    token_usage: int = 0
    latency: float = 0.0
    metrics: dict[str, Any] = field(default_factory=dict)


class EvaluationEngine:
    """Produce deterministic evaluation summaries for completed tasks."""

    def evaluate(self, *, task: str, answer: str, tool_calls: list[dict[str, Any]] | None = None,
                 plan: list[str] | None = None, agent: str | None = None) -> dict[str, Any]:
        tool_calls = tool_calls or []
        plan = plan or []
        success_count = sum(1 for tool in tool_calls if tool.get("success", False))
        accuracy = min(1.0, 0.45 + (0.15 * success_count) + (0.1 if answer.strip() else 0.0))
        completeness = min(1.0, 0.5 + (0.1 * min(len(plan), 3)))
        hallucination_rate = max(0.0, 0.2 - (0.02 * success_count))
        citation_quality = 0.9 if answer.strip() and "source" in answer.lower() else 0.6
        tool_efficiency = min(1.0, 0.7 + (0.05 * success_count))
        token_usage = sum(int(tool.get("tokens", 0)) for tool in tool_calls) + max(50, len(task.split()) * 8)
        latency = sum(float(tool.get("latency_ms", 0)) for tool in tool_calls) / max(1, len(tool_calls))

        metrics = {
            "tool_calls": len(tool_calls),
            "plan_steps": len(plan),
            "agent": agent or "unknown",
            "successes": success_count,
        }

        return {
            "task": task,
            "answer": answer,
            "accuracy": round(accuracy, 3),
            "completeness": round(completeness, 3),
            "hallucination_rate": round(hallucination_rate, 3),
            "citation_quality": round(citation_quality, 3),
            "tool_efficiency": round(tool_efficiency, 3),
            "token_usage": token_usage,
            "latency": round(latency, 3),
            "metrics": metrics,
        }


class RAGEvaluator:
    """Computes RAG evaluation metrics: Faithfulness, Answer Relevance, and Context Recall."""

    @classmethod
    def evaluate_rag(cls, query: str, answer: str, retrieved_contexts: list[str]) -> dict[str, Any]:
        """
        Evaluate RAG performance metrics.
        - Faithfulness: Groundedness of answer in retrieved context.
        - Answer Relevance: Alignment of answer with user query.
        - Context Recall: Sufficiency of retrieved context chunks.
        """
        if not retrieved_contexts:
            return {
                "faithfulness": 0.0,
                "answer_relevance": 0.0,
                "context_recall": 0.0,
                "overall_rag_score": 0.0,
                "retrieved_chunks_count": 0,
                "reason": "No context chunks retrieved.",
            }

        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        combined_context = " ".join(retrieved_contexts).lower()
        context_words = set(combined_context.split())

        # 1. Faithfulness (Grounding of answer words in context)
        overlap_with_context = len(answer_words & context_words) / max(1, len(answer_words))
        faithfulness = round(min(1.0, 0.4 + (0.6 * overlap_with_context)), 3)

        # 2. Answer Relevance (Alignment of answer with query)
        overlap_with_query = len(query_words & answer_words) / max(1, len(query_words))
        answer_relevance = round(min(1.0, 0.5 + (0.5 * overlap_with_query)), 3)

        # 3. Context Recall (Coverage of query tokens in context)
        context_recall = round(len(query_words & context_words) / max(1, len(query_words)), 3)

        overall_score = round(0.4 * faithfulness + 0.4 * answer_relevance + 0.2 * context_recall, 3)

        return {
            "faithfulness": faithfulness,
            "answer_relevance": answer_relevance,
            "context_recall": context_recall,
            "overall_rag_score": overall_score,
            "retrieved_chunks_count": len(retrieved_contexts),
        }

