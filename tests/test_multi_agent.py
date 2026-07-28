from data_analyst_agent.multi_agent.orchestrator import Orchestrator
from data_analyst_agent.multi_agent.scheduler import Scheduler

def test_orchestrator_coordinates_specialists(monkeypatch):
    monkeypatch.setattr("data_analyst_agent.multi_agent.agents.research_agent.memory_manager.retrieve", lambda *args, **kwargs: [])
    monkeypatch.setattr("data_analyst_agent.multi_agent.agents.research_agent.knowledge_manager.retrieve", lambda *args, **kwargs: [])
    monkeypatch.setattr("data_analyst_agent.multi_agent.agents.planner_agent.create_plan", lambda *args: object())
    outcome = Orchestrator().run("Analyze sales")
    assert outcome["status"] == "completed" and outcome["context"].traces == ["research", "planner", "analysis", "reviewer", "response"]

def test_orchestrator_supports_approval_checkpoint():
    outcome = Orchestrator(approval_required=True).run("Analyze sales", approved=False)
    assert outcome["status"] == "awaiting_approval"

def test_scheduler_can_parallelize_independent_tasks():
    assert sorted(Scheduler().run([1, 2], lambda item: item * 2, parallel=True)) == [2, 4]
