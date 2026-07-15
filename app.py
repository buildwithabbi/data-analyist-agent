from langchain_core.messages import HumanMessage
from graph import graph
from console_output import print_json

result = graph.invoke(
    {
        "messages": [
            HumanMessage(content=" Trends over time (sales, profit, quantity, discounts) and line charts."),
        ],
        "trace": [],
    },
    config={"recursion_limit": 100},
)

print_json("TOOL RESULTS", result.get("tool_results", []))
print_json("AGENT TRACE", result.get("trace", []))
print("\n========== ANSWER ==========")
print(result["messages"][-1].content)
