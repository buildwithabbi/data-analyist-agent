from langchain_core.messages import HumanMessage
from graph import graph

result = graph.invoke(
    {
        "messages": [
            HumanMessage(
                content="Show top 5 customers by sales and generate a chart."
            )
        ],
        "trace": [],
    },
    config={
        "recursion_limit": 100
    }
)

print("\n===== AGENT TRACE =====")

for step in result["trace"]:
    print(step)


print("\n========== ANSWER ==========")
print(result["messages"][-1].content)