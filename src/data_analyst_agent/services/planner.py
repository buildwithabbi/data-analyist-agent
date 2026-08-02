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
  "steps": [
    {
      "action": "QUERY",
      "description": "Retrieve the required monthly metrics in one SQL query",
      "expected_tool": "run_sql",
      "expected_output": "structured rows for analysis",
      "requires": [],
      "inputs": []
    },
    {
      "action": "GENERATE_CHART",
      "description": "Visualize the retrieved metrics",
      "expected_tool": "generate_chart",
      "expected_output": "multi_series_line_chart",
      "requires": ["run_sql"],
      "inputs": ["sales", "profit", "quantity", "discount"]
    },
    {
      "action": "SUMMARIZE",
      "description": "Summarize findings using the retrieved results",
      "expected_tool": null,
      "expected_output": "grounded natural-language summary",
      "requires": ["run_sql", "generate_chart"],
      "inputs": []
    }
  ],
  "current_step": 0
}

Use only the tools and capabilities available to this agent. For a request that
needs a chart, use concise logical tasks: retrieve the needed metrics, visualize
them, then summarize. Do not split SQL aggregation into a separate task when it
can be part of retrieval. Do not include setup, pandas, Plotly, or manual
data-cleaning steps.
"""

from ..core.llm import llm, safe_invoke
from ..domain.models import Plan, PlanStep


def _default_plan(goal: str) -> Plan:
    """Produce a valid minimal plan when a model returns empty/invalid JSON."""
    lowered = goal.lower()
    metrics = [metric for metric in ("sales", "profit", "quantity", "discount") if metric in lowered]
    wants_chart = any(word in lowered for word in ("chart", "plot", "visual", "graph"))
    steps: list[PlanStep] = [
        PlanStep(
            action="QUERY",
            description="Retrieve the requested metrics in one SQLite query",
            expected_tool="run_sql",
            expected_output="structured rows for analysis",
        )
    ]
    if wants_chart:
        steps.append(
            PlanStep(
                action="GENERATE_CHART",
                description="Visualize the retrieved metrics with an appropriate chart",
                expected_tool="generate_chart",
                expected_output="multi_series_line_chart" if len(metrics) > 1 else "chart",
                requires=["run_sql"],
                inputs=metrics,
            )
        )
    steps.append(
        PlanStep(
            action="SUMMARIZE",
            description="Summarize the findings using the retrieved evidence",
            expected_output="grounded natural-language summary",
            requires=["run_sql", *( ["generate_chart"] if wants_chart else [])],
        )
    )
    return Plan(goal=goal, steps=steps)


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
            steps = []
            for step in payload["steps"]:
                if isinstance(step, dict) and step.get("description"):
                    steps.append(PlanStep(**step))
                elif isinstance(step, str) and step.strip():
                    steps.append(step.strip())
            current_step = int(payload.get("current_step", 0))
            if steps:
                return Plan(
                    goal=str(payload.get("goal") or goal).strip(),
                    steps=steps,
                    current_step=max(0, min(current_step, max(len(steps) - 1, 0))),
                )
    except (TypeError, ValueError, json.JSONDecodeError):
        pass

    return _default_plan(goal)


def create_plan(question: str, memories: list | None = None, knowledge: list | None = None) -> Plan:

    memory_context = ""
    if memories:
        rendered = []
        for memory in memories:
            if hasattr(memory, "metadata"):
                rendered.append(
                    f"- [{memory.kind.value}, confidence={memory.score.confidence:.2f}] {memory.content}"
                )
            else:
                rendered.append(f"- {memory.content}")
        memory_context = (
            "\nRelevant past experience (use it as guidance, not as evidence for the answer):\n"
            + "\n".join(rendered)
        )
    if knowledge:
        memory_context += "\nRelevant external knowledge (cite sources; do not make unsupported claims):\n" + "\n".join(
            f"- [{item.citation}; confidence={item.score:.2f}] {item.chunk.text}" for item in knowledge
        )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT + memory_context),
        ("human", question),
    ]

    response = safe_invoke(llm, messages)
    content = response.content if isinstance(response.content, str) else ""
    return _plan_from_response(question, content)
