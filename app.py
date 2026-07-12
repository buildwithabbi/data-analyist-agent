from langchain_core.messages import HumanMessage
from graph import graph

result = graph.invoke(
    {
        "messages": [
            HumanMessage(
                content="What is the sum of 25 and 12?"
            )
        ],
        "trace": []
    }
)

print("\n===== AGENT TRACE =====")

for step in result["trace"]:
    print(step)

print("\n===== FINAL ANSWER =====")

print(result["messages"][-1].content)