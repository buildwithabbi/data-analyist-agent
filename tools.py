from langchain_core.tools import tool
import sqlite3
import json
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # MUST be before pyplot import, and before any other matplotlib import
import matplotlib.pyplot as plt
import os

import sqlite3
from pathlib import Path
from langchain_core.tools import tool

DB_PATH = Path(__file__).resolve().parent / "database" / "sales.db"


def get_schema_text():
    conn = sqlite3.connect("database/sales.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(sales)")
    cols = cursor.fetchall()
    conn.close()
    return "Table `sales` columns: " + ", ".join(c[1] for c in cols)

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
    Execute a SQLite query against the sales database.

    Only call this tool after generating a valid SQLite query.
    """
    print("➡️ run_sql")

    conn = sqlite3.connect("database/sales.db")
    cursor = conn.cursor()

    try:
        cursor.execute(query)
    except Exception as e:
        print("❌ SQL ERROR:", e)
        conn.close()
        return f"ERROR: {e}"

    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()

    # Convert rows into list of dicts, keyed by column name
    result = [dict(zip(columns, row)) for row in rows]

    print("✅ SQL executed successfully")
    print("Rows fetched:", len(result))

    # Return valid JSON, not a Python str(list)
    return json.dumps(result)

@tool
def get_schema() -> str:
    """
    Return the database schema.
    """
    print("➡️ get_schema")
    return get_schema_text()
()





@tool
def generate_chart(data: str, chart_type: str, title: str, x_column: str, y_column: str) -> str:
    """
    Generate a chart. `data` must be a JSON string like
    '[{"x_column": "Alice", "y_column": 100}, ...]'.
    """
    try:
        rows = json.loads(data)
        df = pd.DataFrame(rows) if isinstance(rows[0], dict) else pd.DataFrame(rows, columns=[x_column, y_column])

        # Drop any stray header-like row where y is non-numeric (e.g. {"x_column": "customer_name", "y_column": "sales"})
        df[y_column] = pd.to_numeric(df[y_column], errors="coerce")
        df = df.dropna(subset=[x_column, y_column])

        # Aggregate duplicate x-labels instead of letting bars silently overlap
        df = df.groupby(x_column, as_index=False)[y_column].sum()
        df = df.sort_values(y_column, ascending=False)

        if df.empty:
            return "ERROR: no valid data rows after cleaning"

        fig, ax = plt.subplots()
        if chart_type == "bar":
            ax.bar(df[x_column], df[y_column])
        elif chart_type == "line":
            ax.plot(df[x_column], df[y_column])
        elif chart_type == "pie":
            ax.pie(df[y_column], labels=df[x_column], autopct="%1.1f%%")
        else:
            ax.scatter(df[x_column], df[y_column])

        ax.set_title(title)
        os.makedirs("/home/abhishek/agentic-ai/charts", exist_ok=True)
        path = f"/home/abhishek/agentic-ai/charts/{title.replace(' ', '_')}.png"
        fig.savefig(path)
        # plt.close(fig)
        return path
    except Exception as e:
        plt.close("all")
        return f"ERROR: {e}"


TOOLS = [
    # get_schema,
    run_sql,
    # calculator,
    # joke_generator
    generate_chart
]