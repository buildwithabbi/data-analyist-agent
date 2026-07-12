from typing import List

def create_plan(user_query: str) -> List[str]:
    return [
        "Understand user request",
        "Generate SQL",
        "Execute SQL",
        "Analyze results",
        "Generate final response"
    ]