from langchain_core.messages import AIMessage, SystemMessage
from langchain_groq import ChatGroq
from groq import BadRequestError
from ..tools import TOOLS
from .config import GROQ_API_KEY
from ..utils.console import print_json


def _is_rate_limit_error(error: Exception) -> bool:
    message = str(error).lower()
    return "rate limit" in message or "rate-limit" in message

# Choose exactly one model by commenting/uncommenting a line below.
#MODEL_NAME = "llama-3.1-8b-instant"       # Fast, low-quota dashboard default
#MODEL_NAME = "openai/gpt-oss-120b"      # Strong reasoning; higher token usage
MODEL_NAME = "llama-3.3-70b-versatile"  # Higher-capacity general model
#MODEL_NAME = "qwen/qwen3-32b"           # Mid-tier reasoning model
#MODEL_NAME = "openai/gpt-oss-20b"       # Fast reasoning model
# Tool calls and short grounded summaries do not need a long completion.
MAX_TOKENS = 256
REQUEST_TIMEOUT_SECONDS = 45

llm = ChatGroq(
    model=MODEL_NAME,
    api_key=GROQ_API_KEY,
    temperature=0,
    max_tokens=MAX_TOKENS,
    timeout=REQUEST_TIMEOUT_SECONDS,
    max_retries=0,
)


def safe_invoke(model, messages):
    """
    Invoke an LLM safely.
    """

    try:
        return model.invoke(messages)

    except BadRequestError as e:
        print_json("LLM ERROR", {"type": "BadRequestError", "message": str(e)})

        if _is_rate_limit_error(e):
            return AIMessage(content="", tool_calls=[])

        # Retrying an invalid tool generation unchanged only reproduces the
        # provider error. Keep the selected tool/schema intact and make the
        # required JSON argument format explicit for the corrective attempt.
        corrective_messages = list(messages)
        for index, message in enumerate(corrective_messages):
            if isinstance(message, SystemMessage):
                corrective_messages[index] = SystemMessage(
                    content=(
                        f"{message.content}\n\n"
                        "Tool-call correction: call the selected function with a JSON "
                        "object matching its schema. For run_sql this must be exactly "
                        '{"query": "SELECT ..."}. Never place raw SQL directly inside '
                        "a function tag."
                    )
                )
                break

        try:
            return model.invoke(corrective_messages)
        except BadRequestError as retry_error:
            print_json(
                "LLM ERROR",
                {"type": "BadRequestError", "message": str(retry_error), "retry": 1},
            )
            # Some providers reject a forced tool call even after correction.
            # Return a safe empty message so the executor can mark the step as
            # needing repair instead of crashing the whole workflow.
            return AIMessage(content="", tool_calls=[])

    except Exception as e:
        print_json(
            "LLM ERROR",
            {"type": type(e).__name__, "message": str(e)},
        )
        return AIMessage(content="", tool_calls=[])


llm_with_tools = llm.bind_tools(TOOLS)
