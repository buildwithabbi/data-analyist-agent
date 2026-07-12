from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from state import AgentState
from nodes import chatbot
from tools import run_sql
from router import route_tools

builder = StateGraph(AgentState)

builder.add_node("chatbot", chatbot)
builder.add_node("tool", ToolNode([run_sql]))

builder.add_edge(START, "chatbot")

builder.add_conditional_edges(
    "chatbot",
    route_tools,
    {
        "tool": "tool",
        "end": END,
    },
)

builder.add_edge("tool", "chatbot")

graph = builder.compile()