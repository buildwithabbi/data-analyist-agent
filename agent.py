import os
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# 1. API Key Set Karein 
os.environ["GROQ_API_KEY"] = "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"

# 2. TOOL BANAYEIN
@tool
def get_word_length(word: str) -> int:
    """Returns the length of a word.""" 
    return len(word)

tools = [get_word_length]

# 3. BRAIN (LLM) INITIALIZE KAREIN
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

# 4. AGENT CREATE KAREIN
# Llama ko clean JSON structural calls ke liye strict prompt dena zaroori hai
strict_system_prompt = (
    "You are a helpful assistant. You have access to tools. "
    "When you decide to call a tool, you must generate a clean function call "
    "according to the expected tool schema without wrapping it in raw XML tags."
)

# ✅ state_modifier ko badal kar 'prompt' kar diya gaya hai
agent_app = create_react_agent(
    llm, 
    tools=tools,
    prompt=strict_system_prompt  
)

# 5. AGENT KO TASK DEIN Aur RUN KAREIN
print("Agent is thinking...\n")

result = agent_app.invoke({
    "messages": [("human", "What is the length of the word 'Supercalifragilisticexpialidocious'?")]
})

print("\nFINAL ANSWER:")
print(result['messages'][-1].content)