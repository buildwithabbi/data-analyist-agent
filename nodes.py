from langsmith import trace

from llm import llm, safe_invoke
from tools import TOOLS
from planner import create_plan
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from context_builder import build_context
import json
llm_with_tools = llm.bind_tools([*TOOLS])

from groq import BadRequestError


from state import AgentState


def executor(state: AgentState) -> dict:

    print("➡️ Executor")

    trace = [
        *state.get("trace", []),
        "🧠 Context built",
    ]
    tool_results = [*state.get("tool_results", [])]

    last_message = state["messages"][-1]

    last_message = state["messages"][-1]

    print(type(last_message))

    if isinstance(last_message, ToolMessage):
        print(last_message)
        print(vars(last_message))

    if isinstance(last_message, ToolMessage):

        

        payload = json.loads(last_message.content)

        tool_results.append(payload)

        trace.append(f"📊 Stored result from {last_message.name}")
    context = build_context(state)

    messages = [
        SystemMessage(content=context),
        *state["messages"],
    ]

    response = safe_invoke(
        llm_with_tools,
        messages,
    )

    print("\n===== TOOL CALLS =====")

    if response.tool_calls:
        for tool in response.tool_calls:
            print(f"Tool call: {tool['name']} ")

    return {"messages": [response], "trace": trace, "tool_results": tool_results}


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


def reflection_node(state):

    last_message = state["messages"][-1]

    if "ERROR:" in last_message.content:

        print("🔍 Reflection")

        print(last_message.content)

        return {
            "last_error": last_message.content,
            "retry_count": state.get("retry_count", 0) + 1,
        }

    return {}
