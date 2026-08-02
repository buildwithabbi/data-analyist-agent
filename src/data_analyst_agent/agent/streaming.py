"""
Real-Time Event & Token Streaming Engine for LangGraph.
Uses graph.astream_events (v2) to yield real-time node transitions,
tool executions, and LLM token chunks as they are generated.
"""

import asyncio
from typing import AsyncGenerator, Dict, Any
from langchain_core.messages import HumanMessage
from .graph import graph


async def stream_agent_events(question: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Asynchronously stream step-by-step node execution events and LLM token chunks.
    Yields structured dictionary events:
    - {'type': 'node_start', 'node': node_name}
    - {'type': 'token', 'content': chunk_text}
    - {'type': 'tool_start', 'tool': tool_name}
    - {'type': 'tool_end', 'tool': tool_name}
    """
    inputs = {"messages": [HumanMessage(content=question)], "trace": []}
    config = {"recursion_limit": 100}

    target_nodes = {
        "memory_node",
        "planner_node",
        "executor_node",
        "validator_node",
        "reflection_node",
        "repair_node",
        "memory_update_node",
    }

    async for event in graph.astream_events(inputs, config=config, version="v2"):
        kind = event.get("event")
        name = event.get("name", "")

        if kind == "on_chain_start" and name in target_nodes:
            yield {"type": "node_start", "node": name}

        elif kind == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            if content:
                yield {"type": "token", "content": content}

        elif kind == "on_tool_start":
            yield {"type": "tool_start", "tool": name, "input": event.get("data", {}).get("input")}

        elif kind == "on_tool_end":
            yield {"type": "tool_end", "tool": name}

        elif kind == "on_chain_end" and name in target_nodes:
            yield {"type": "node_end", "node": name, "output": event.get("data", {}).get("output")}


def run_agent_streaming_sync(question: str):
    """Synchronous wrapper to run stream_agent_events in standard event loops."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        gen = stream_agent_events(question)
        while True:
            try:
                event = loop.run_until_complete(gen.__anext__())
                yield event
            except StopAsyncIteration:
                break
    finally:
        loop.close()
