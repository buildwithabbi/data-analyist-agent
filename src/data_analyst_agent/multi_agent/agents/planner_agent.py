from .base import SpecialistAgent
from ...services.planner import create_plan
class PlannerAgent(SpecialistAgent):
    name = "planner"
    def run(self, context): return {"plan": create_plan(context.query, context.data.get("memories", []), context.data.get("knowledge", []))}
