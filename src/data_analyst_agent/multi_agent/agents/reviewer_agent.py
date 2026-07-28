from .base import SpecialistAgent
class ReviewerAgent(SpecialistAgent):
    name = "reviewer"
    def run(self, context):
        approved = bool(context.data.get("plan")) and (not context.data.get("knowledge") or all(hit.score > 0 for hit in context.data["knowledge"]))
        return {"review": {"approved": approved, "reason": "Plan and retrieved evidence validated." if approved else "Missing plan or invalid evidence."}}
