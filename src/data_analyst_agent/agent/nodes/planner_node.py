"""Planner workflow node."""

from ...services.planner import create_plan
from ..state import AgentState


def planner_node(state: AgentState) -> dict:
    print("➡️ Planner")
    question = state["messages"][-1].content
    plan = create_plan(question, state.get("memory", []), state.get("knowledge", []))

    trace = [*state.get("trace", []), "Context built", "📋 Planner generated execution plan", "➡️ Planner"]
    trace.extend(
        [
            "📋 Plan:",
            f"Goal: {plan.goal}",
            f"Current step: {plan.current_step}",
            "Steps:",
            *[
                f"  {index}. [{step.action}] {step.description}"
                for index, step in enumerate(plan.steps, start=1)
            ],
        ]
    )

    return {"plan": plan, "trace": trace}
