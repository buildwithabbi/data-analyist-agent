"""Executor workflow node."""

import json

from langchain_core.messages import SystemMessage, ToolMessage

from ...core.llm import llm_with_tools, safe_invoke
from ...domain.models import ToolResult
from ...services.context import build_context
from ..state import AgentState


def _parse_tool_result(payload: dict, fallback_tool: str | None) -> ToolResult:
    """Convert a raw tool JSON response to the internal ToolResult shape."""
    result = payload.get("result")
    if result is None and payload.get("status") == "success":
        result = {
            key: value
            for key, value in payload.items()
            if key not in {"status", "tool", "message"}
        }

    return ToolResult(
        tool=payload.get("tool", fallback_tool or "unknown"),
        status=payload.get("status", "error"),
        result=result,
        message=payload.get("message"),
    )


def executor(state: AgentState) -> dict:
    print("➡️ Executor")

    trace = list(state.get("trace", []))

    if state.get("repair_attempts", 0):
        trace.append(
            f"🔁 Repair Attempt #{state['repair_attempts']}"
        )

    trace.append("🧠 Context built")

    tool_results = [*state.get("tool_results", [])]
    last_message = state["messages"][-1]

    if isinstance(last_message, ToolMessage):
        try:
            payload = json.loads(last_message.content)

            tool_results.append(
                _parse_tool_result(payload, last_message.name)
            )

            trace.append(
                f"📊 {payload['tool']} -> {payload['status']}"
            )

        except json.JSONDecodeError:
            tool_results.append(
                ToolResult(
                    tool=last_message.name,
                    status="error",
                    result=None,
                    message="Tool returned invalid JSON.",
                )
            )

            trace.append("⚠️ Failed to parse tool output.")

    context = build_context(
        {
            **state,
            "tool_results": tool_results,
        }
    )

    response = safe_invoke(
        llm_with_tools,
        [
            SystemMessage(content=context),
            *state["messages"],
        ],
    )

    print("\n===== TOOL CALLS =====")

    if response.tool_calls:
        for tool in response.tool_calls:
            print(f"Tool call -> {tool['name']}")

    return {
        "messages": [response],
        "trace": trace,
        "tool_results": tool_results,
    }