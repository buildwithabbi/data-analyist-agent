"""Command-line entry point for a one-off analysis request."""

import argparse

from langchain_core.messages import HumanMessage

from .agent.graph import graph
from .utils.console import print_json
from .utils.logging import AgentLogger


def main() -> None:
    """Run an analysis query and print its answer and trace."""
    parser = argparse.ArgumentParser(description="Run a data-analysis request.")
    parser.add_argument("query", nargs="*", help="Natural-language analysis request.")
    arguments = parser.parse_args()
    query = " ".join(arguments.query) or (
        "Trends over time month on month (sales, profit, quantity, discounts) "
        "and generate a suitable chart."
    )
    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=query
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
