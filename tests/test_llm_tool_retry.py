from groq import BadRequestError
from langchain_core.messages import AIMessage, SystemMessage

from data_analyst_agent.core.llm import safe_invoke


class ToolUseFailure(BadRequestError):
    def __init__(self):
        Exception.__init__(self, "tool_use_failed")


def test_tool_use_retry_adds_json_argument_correction():
    calls = []

    class Model:
        def invoke(self, messages):
            calls.append(messages)
            if len(calls) == 1:
                raise ToolUseFailure()
            return "recovered"

    assert safe_invoke(Model(), [SystemMessage(content="Use the SQL tool.")]) == "recovered"
    assert "JSON object" in calls[1][0].content
    assert '"query"' in calls[1][0].content


def test_tool_use_failure_returns_empty_tool_response():
    class Model:
        def invoke(self, messages):
            raise ToolUseFailure()

    response = safe_invoke(Model(), [SystemMessage(content="Use the SQL tool.")])

    assert isinstance(response, AIMessage)
    assert response.tool_calls == []
