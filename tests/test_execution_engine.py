from langchain_core.messages import AIMessage, ToolMessage

from data_analyst_agent.agent.nodes.reflection_node import reflection_node
from data_analyst_agent.domain.enums import ExecutionStatus
from data_analyst_agent.domain.models import Plan
from data_analyst_agent.domain.models import PlanStep
from data_analyst_agent.services.execution import (
    missing_dependencies,
    validate_downstream_chart_data,
    validate_tool_result,
)
from data_analyst_agent.domain.models import ChartResult, ToolResult
from data_analyst_agent.agent.tool_routing import route_tools
from data_analyst_agent.agent.nodes.executor_node import (
    _chart_data_from_results,
    _chart_series_from_results,
)
from data_analyst_agent.services.execution import current_step


def test_successful_tool_advances_only_the_current_step_and_records_output():
    plan = Plan(goal="Chart monthly sales", steps=["Run SQL", "Generate chart"])
    tool_call = {
        "name": "run_sql",
        "args": {"query": "SELECT 1 AS label, 2 AS value"},
        "id": "call-1",
        "type": "tool_call",
    }
    state = {
        "plan": plan,
        "messages": [
            AIMessage(content="", tool_calls=[tool_call]),
            ToolMessage(
                content=(
                    '{"status":"success","tool":"run_sql",'
                    '"row_count":1,"rows":[{"label":"1","value":2}]}'
                ),
                name="run_sql",
                tool_call_id="call-1",
            ),
        ],
        "tool_results": [],
        "execution_records": [],
        "trace": [],
        "repair_attempts": 0,
    }

    updated = reflection_node(state)

    assert updated["plan"].current_step == 1
    assert updated["tool_results"][-1].result["rows"] == [{"label": "1", "value": 2}]
    assert updated["execution_records"][-1].tool_input == tool_call["args"]
    assert updated["execution_records"][-1].success is True
    assert updated["repair_decision"].status == ExecutionStatus.SUCCESS


def test_failed_tool_does_not_advance_plan_step():
    state = {
        "plan": Plan(goal="Analyze sales", steps=["Run SQL"]),
        "messages": [
            ToolMessage(
                content='{"status":"error","tool":"run_sql","message":"bad SQL"}',
                name="run_sql",
                tool_call_id="call-1",
            ),
        ],
        "tool_results": [],
        "execution_records": [],
        "trace": [],
        "repair_attempts": 0,
    }

    updated = reflection_node(state)

    assert updated["plan"].current_step == 0
    assert updated["execution_records"][-1].success is False
    assert updated["repair_decision"].status == ExecutionStatus.RECOVERABLE_FAILURE


def test_unexpected_tool_does_not_complete_the_step():
    state = {
        "plan": Plan(
            goal="Create chart",
            steps=[PlanStep(action="GENERATE_CHART", description="Create chart", expected_tool="generate_chart")],
        ),
        "messages": [
            ToolMessage(
                content='{"status":"success","tool":"run_sql","rows":[]}',
                name="run_sql",
                tool_call_id="call-1",
            ),
        ],
        "tool_results": [],
        "execution_records": [],
        "trace": [],
        "repair_attempts": 0,
    }

    updated = reflection_node(state)

    assert updated["plan"].current_step == 0
    assert updated["tool_results"][-1].status == "error"
    assert "requires generate_chart" in updated["tool_results"][-1].message


def test_chart_contract_requires_a_successful_sql_result():
    step = PlanStep(
        action="GENERATE_CHART",
        description="Visualize metrics",
        expected_tool="generate_chart",
        requires=["run_sql"],
    )

    assert missing_dependencies(step, []) == ["run_sql"]
    assert validate_tool_result(
        step, ToolResult(tool="run_sql", status="success", result={})
    ) == "Step requires generate_chart, but received run_sql."


def test_step_id_dependencies_are_enforced():
    plan = Plan(
        goal="Analyze sales",
        steps=[
            PlanStep(action="QUERY", description="Fetch sales"),
            PlanStep(action="SUMMARIZE", description="Summarize sales", dependencies=[1]),
        ],
    )

    assert missing_dependencies(plan.steps[1], [], plan) == ["step 1"]


def test_invalid_step_call_is_not_sent_to_the_tool_node():
    state = {
        "step_validation_error": "Expected generate_chart.",
        "messages": [
            AIMessage(
                content="",
                tool_calls=[{"name": "run_sql", "args": {}, "id": "call-1", "type": "tool_call"}],
            )
        ],
    }

    assert route_tools(state) == "end"


def test_chart_data_is_projected_from_structured_sql_output():
    state = {
        "tool_results": [
            ToolResult(
                tool="run_sql",
                status="success",
                result={
                    "rows": [
                        {"month": "2018-01", "total_sales": 100, "total_profit": 20},
                        {"month": "2018-02", "total_sales": 120, "total_profit": 25},
                    ]
                },
            )
        ]
    }

    assert _chart_data_from_results(state, "Monthly Profit Trend") == [
        {"label": "2018-01", "value": 20},
        {"label": "2018-02", "value": 25},
    ]


def test_summary_step_has_no_expected_tool():
    plan = Plan(
        goal="Summarize",
        steps=[PlanStep(action="SUMMARIZE", description="Provide findings")],
    )

    assert current_step(plan).expected_tool is None


def test_multi_series_chart_data_is_built_from_sql_output():
    state = {
        "tool_results": [
            ToolResult(
                tool="run_sql",
                status="success",
                result={
                    "rows": [
                        {"month": "2018-01", "total_sales": 100, "total_profit": 20},
                        {"month": "2018-02", "total_sales": 120, "total_profit": 25},
                    ]
                },
            )
        ]
    }

    assert _chart_series_from_results(state, ["sales", "profit"]) == [
        {
            "name": "Sales",
            "data": [{"label": "2018-01", "value": 100}, {"label": "2018-02", "value": 120}],
        },
        {
            "name": "Profit",
            "data": [{"label": "2018-01", "value": 20}, {"label": "2018-02", "value": 25}],
        },
    ]


def test_multi_series_contract_rejects_a_single_series_result():
    step = PlanStep(
        action="GENERATE_CHART",
        description="Create a multi-series chart for sales and profit",
        expected_tool="generate_chart",
        expected_output="multi_series_line_chart",
    )

    assert validate_tool_result(
        step,
        ToolResult(
            tool="generate_chart",
            status="success",
            result={"series_count": 1},
            typed_result=ChartResult(
                chart_path="charts/example.png",
                chart_type="line",
                title="Example",
                series_count=1,
            ),
        ),
    ) == "Step requires 2 chart series (sales, profit), but produced 1."


def test_query_must_produce_metrics_required_by_next_multi_series_chart():
    plan = Plan(
        goal="Monthly trends",
        steps=[
            PlanStep(action="QUERY", description="Retrieve monthly metrics"),
            PlanStep(
                action="GENERATE_CHART",
                description="Chart sales and profit",
                expected_tool="generate_chart",
                expected_output="multi_series_line_chart",
                inputs=["sales", "profit"],
            ),
        ],
    )

    error = validate_downstream_chart_data(
        plan,
        plan.steps[0],
        ToolResult(tool="run_sql", status="success", result={"rows": [{"label": "2018-01", "value": 10}]}),
    )

    assert "sales, profit" in error
