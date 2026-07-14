from langchain_core.messages import SystemMessage

SYSTEM_PROMPT = """
You are an AI Planner.

Your job is NOT to answer the question.

Break the user's request into small executable steps.

Return only numbered steps.
"""

from typing import List

from llm import llm


def create_plan(question: str):

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        ("human", question),
    ]

    response = llm.invoke(messages)

    return response.content
