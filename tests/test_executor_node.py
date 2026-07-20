import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from data_analyst_agent.agent.nodes import executor_node
from data_analyst_agent.domain.models import Plan


def test_executor_sends_compact_context_and_keeps_only_one_tool_call(monkeypatch):
    captured = {}

    def fake_invoke(model, messages):
        captured["messages"] = messages
        return AIMessage(
            content="",
            tool_calls=[
                {"name": "run_sql", "args": {"query": "SELECT 1"}, "id": "one"},
                {"name": "run_sql", "args": {"query": "SELECT 2"}, "id": "two"},
            ],
        )

    monkeypatch.setattr(executor_node, "safe_invoke", fake_invoke)
    state = {
        "messages": [HumanMessage(content="Show monthly sales")],
        "trace": [],
        "tool_results": [],
    }

    result = executor_node.executor(state)

    assert len(captured["messages"]) == 2
    assert captured["messages"][1].content == "Show monthly sales"
    assert len(result["messages"][0].tool_calls) == 1
    assert result["messages"][0].tool_calls[0]["id"] == "one"


def test_executor_advances_plan_after_a_successful_tool_result(monkeypatch):
    monkeypatch.setattr(
        executor_node,
        "safe_invoke",
        lambda model, messages: AIMessage(content="Ready to chart."),
    )
    state = {
        "messages": [
            HumanMessage(content="Show monthly sales"),
            ToolMessage(
                name="run_sql",
                tool_call_id="sql-1",
                content=json.dumps(
                    {"status": "success", "tool": "run_sql", "row_count": 1, "rows": []}
                ),
            ),
        ],
        "plan": Plan(goal="Sales chart", steps=["Run SQL", "Generate chart", "Summarize"]),
        "trace": [],
        "tool_results": [],
    }

    result = executor_node.executor(state)

    assert result["plan"].current_step == 1


def test_parse_tool_result_keeps_failed_query_for_repair_context():
    result = executor_node._parse_tool_result(
        {
            "status": "error",
            "tool": "run_sql",
            "query": "SELECT EXTRACT(YEAR FROM order_date) FROM sales",
            "message": "SQLite does not support EXTRACT(...).",
        },
        "run_sql",
    )

    assert result.result == {"query": "SELECT EXTRACT(YEAR FROM order_date) FROM sales"}


def test_executor_requires_a_tool_before_the_final_plan_step(monkeypatch):
    captured = {}

    def fake_invoke(model, messages):
        captured["model"] = model
        return AIMessage(content="", tool_calls=[])

    monkeypatch.setattr(executor_node, "safe_invoke", fake_invoke)
    state = {
        "messages": [HumanMessage(content="Show monthly sales")],
        "plan": Plan(goal="Sales chart", steps=["Run SQL", "Chart", "Summarize"]),
        "trace": [],
        "tool_results": [],
    }

    executor_node.executor(state)

    assert captured["model"] is executor_node.llm_with_required_tool
