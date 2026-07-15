from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from state import AgentState
from nodes import (
    planner_node,
    executor,
    reflection_node,
    memory_node,
    memory_update_node,
)

from tools import TOOLS
from router import route_tools
from reflection_router import route_reflection

builder = StateGraph(AgentState)

# -----------------------------
# Nodes
# -----------------------------

builder.add_node("planner", planner_node)

builder.add_node("executor", executor)

builder.add_node("tool", ToolNode(TOOLS))

builder.add_node("reflection", reflection_node)

builder.add_node("memory", memory_node)

builder.add_node("memory_update", memory_update_node)
# -----------------------------
# Start
# -----------------------------

builder.add_edge(
    START,
    "planner",
)

builder.add_edge(
    "planner",
    "executor",
)

# -----------------------------
# Executor
# -----------------------------

builder.add_conditional_edges(
    "executor",
    route_tools,
    {
        "tool": "tool",
        "end": END,
    },
)

# -----------------------------
# Tool
# -----------------------------

builder.add_edge(
    "tool",
    "reflection",
)

# -----------------------------
# Reflection
# -----------------------------

builder.add_conditional_edges(
    "reflection",
    route_reflection,
    {
        "executor": "executor",
        "memory_update": "memory_update",
        "end": END,
    },
)

builder.add_edge("memory_update", END)

graph = builder.compile(name="DataAnalystAgent")
