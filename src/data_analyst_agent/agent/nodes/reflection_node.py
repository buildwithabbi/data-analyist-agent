"""
Reflection workflow node.
"""

from data_analyst_agent.agent.state import AgentState
from data_analyst_agent.services.repair import analyze_execution


def reflection_node(state: AgentState) -> dict:
    """
    Analyze the latest execution and produce a
    structured RepairDecision.

    Reflection does not repair anything.
    It only classifies execution.
    """

    print("➡️ Reflection")

    repair_decision = analyze_execution(state)

    return {
        "repair_decision": repair_decision
    }