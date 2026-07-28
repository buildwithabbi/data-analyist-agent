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
