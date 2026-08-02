"""Command-line entry point for a one-off analysis request."""

import argparse

from langchain_core.messages import HumanMessage

from .agent.graph import graph
from .services.response_cache import response_cache
from .tools import active_dataset_id
from .utils.console import print_json
from .utils.logging import AgentLogger


def main() -> None:
    """Run an analysis query and print its answer and trace."""
    parser = argparse.ArgumentParser(description="Run a data-analysis request.")
    parser.add_argument("query", nargs="*", help="Natural-language analysis request.")
    parser.add_argument("--refresh", action="store_true", help="Bypass the exact-question response cache.")
    arguments = parser.parse_args()
    query = " ".join(arguments.query) or (
        "Trends over time month on month (sales, profit, quantity, discounts) "
        "and generate a suitable chart."
    )
    dataset_id = active_dataset_id()
    cached = None if arguments.refresh else response_cache.get(dataset_id, query)
    if cached:
        print("Using cached answer for this exact question and dataset. Use --refresh to rerun it.")
        print("\n========== ANSWER ==========")
        print(cached["answer"])
        return
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
    response_cache.put(
        dataset_id,
        query,
        {
            "answer": str(result["messages"][-1].content),
            "artifacts": [artifact.model_dump() for artifact in result.get("artifacts", [])],
            "trace": result.get("trace", []),
            "tool_results": [item.result or {"tool": item.tool, "message": item.message} for item in result.get("tool_results", [])],
        },
    )
