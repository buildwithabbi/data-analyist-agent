from langchain_core.messages import HumanMessage
from graph import graph
from pprint import pprint

result = graph.invoke(
    {
        "messages": [
            HumanMessage(content="Show top 5 customers by sales and generate a chart.")
        ],
        "trace": [],
    },
    config={"recursion_limit": 100},
)

print("\n===== TOOL RESULTS =====")

for item in result.get("tool_results", []):
    pprint(item)

print("\n===== AGENT TRACE =====")

for step in result["trace"]:
    pprint(step)


print("\n========== ANSWER ==========")
print(result["messages"][-1].content)
