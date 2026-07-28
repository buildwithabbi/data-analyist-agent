from langchain_core.messages import AIMessage, ToolMessage

from data_analyst_agent.agent.nodes.validator_node import validator_node
from data_analyst_agent.domain.enums import StepAction, StepStatus
from data_analyst_agent.domain.models import Plan, PlanStep
from data_analyst_agent.agent.tool_results import parse_tool_result


def test_validator_completes_query_step_and_registers_dataset_artifact():
    plan = Plan(
        goal="Retrieve metrics",
        steps=[
            PlanStep(
                action=StepAction.QUERY,
                description="Retrieve metrics",
                expected_tool="run_sql",
                expected_output="dataset",
            )
        ],
    )
    state = {
        "plan": plan,
        "messages": [
            AIMessage(
                content="",
                tool_calls=[{"name": "run_sql", "args": {}, "id": "call-1", "type": "tool_call"}],
            ),
            ToolMessage(
                content='{"status":"success","tool":"run_sql","rows":[]}',
                name="run_sql",
                tool_call_id="call-1",
            ),
        ],
        "tool_results": [],
        "execution_records": [],
        "artifacts": [],
        "trace": [],
    }

    result = validator_node(state)

    assert result["plan"].current_step == 1
    assert result["plan"].steps[0].status == StepStatus.COMPLETED
    assert result["artifacts"][0].type == "DATASET"
    assert result["validation_complete"] is True


def test_tool_message_is_parsed_into_a_typed_sql_result():
    parsed = parse_tool_result(
        ToolMessage(
            content='{"status":"success","tool":"run_sql","query":"SELECT 1","row_count":1,"rows":[{"value":1}]}',
            name="run_sql",
            tool_call_id="call-1",
        )
    )

    assert parsed.typed_result.row_count == 1


def test_malformed_successful_tool_output_becomes_a_validation_error():
    parsed = parse_tool_result(
        ToolMessage(
            content=(
                '{"status":"success","tool":"generate_chart",'
                '"chart_path":"charts/example.png"}'
            ),
            name="generate_chart",
            tool_call_id="call-1",
        )
    )

    assert parsed.status == "error"
    assert parsed.typed_result is None
    assert "invalid result contract" in parsed.message
