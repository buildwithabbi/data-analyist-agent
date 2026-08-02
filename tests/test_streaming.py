"""Unit tests for Real-Time Event & Token Streaming Engine."""

from data_analyst_agent.agent.streaming import run_agent_streaming_sync


def test_agent_event_streaming():
    events = []
    token_chunks = []

    for event in run_agent_streaming_sync("Calculate total sales count"):
        events.append(event)
        if event["type"] == "token":
            token_chunks.append(event["content"])

    assert len(events) > 0
    assert len(token_chunks) > 0
    assert any("token" == e["type"] for e in events)
