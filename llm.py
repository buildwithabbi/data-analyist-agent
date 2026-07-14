from langchain_groq import ChatGroq
from groq import BadRequestError

from config import GROQ_API_KEY

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.5,
    max_tokens=2048,
)


def safe_invoke(model, messages):
    """
    Invoke an LLM safely.
    """

    try:
        return model.invoke(messages)

    except BadRequestError as e:
        print(f"⚠️ Tool call generation failed: {e}")

        # Retry once
        try:
            return model.invoke(messages)
        except BadRequestError as retry_error:
            print(f"❌ Retry failed: {retry_error}")
            raise

    except Exception as e:
        print(f"❌ Unexpected LLM error: {e}")
        raise