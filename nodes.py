from langsmith import trace

from llm import llm, safe_invoke, llm_with_tools
from tools import TOOLS
from planner import create_plan
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from context_builder import build_context
import json


from groq import BadRequestError


from state import AgentState

MAX_RETRIES = 3


import json

from groq import BadRequestError
from langchain_core.messages import SystemMessage, ToolMessage

from context_builder import build_context
from llm import llm, safe_invoke
from state import AgentState


def executor(state: AgentState) -> dict:
    print("➡️ Executor")

    trace = [
        *state.get("trace", []),
        "🧠 Context built",
    ]

    tool_results = [*state.get("tool_results", [])]

    # ---------------------------------------------------------
    # Observe latest tool execution
    # ---------------------------------------------------------

    last_message = state["messages"][-1]

    if isinstance(last_message, ToolMessage):

        try:
            payload = json.loads(last_message.content)

            tool_results.append(payload)

            trace.append(f"📊 {payload['tool']} -> {payload['status']}")

        except json.JSONDecodeError:

            trace.append("⚠️ Failed to parse tool output.")

            tool_results.append(
                {
                    "status": "error",
                    "tool": last_message.name,
                    "message": "Tool returned invalid JSON.",
                }
            )

    # ---------------------------------------------------------
    # Build context
    # ---------------------------------------------------------

    context = build_context(
        {
            **state,
            "tool_results": tool_results,
        }
    )

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

    # Success
    if latest.get("status") == "success":
        return {"last_error": None}

    # Failure
    retry_count = state.get("retry_count", 0)

    retry_count += 1

    if retry_count > MAX_RETRIES:

        return {
            "retry_count": retry_count,
            "last_error": latest.get("message"),
        }

    return {
        "retry_count": retry_count,
        "last_error": latest.get("message"),
    }
