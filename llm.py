from langchain_groq import ChatGroq
from groq import BadRequestError
from tools import TOOLS
from config import GROQ_API_KEY
from console_output import print_json

llm = ChatGroq(
    model=
    # ==========================================
    # 🌟 TOP-TIER REASONING & LARGE PRODUCTION MODELS
    
    # ==========================================
    "openai/gpt-oss-120b",  # Highest rated overall, heavy reasoning + built-in search/code execution
    #"llama-3.3-70b-versatile",       # Best balanced open-weight production model (high capacity, multi-tool use)
    #"deepseek-r1-distill-llama-70b", # Exceptional specialized model for advanced logic, math, and coding tasks
    # # ==========================================
    # # ⚡ AGENTIC & COMPOUND SYSTEMS
    # # ==========================================
    #"groq/compound",                 # Fully managed agentic system with native tool orchestration
    #"groq/compound-mini",            # Lightweight, ultra-fast agentic system for multi-turn task workflows
    # # ==========================================
    # # 🚀 NEXT-GEN PREVIEW & MID-TIER REASONING
    # # ==========================================
    # "qwen/qwen3.6-27b",              # Advanced reasoning mode, strong text/image handling
    # "deepseek-r1-distill-qwen-32b",  # Highly effective mid-size reasoning model
    # "qwen/qwen3-32b",                # Balanced mid-tier model with excellent parallel tool use support
    # "openai/gpt-oss-20b",            # Blazing fast (1000 tokens/sec) reasoning model
    # "meta-llama/llama-4-scout-17b-16e-instruct", # Preview next-gen architecture optimized for vision and tools
    # # ==========================================
    # # 🏃 LIGHTWEIGHT, FAST & UTILITY MODELS
    # # ==========================================
    # "llama-3.1-8b-instant",          # The go-to lightweight model for high-throughput, low-latency text tasks
    # "openai/gpt-oss-safeguard-20b",  # Specialized model strictly tuned for content moderation and safety
    # # ==========================================
    # # 🎙️ AUDIO SPEECH-TO-TEXT MODELS
    # # ==========================================
    #"whisper-large-v3",              # Gold standard high-fidelity audio transcription
    # "whisper-large-v3-turbo"         # Maximum speed optimized audio transcription,
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
        print_json("LLM ERROR", {"type": "BadRequestError", "message": str(e)})

        # Retry once
        try:
            return model.invoke(messages)
        except BadRequestError as retry_error:
            print_json(
                "LLM ERROR",
                {"type": "BadRequestError", "message": str(retry_error), "retry": 1},
            )
            raise

    except Exception as e:
        print_json(
            "LLM ERROR",
            {"type": type(e).__name__, "message": str(e)},
        )
        raise


llm_with_tools = llm.bind_tools(TOOLS)
