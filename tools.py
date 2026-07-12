from langchain_core.tools import tool
import sqlite3

@tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression.
    Example:
    25 * 12 + 10
    """
    try:
        return str(eval(expression))
    except Exception as e:
        return str(e)
    
@tool
def joke_generator() -> str:
    """
    Generate a random joke.
    """
    import random
# here can we create dynamic unique jokes using LLM or any other method?

    jokes = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "Why did the scarecrow win an award? Because he was outstanding in his field!",
        "Why did the bicycle fall over? Because it was two-tired!",
        "Why did the math book look sad? Because it had too many problems.",
        "Why did the tomato turn red? Because it saw the salad dressing!"
    ]

    return random.choice(jokes)

@tool
def run_sql(query: str) -> str:
    """
    Execute SQL against the sales database.
    """

    conn = sqlite3.connect("database/sales.db")

    cursor = conn.cursor()

    cursor.execute(query)

    rows = cursor.fetchall()

    conn.close()

    return str(rows)