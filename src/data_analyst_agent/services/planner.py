from langchain_core.messages import SystemMessage
import json
import re

SYSTEM_PROMPT = """
You are an AI Planner.

Your job is NOT to answer the question.

Create a short, executable plan for the data-analysis agent.

Return only valid JSON in this exact shape:
{
  "goal": "short description of the user's request",
  "steps": ["Step one", "Step two", "Step three"],
  "current_step": 0
}

Use only the tools and capabilities available to this agent. For a request that
needs a chart, use concise steps such as "Run SQL", "Generate Chart", and
"Summarize". Do not include setup, pandas, Plotly, or manual data-cleaning
steps.
"""

from ..core.llm import llm
from ..domain.models import Plan


def _plan_from_response(goal: str, response_text: str) -> Plan:
    """Turn a planner response into the structured Plan model."""
    cleaned_response = response_text.strip()
    if cleaned_response.startswith("```"):
        cleaned_response = re.sub(
            r"^```(?:json)?\s*|\s*```$", "", cleaned_response, flags=re.IGNORECASE
        ).strip()

    try:
        payload = json.loads(cleaned_response)
        if isinstance(payload, dict) and isinstance(payload.get("steps"), list):
            steps = [str(step).strip() for step in payload["steps"] if str(step).strip()]
            current_step = int(payload.get("current_step", 0))
            return Plan(
                goal=str(payload.get("goal") or goal).strip(),
                steps=steps,
                current_step=max(0, min(current_step, max(len(steps) - 1, 0))),
            )
    except (TypeError, ValueError, json.JSONDecodeError):
        pass

    # Backward-compatible fallback if the model does not return JSON.
    steps = []
    for line in response_text.splitlines():
        step = re.sub(r"^\s*(?:\d+[.)]|[-*])\s*", "", line).strip()
        if step:
            steps.append(step)

    # Preserve a useful plan even if the model does not follow the numbered
    # response format exactly.
    if not steps and response_text.strip():
        steps = [response_text.strip()]

    return Plan(goal=goal, steps=steps, current_step=0)


def create_plan(question: str) -> Plan:

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        ("human", question),
    ]

    response = llm.invoke(messages)

    return _plan_from_response(question, response.content)
