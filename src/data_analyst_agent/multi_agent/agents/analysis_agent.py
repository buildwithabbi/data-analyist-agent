from .base import SpecialistAgent
class AnalysisAgent(SpecialistAgent):
    name = "analysis"
    def run(self, context): return {"analysis": "Execution plan and evidence are ready for validated response."}
