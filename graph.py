from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from state import AgentState
from nodes import planner_node, executor
from tools import TOOLS
from router import route_tools

builder = StateGraph(AgentState)

# Nodes
builder.add_node("planner", planner_node)
builder.add_node("executor", executor)
builder.add_node("tool", ToolNode(TOOLS))

# Start
builder.add_edge(START, "planner")

# Planner runs only once
builder.add_edge("planner", "executor")

# executor decides
builder.add_conditional_edges(
    "executor",
    route_tools,
    {
        "tool": "tool",
        "end": END,
    },
)

# Tool returns to executor
builder.add_edge("tool", "executor")

graph = builder.compile(name="DataAnalystAgent")
