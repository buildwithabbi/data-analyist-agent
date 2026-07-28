"""
Reflection workflow node.
"""

from langchain_core.messages import ToolMessage

from data_analyst_agent.agent.state import AgentState
from data_analyst_agent.agent.tool_results import (
    execution_record_for_tool,
    parse_tool_result,
)
from data_analyst_agent.domain.models import Plan
from data_analyst_agent.domain.models import ToolResult
from data_analyst_agent.services.execution import current_step, validate_tool_result
from data_analyst_agent.services.repair import analyze_execution


def reflection_node(state: AgentState) -> dict:
    """
    Analyze the latest execution and produce a
    structured RepairDecision.

    Reflection does not repair anything.
    It only classifies execution.
    """

    print("➡️ Reflection")

    # Normal graph execution arrives from the dedicated validator node. Keep
    # the legacy fallback below for direct callers and older persisted states.
    if state.get("validation_complete"):
        return {
            "repair_decision": analyze_execution(state),
            "validation_complete": False,
        }

    tool_results = [*state.get("tool_results", [])]
    records = [*state.get("execution_records", [])]
    trace = [*state.get("trace", [])]
    plan = state.get("plan")
    latest_message = state.get("messages", [])[-1] if state.get("messages") else None

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
    elif isinstance(latest_message, ToolMessage):
        result = parse_tool_result(latest_message)
        step_contract = current_step(plan)
        contract_error = validate_tool_result(step_contract, result) if step_contract else "No executable plan step is available."
        if contract_error:
            result = ToolResult(
                tool=result.tool,
                status="error",
                result=result.result,
                message=contract_error,
            )
        tool_results.append(result)
        step_number = plan.current_step + 1 if plan else 0
        step = step_contract.description if step_contract else "Unplanned tool call"
        records.append(execution_record_for_tool(state["messages"], step_number, step, result))
        trace.append(f"📊 {result.tool} -> {result.status}")

        if result.status == "success" and plan and plan.current_step < len(plan.steps):
            plan = Plan(goal=plan.goal, steps=plan.steps, current_step=plan.current_step + 1)
            trace.append(f"✅ Completed step {step_number}: {step}")

    repair_decision = analyze_execution({**state, "tool_results": tool_results})

    return {
        "plan": plan,
        "tool_results": tool_results,
        "execution_records": records,
        "trace": trace,
        "repair_decision": repair_decision,
        "step_validation_error": "",
    }
