"""Command-line entry point for a one-off analysis request."""

from langchain_core.messages import HumanMessage

from .agent.graph import graph
from .utils.console import print_json
from .utils.logging import AgentLogger


def main() -> None:
    """Run the example analysis query and print its answer and trace."""
    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "Trends over time month on month (sales, profit, quantity, "
                        "discounts) and generate suiatable chart ."
                    )
                )
            ],
            "trace": [],
        },
        config={"recursion_limit": 100},
    )

    print_json("TOOL RESULTS", result.get("tool_results", []))

    logger = AgentLogger()
    for entry in result.get("trace", []):
        logger.log(entry)
    logger.print()

    print("\n========== ANSWER ==========")
    print(result["messages"][-1].content)
