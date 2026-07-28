from .agents.analysis_agent import AnalysisAgent
from .agents.planner_agent import PlannerAgent
from .agents.research_agent import ResearchAgent
from .agents.response_agent import ResponseAgent
from .agents.reviewer_agent import ReviewerAgent
from .communication.message import AgentMessage
from .context import SharedContext
from .message_bus import MessageBus
from .registry import AgentRegistry
class Orchestrator:
    def __init__(self, *, approval_required=False):
        self.approval_required, self.bus, self.registry = approval_required, MessageBus(), AgentRegistry()
        for agent in (ResearchAgent(), PlannerAgent(), AnalysisAgent(), ReviewerAgent(), ResponseAgent()): self.registry.register(agent.name, agent)
    def run(self, query, *, approved=True):
        context = SharedContext(query=query, approved=approved)
        for name in ("research", "planner", "analysis", "reviewer", "response"):
            if self.approval_required and name == "analysis" and not approved: return {"status": "awaiting_approval", "context": context}
            self.bus.publish(AgentMessage(event="AgentStarted", sender=name, payload={}, task_id=name))
            context.data.update(self.registry.get(name).run(context)); context.traces.append(name)
            self.bus.publish(AgentMessage(event="AgentFinished", sender=name, payload=context.data, task_id=name))
        return {"status": "completed", "context": context, "response": context.data["response"]}
