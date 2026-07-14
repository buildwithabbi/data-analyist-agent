from langsmith import trace

from llm import llm, safe_invoke
from tools import TOOLS
from planner import create_plan
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from context_builder import build_context



llm_with_tools = llm.bind_tools([*TOOLS])

from groq import BadRequestError


from state import AgentState

def executor(state: AgentState) -> dict:

    print("➡️ Executor")

    trace = [
        *state.get("trace", []),
        "🧠 Context built",
    ]

    context = build_context(state)

    messages = [
        SystemMessage(content=context),
        *state["messages"],
    ]

    response = safe_invoke(
        llm_with_tools,
        messages,
    )

    return {
        "messages": [response],
        "trace": trace,
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





def reflection_node(state):

    last_message = state["messages"][-1]

    if "ERROR:" in last_message.content:

        print("🔍 Reflection")

        print(last_message.content)

        return {
            "last_error": last_message.content,
            "retry_count": state.get("retry_count", 0) + 1
        }

    return {}