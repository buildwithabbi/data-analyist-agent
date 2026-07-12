from llm import llm
from tools import *
from planner import create_plan

llm_with_tools = llm.bind_tools([run_sql, calculator, joke_generator])



def planner_node(state):

    question = state["messages"][-1].content

    plan = create_plan(question)

    trace = state.get("trace", [])
    trace.append("📋 Plan created")

    return {
        "plan": plan,
        "trace": trace
    }


def chatbot(state):
    trace = state.get("trace", [])

    trace.append("🧠 Chatbot node started")

    response = llm_with_tools.invoke(state["messages"])

    if response.tool_calls:
        tool_name = response.tool_calls[0]["name"]
        trace.append(f"🔧 Tool requested: {tool_name}")
    else:
        trace.append("💬 Generated final answer")

    return {
        "messages": [response],
        "trace": trace,
    }