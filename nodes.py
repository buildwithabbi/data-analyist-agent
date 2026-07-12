from llm import llm
from tools import TOOLS
from planner import create_plan
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from context_builder import build_context



llm_with_tools = llm.bind_tools([*TOOLS])

from groq import BadRequestError

def chatbot(state):
    print("➡️ Chatbot")

    trace = state.get("trace", [])

    context = build_context(state)
    trace.append("🧠 Context built")

    messages = [
        SystemMessage(content=context),
        *state["messages"],
    ]

    try:
        response = llm_with_tools.invoke(messages)
    except BadRequestError as e:
        print(f"⚠️ Tool call generation failed: {e}")
        trace.append(f"⚠️ Malformed tool call, retrying: {e}")

        # Retry once — small models occasionally self-correct on a second pass
        try:
            response = llm_with_tools.invoke(messages)
        except BadRequestError as e2:
            print(f"❌ Retry also failed: {e2}")
            trace.append(f"❌ Tool call failed after retry: {e2}")
            # Fall back to a plain AIMessage so the graph doesn't crash
            response = AIMessage(
                content="Sorry, I had trouble formatting that request internally. Could you rephrase or simplify your question?"
            )

    return {
        "messages": [response],
        "trace": trace,
    }

def planner_node(state):
    print("➡️ Planner")
    question = state["messages"][-1].content

    plan = create_plan(question)

    trace = state.get("trace", [])

    trace.append("📋 Planner generated execution plan")

    print("\n===== PLAN =====")
    trace.append(f"📋 PLAN\n{plan}")

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