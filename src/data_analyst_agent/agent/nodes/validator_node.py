"""Deterministic validation of a completed executor step."""

from langchain_core.messages import ToolMessage

from ...domain.enums import StepStatus
from ...domain.models import Artifact, Plan, ToolResult
from ...services.execution import (
    current_step,
    missing_dependencies,
    validate_downstream_chart_data,
    validate_tool_result,
)
from ..state import AgentState
from ..tool_results import execution_record_for_tool, parse_tool_result


def _artifact_for(result: ToolResult, step_id: int) -> Artifact | None:
    if result.status != "success":
        return None
    artifact_type = {"run_sql": "DATASET", "generate_chart": "CHART"}.get(result.tool)
    if artifact_type is None:
        return None
    return Artifact(
        id=f"step_{step_id}_{artifact_type.lower()}",
        type=artifact_type,
        producer=result.tool,
        payload=result.result or {},
    )


def validator_node(state: AgentState) -> dict:
    """Validate tool output against the active plan-step contract."""
    tool_results = [*state.get("tool_results", [])]
    records = [*state.get("execution_records", [])]
    artifacts = [*state.get("artifacts", [])]
    trace = [*state.get("trace", [])]
    plan = state.get("plan")
    latest = state.get("messages", [])[-1] if state.get("messages") else None
    validation_error = state.get("step_validation_error")

    if validation_error:
        step = current_step(plan)
        result = ToolResult(
            tool=step.expected_tool if step and step.expected_tool else "executor",
            status="error",
            message=validation_error,
        )
        tool_results.append(result)
        trace.append(f"⚠️ Step validation failed: {validation_error}")
    elif isinstance(latest, ToolMessage):
        result = parse_tool_result(latest)
        step = current_step(plan)
        dependencies = missing_dependencies(step, tool_results, plan) if step else []
        error = (
            f"Step '{step.description}' requires successful output from: {', '.join(dependencies)}."
            if dependencies
            else validate_tool_result(step, result) if step else "No executable plan step is available."
        )
        if error is None and step:
            error = validate_downstream_chart_data(plan, step, result)
        if error:
            result = ToolResult(tool=result.tool, status="error", result=result.result, message=error)
        tool_results.append(result)
        step_number = step.id if step else 0
        records.append(execution_record_for_tool(state["messages"], step_number, step.description if step else "Unplanned tool call", result))
        trace.append(f"📊 {result.tool} -> {result.status}")
        if result.status == "success" and plan and step:
            step.status = StepStatus.COMPLETED
            artifacts.extend(item for item in [_artifact_for(result, step.id)] if item)
            plan = Plan(goal=plan.goal, steps=plan.steps, current_step=plan.current_step + 1)
            trace.append(f"✅ Completed step {step.id}: {step.description}")

    return {
        "plan": plan,
        "tool_results": tool_results,
        "execution_records": records,
        "artifacts": artifacts,
        "trace": trace,
        "step_validation_error": "",
        "validation_complete": True,
    }
