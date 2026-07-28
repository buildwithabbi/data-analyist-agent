from data_analyst_agent.platform.evaluation import EvaluationEngine
from data_analyst_agent.platform.governance import GovernancePolicy
from data_analyst_agent.platform.observability import ObservabilityManager
from data_analyst_agent.platform.sdk import Platform


def test_evaluation_engine_reports_metrics():
    engine = EvaluationEngine()
    report = engine.evaluate(
        task="Summarize the sales trend",
        answer="Sales grew steadily over the period.",
        tool_calls=[{"tool": "run_sql", "latency_ms": 120, "success": True}],
        plan=["inspect data", "summarize"],
        agent="planner",
    )

    assert report["accuracy"] >= 0
    assert report["tool_efficiency"] >= 0
    assert report["metrics"]["tool_calls"] == 1


def test_governance_masks_pii_and_audits():
    policy = GovernancePolicy()
    masked = policy.mask_pii("Email me at someone@example.com")

    assert "REDACTED" in masked
    assert policy.audit("planner", "tool_call") is not None


def test_observability_tracks_spans_and_metrics():
    observability = ObservabilityManager()
    span_id = observability.start_span("planner", metadata={"query": "sales"})
    observability.record_event(span_id, "tool_call", {"tool": "run_sql"})
    observability.finish_span(span_id, success=True)

    assert observability.get_trace("planner")[0]["name"] == "planner"


def test_platform_run_returns_evaluations_and_trace_id():
    platform = Platform()
    result = platform.run("Summarize the repository")

    assert result["status"] == "completed"
    assert result["trace_id"]
    assert "evaluations" in result
