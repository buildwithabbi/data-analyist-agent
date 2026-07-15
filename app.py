from langchain_core.messages import HumanMessage
from graph import graph
from console_output import print_json
from logger import AgentLogger

result = graph.invoke(
    {
        "messages": [
            HumanMessage(content=" Trends over time month on month(sales, profit, quantity, discounts) and generate line chart in one picture."),
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
