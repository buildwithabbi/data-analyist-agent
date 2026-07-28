"""Deterministic plan-step contracts and validation."""

from ..domain.models import Plan, PlanStep, ToolResult
from ..domain.enums import StepAction
from ..domain.contracts import contract_for


def current_step(plan: Plan | None) -> PlanStep | None:
    if plan is None or plan.current_step >= len(plan.steps):
        return None
    return plan.steps[plan.current_step]


def missing_dependencies(
    step: PlanStep,
    tool_results: list[ToolResult],
    plan: Plan | None = None,
) -> list[str]:
    """Return unmet tool and plan-step prerequisites for ``step``."""
    successful_tools = {result.tool for result in tool_results if result.status == "success"}
    missing = [tool for tool in step.requires if tool not in successful_tools]

    if plan is not None:
        completed_step_ids = {
            candidate.id for candidate in plan.steps if candidate.status.value == "COMPLETED"
        }
        missing.extend(
            f"step {dependency}"
            for dependency in step.dependencies
            if dependency not in completed_step_ids
        )

    return missing


def validate_tool_result(step: PlanStep, result: ToolResult) -> str | None:
    if step.expected_tool and result.tool != step.expected_tool:
        return f"Step requires {step.expected_tool}, but received {result.tool}."
    if result.status != "success":
        return result.message or f"{result.tool} did not complete successfully."
    contract = contract_for(result.tool)
    if contract and step.action not in contract.supported_actions:
        return f"Tool {result.tool} does not support {step.action.value} steps."
    if contract and result.typed_result is None:
        return f"Tool {result.tool} did not produce the required {contract.output_type}."
    if result.tool == "run_sql" and result.typed_result:
        if result.typed_result.row_count != len(result.typed_result.rows):
            return "SQL result row_count does not match the returned rows."
    if result.tool == "generate_chart" and result.typed_result:
        if result.typed_result.series_count != len(result.typed_result.series or ["default"]):
            return "Chart result series_count does not match the returned series."
    if step.expected_output == "multi_series_line_chart":
        expected_series = len(step.inputs)
        actual_series = (result.result or {}).get("series_count", 0)
        if actual_series < expected_series:
            return (
                f"Step requires {expected_series} chart series "
                f"({', '.join(step.inputs)}), but produced {actual_series}."
            )
    return None


def required_chart_metrics(plan: Plan | None, step: PlanStep) -> list[str]:
    """Return metrics the current query must expose for its next chart step."""
    if plan is None or step.action != StepAction.QUERY:
        return []
    try:
        index = plan.steps.index(step)
    except ValueError:
        return []
    for candidate in plan.steps[index + 1 :]:
        if candidate.action == StepAction.GENERATE_CHART and candidate.expected_output == "multi_series_line_chart":
            return candidate.inputs
    return []


def validate_downstream_chart_data(plan: Plan | None, step: PlanStep, result: ToolResult) -> str | None:
    """Ensure a completed query can satisfy the next multi-series chart contract."""
    metrics = required_chart_metrics(plan, step)
    if not metrics or result.status != "success":
        return None
    rows = (result.result or {}).get("rows", [])
    if not rows:
        return "Query returned no rows for the required multi-series chart."
    first_row = rows[0]
    missing = [
        metric for metric in metrics
        if not any(metric.lower() in column.lower() for column in first_row)
    ]
    if missing:
        return (
            "Query output cannot satisfy the next multi-series chart. Return a label "
            f"column and numeric aliases for: {', '.join(missing)}."
        )
    if not any(column in first_row for column in ("label", "month", "date", "order_date")):
        return "Query output for the next chart requires a label, month, date, or order_date column."
    return None
