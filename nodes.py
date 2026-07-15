from langsmith import trace

from llm import llm, safe_invoke, llm_with_tools
from tools import TOOLS
from planner import create_plan
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from context_builder import build_context
import json
from  models import ToolResult

from groq import BadRequestError


from state import AgentState

MAX_RETRIES = 3


import json

from groq import BadRequestError
from langchain_core.messages import SystemMessage, ToolMessage

from context_builder import build_context
from llm import llm, safe_invoke
from state import AgentState
from models import ToolResult
from memory.short_term import get_memory
tool_results: list[ToolResult]


def _parse_tool_result(payload: dict, fallback_tool: str | None) -> ToolResult:
    """Convert a raw tool JSON response to the internal ToolResult shape."""
    result = payload.get("result")
    if result is None and payload.get("status") == "success":
        # Tools return their successful data at the top level (for example,
        # ``rows``/``row_count`` from run_sql and chart metadata from
        # generate_chart). Keep that data together for downstream consumers.
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

    trace = [
        *state.get("trace", []),
        "🧠 Context built",
    ]

    tool_results = [
        *state.get("tool_results", [])
    ]

    # ---------------------------------------------------------
    # Observe latest tool execution
    # ---------------------------------------------------------

    last_message = state["messages"][-1]

    if isinstance(last_message, ToolMessage):

        try:

            payload = json.loads(last_message.content)

            tool_results.append(_parse_tool_result(payload, last_message.name))

            trace.append(
                f"📊 {payload['tool']} -> {payload['status']}"
            )

        except json.JSONDecodeError:

            tool_results.append(
                ToolResult(
                    tool=last_message.name,
                    status="error",
                    result=None,
                    message="Tool returned invalid JSON."
                )
            )

            trace.append(
                "⚠️ Failed to parse tool output."
            )

    # ---------------------------------------------------------
    # Build context
    # ---------------------------------------------------------

    context = build_context({
        **state,
        "tool_results": tool_results,
    })

    messages = [
        SystemMessage(content=context),
        *state["messages"],
    ]

    # ---------------------------------------------------------
    # Invoke LLM
    # ---------------------------------------------------------

    response = safe_invoke(
        llm_with_tools,
        messages,
    )

    # ---------------------------------------------------------
    # Debug
    # ---------------------------------------------------------

    print("\n===== TOOL CALLS =====")

    if response.tool_calls:

        for tool in response.tool_calls:
            print(f"Tool call -> {tool['name']}")

    # ---------------------------------------------------------
    # Return updated state
    # ---------------------------------------------------------

    return {
        "messages": [response],
        "trace": trace,
        "tool_results": tool_results,
    }


def planner_node(state):
    print("➡️ Planner")
    question = state["messages"][-1].content

    plan = create_plan(question)

    trace = [
        *state.get("trace", []),
        "Context built",
    ]

    trace.append("📋 Planner generated execution plan")

    trace.append("➡️ Planner")
    trace.append(f"📋 Plan:\n{plan}")

    return {
        "plan": plan,
        "trace": trace,
    }







def reflection_node(state: AgentState):

    print("➡️ Reflection")

    tool_results = state.get("tool_results", [])

    if not tool_results:
        return {}

    latest = tool_results[-1]

    if latest.status == "success":
        return {
            "last_error": None
        }

    retry_count = state.get("retry_count", 0) + 1

    return {
        "retry_count": retry_count,
        "last_error": latest.message,
    }





def memory_node(state: AgentState):

    print("➡️ Memory")

    memory = get_memory()

    trace = [
        *state.get("trace", []),
        f"🧠 Loaded {len(memory)} memory items"
    ]

    return {
        "memory": memory,
        "trace": trace,
    }


from memory.short_term import add_memory


def memory_update_node(state: AgentState):

    print("➡️ Memory Update")

    tool_results = state.get("tool_results", [])

    if not tool_results:
        return {}

    latest = tool_results[-1]

    if latest.status != "success":
        return {}

    if latest.tool == "run_sql":

        row_count = latest.result.get("row_count", 0)

        add_memory(
            f"Executed SQL successfully and returned {row_count} rows."
        )

    elif latest.tool == "generate_chart":

        title = latest.result.get("title", "Chart")

        add_memory(
            f"Generated chart '{title}'."
        )

    return {}
