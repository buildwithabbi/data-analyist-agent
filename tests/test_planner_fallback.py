from types import SimpleNamespace

from data_analyst_agent.services import planner
from data_analyst_agent.services.planner import _plan_from_response


def test_empty_planner_response_uses_a_valid_chart_plan():
    plan = _plan_from_response("Total sales, profit, and discount with a chart", "")

    assert [step.expected_tool for step in plan.steps] == ["run_sql", "generate_chart", None]
    assert plan.steps[1].inputs == ["sales", "profit", "discount"]


def test_provider_failure_response_uses_default_plan(monkeypatch):
    monkeypatch.setattr(planner, "safe_invoke", lambda *_: SimpleNamespace(content=None))

    plan = planner.create_plan("Show sales")

    assert [step.expected_tool for step in plan.steps] == ["run_sql", None]
