from .base import SpecialistAgent
class ResponseAgent(SpecialistAgent):
    name = "response"
    def run(self, context):
        review = context.data["review"]
        return {"response": "Ready for execution." if review["approved"] else f"Review failed: {review['reason']}"}
