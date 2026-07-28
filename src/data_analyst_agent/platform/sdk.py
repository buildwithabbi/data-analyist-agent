"""A small SDK facade that exposes the platform to other callers."""

from __future__ import annotations

import uuid
from typing import Any

from ..multi_agent.orchestrator import Orchestrator
from .evaluation import EvaluationEngine
from .governance import GovernancePolicy
from .observability import ObservabilityManager


class Platform:
    """Convenience facade for running tasks through the platform stack."""

    def __init__(self) -> None:
        self.orchestrator = Orchestrator(approval_required=False)
        self.evaluator = EvaluationEngine()
        self.governance = GovernancePolicy()
        self.observability = ObservabilityManager()

    def run(self, query: str) -> dict[str, Any]:
        trace_id = str(uuid.uuid4())
        span_id = self.observability.start_span("platform", metadata={"query": query, "trace_id": trace_id})
        self.observability.record_event(span_id, "query_received", {"query": query})

        result = self.orchestrator.run(query, approved=True)
        evaluation = self.evaluator.evaluate(
            task=query,
            answer=str(result.get("response", "")),
            tool_calls=[],
            plan=result.get("context", {}).data.get("plan") and [step.description for step in result.get("context", {}).data.get("plan").steps] or [],
            agent="platform",
        )
        self.governance.audit("platform", "task_completed", trace_id=trace_id)
        self.observability.record_event(span_id, "task_completed", {"evaluation": evaluation})
        self.observability.finish_span(span_id, success=True)

        return {
            "status": result.get("status", "completed"),
            "trace_id": trace_id,
            "response": result.get("response", ""),
            "evaluations": evaluation,
        }

    def register_agent(self, name: str, agent: Any) -> None:
        self.orchestrator.registry.register(name, agent)

    def register_tool(self, name: str, tool: Any) -> None:
        self.orchestrator.registry.register(name, tool)

    def register_mcp(self, name: str, capability: Any) -> None:
        self.orchestrator.registry.register(name, capability)

    def register_memory(self, name: str, memory: Any) -> None:
        self.orchestrator.registry.register(name, memory)
