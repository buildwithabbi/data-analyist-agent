from .base import SpecialistAgent
from ...memory.manager import memory_manager
from ...knowledge.manager import knowledge_manager
class ResearchAgent(SpecialistAgent):
    name = "research"
    def run(self, context):
        return {"memories": memory_manager.retrieve(context.query, limit=3), "knowledge": knowledge_manager.retrieve(context.query, limit=5)}
