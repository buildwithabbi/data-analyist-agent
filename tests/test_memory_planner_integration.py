from data_analyst_agent.memory.models import MemoryMetadata, SemanticMemory
from data_analyst_agent.memory.scorer import MemoryScorer
from data_analyst_agent.services import planner


def test_planner_receives_retrieved_memory(monkeypatch):
    captured = {}

    class FakeLLM:
        def invoke(self, messages):
            captured["system"] = messages[0].content
            return type("Response", (), {"content": '{"goal":"test","steps":["Query sales"]}'})()

    memory = SemanticMemory(
        content="Monthly sales trends should group with strftime.",
        metadata=MemoryMetadata(),
        score=MemoryScorer().score(success=True, tool_count=1, has_summary=True, novel=True),
    )
    monkeypatch.setattr(planner, "llm", FakeLLM())

    result = planner.create_plan("Show monthly sales", [memory])

    assert result.goal == "test"
    assert "Monthly sales trends" in captured["system"]
