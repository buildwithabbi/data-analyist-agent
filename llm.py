from langchain_groq import ChatGroq
from config import GROQ_API_KEY

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    # model="llama-3.1-8b-instant",
    # model="qwen/qwen3-32b",
    api_key=GROQ_API_KEY,
    temperature=0.5,
)