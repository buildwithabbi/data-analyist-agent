"""Utilities for turning LangChain tool messages into domain models."""

import json

from langchain_core.messages import AIMessage, ToolMessage
from pydantic import ValidationError

from ..domain.models import ChartResult, ExecutionRecord, SQLResult, ToolResult


def parse_tool_result(message: ToolMessage) -> ToolResult:
    """Convert a raw tool JSON response to the internal ToolResult shape."""
    try:
        payload = json.loads(message.content)
    except json.JSONDecodeError:
        return ToolResult(
            tool=message.name or "unknown",
            status="error",
            result=None,
            message="Tool returned invalid JSON.",
        )

    result = payload.get("result")
    if result is None and payload.get("status") == "success":
        result = {
            key: value
            for key, value in payload.items()
            if key not in {"status", "tool", "message"}
        }

    typed_result = None
    try:
        if payload.get("status") == "success" and payload.get("tool") == "run_sql":
            typed_result = SQLResult(
                query=payload.get("query", ""),
                row_count=payload.get("row_count", 0),
                rows=payload.get("rows", []),
            )
        elif payload.get("status") == "success" and payload.get("tool") == "generate_chart":
            typed_result = ChartResult(
                chart_path=payload["chart_path"],
                chart_type=payload["chart_type"],
                title=payload["title"],
                series_count=payload.get("series_count", 1),
                series=payload.get("series", []),
            )
    except (KeyError, ValidationError, TypeError) as error:
        # A tool declaring success without satisfying its result contract is a
        # validation failure, not an unhandled graph error. Reflection can
        # then route it through the normal repair policy.
        return ToolResult(
            tool=payload.get("tool", message.name or "unknown"),
            status="error",
            result=result,
            message=f"Tool returned an invalid result contract: {error}",
        )

    return ToolResult(
        tool=payload.get("tool", message.name or "unknown"),
        status=payload.get("status", "error"),
        result=result,
        message=payload.get("message"),
        typed_result=typed_result,
    )


def execution_record_for_tool(
    messages: list,
    step_number: int,
    step: str,
    result: ToolResult,
) -> ExecutionRecord:
    """Build an execution record, recovering the matching tool-call arguments."""
    tool_input = None
    tool_call_id = None
    latest = messages[-1] if messages else None
    if isinstance(latest, ToolMessage):
        tool_call_id = latest.tool_call_id

    for message in reversed(messages[:-1]):
        if not isinstance(message, AIMessage):
            continue
        for call in message.tool_calls:
            if call.get("id") == tool_call_id:
                tool_input = call.get("args")
                break
        if tool_input is not None:
            break

    return ExecutionRecord(
        step_number=step_number,
        step=step,
        tool=result.tool,
        tool_input=tool_input,
        output=result.result,
        success=result.status == "success",
    )
