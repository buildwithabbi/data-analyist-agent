from langchain_core.tools import tool
from console_output import pretty_json, print_json
import sqlite3
import json
import pandas as pd
import matplotlib

matplotlib.use(
    "Agg"
)  # MUST be before pyplot import, and before any other matplotlib import
import matplotlib.pyplot as plt
import os
from typing import Literal
import json
import os
import re
import traceback
import pandas as pd
from langchain_core.tools import tool
import sqlite3
from pathlib import Path
from langchain_core.tools import tool
from pathlib import Path
import json
import sqlite3
import traceback
from langchain_core.tools import tool

DB_PATH = Path(__file__).resolve().parent / "database" / "sales.db"


def get_schema_text():
    conn = sqlite3.connect(DB_PATH)
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
        "Why did the tomato turn red? Because it saw the salad dressing!",
    ]

    return random.choice(jokes)


@tool
def run_sql(query: str) -> str:
    """
    Execute a READ-ONLY SQLite query.

    PURPOSE
    -------
    Execute SQL against the sales database.

    IMPORTANT
    ---------
    - This tool only supports READ operations.
    - Generate SQLite-compatible SQL.
    - Always inspect the schema first if column names are unknown.
    - Use SELECT statements to retrieve data.
    - Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE,
      REPLACE, ATTACH, DETACH, VACUUM, PRAGMA or other modification statements.

    Args:
        query:
            A valid SQLite SELECT query.

            Example:
                SELECT customer_name, sales
                FROM sales
                ORDER BY sales DESC
                LIMIT 5;

    Returns:
        JSON string.

        Success:
        {
            "status":"success",
            "tool":"run_sql",
            "query":"SELECT ...",
            "row_count":5,
            "rows":[...]
        }

        Error:
        {
            "status":"error",
            "tool":"run_sql",
            "message":"..."
        }
    """

    query = query.strip()

    print_json("RUN SQL", {"query": query})

    query_upper = query.upper()

    # Only allow read-only queries
    if not (query_upper.startswith("SELECT") or query_upper.startswith("WITH")):
        return pretty_json(
            {
                "status": "error",
                "tool": "run_sql",
                "message": ("Only SELECT and WITH queries are allowed."),
            }
        )

    blocked_keywords = {
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "REPLACE",
        "ATTACH",
        "DETACH",
        "VACUUM",
        "PRAGMA",
    }

    for keyword in blocked_keywords:
        if keyword in query_upper:
            return pretty_json(
                {
                    "status": "error",
                    "tool": "run_sql",
                    "message": f"Forbidden SQL keyword detected: {keyword}",
                }
            )

    conn = None

    try:

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute(query)

        rows = [dict(row) for row in cursor.fetchall()]

        print_json("SQL RESULT", {"status": "success", "row_count": len(rows)})

        return pretty_json(
            {
                "status": "success",
                "tool": "run_sql",
                "query": query,
                "row_count": len(rows),
                "rows": rows,
            }
        )

    except sqlite3.Error as e:

        return pretty_json(
            {
                "status": "error",
                "tool": "run_sql",
                "query": query,
                "message": str(e),
                "exception": type(e).__name__,
            }
        )

    except Exception as e:

        return pretty_json(
            {
                "status": "error",
                "tool": "run_sql",
                "query": query,
                "message": str(e),
                "exception": type(e).__name__,
                "traceback": traceback.format_exc(),
            }
        )

    finally:
        if conn is not None:
            conn.close()


@tool
def get_schema() -> str:
    """
    Return the database schema.
    """
    print_json("GET SCHEMA", {"database": str(DB_PATH)})
    return get_schema_text()


@tool
def generate_chart(
    data: str,
    chart_type: Literal["bar", "line", "pie", "plt.scatter"],
    title: str,
) -> str:
    """
    Generate a chart from SQL query results.

    PURPOSE
    -------
    Use this tool to visualize tabular data returned by the `run_sql` tool.

    IMPORTANT
    ---------
    - Always call `run_sql` FIRST.
    - Pass the SQL output directly to this tool.
    - Do NOT rename column names.
    - Do NOT transform the JSON structure.
    - This tool automatically detects:
        * the first text column as the X-axis
        * the first numeric column as the Y-axis

    Args:
        data:
            JSON array returned by run_sql.

            Example:
            [
                {"customer_name": "Alice", "sales": 1200},
                {"customer_name": "Bob", "sales": 950},
                {"customer_name": "Charlie", "sales": 780}
            ]

        chart_type:
            Supported values:
            - "bar"     : compare categories
            - "line"    : show trends
            - "pie"     : show proportions
            - "scatter" : show relationships

        title:
            Human-readable chart title.

    Returns:
        JSON string.

        Success:
        {
            "status": "success",
            "tool": "generate_chart",
            "chart_path": "charts/top_customers.png",
            "chart_type": "bar",
            "title": "Top Customers"
        }

        Error:
        {
            "status": "error",
            "tool": "generate_chart",
            "message": "<error message>"
        }
    """

    fig = None

    try:
        rows = json.loads(data)

        if not isinstance(rows, list):
            return pretty_json(
                {
                    "status": "error",
                    "tool": "generate_chart",
                    "message": "Input data must be a JSON array.",
                }
            )

        if not rows:
            return pretty_json(
                {
                    "status": "error",
                    "tool": "generate_chart",
                    "message": "Input data is empty.",
                }
            )

        if not all(isinstance(row, dict) for row in rows):
            return pretty_json(
                {
                    "status": "error",
                    "tool": "generate_chart",
                    "message": "Each row must be a JSON object.",
                }
            )

        df = pd.DataFrame(rows)

        if df.empty:
            return pretty_json(
                {
                    "status": "error",
                    "tool": "generate_chart",
                    "message": "No rows available for plotting.",
                }
            )

        text_columns = df.select_dtypes(include=["object"]).columns.tolist()
        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()

        if not text_columns:
            return pretty_json(
                {
                    "status": "error",
                    "tool": "generate_chart",
                    "message": "No categorical column found.",
                }
            )

        if not numeric_columns:
            return pretty_json(
                {
                    "status": "error",
                    "tool": "generate_chart",
                    "message": "No numeric column found.",
                }
            )

        x_column = text_columns[0]
        y_column = numeric_columns[0]

        df = df.dropna(subset=[x_column, y_column])

        if df.empty:
            return pretty_json(
                {
                    "status": "error",
                    "tool": "generate_chart",
                    "message": "No valid rows after cleaning.",
                }
            )

        chart_type = chart_type.lower()

        valid_chart_types = {
            "bar",
            "line",
            "pie",
            "scatter",
        }

        if chart_type not in valid_chart_types:
            return pretty_json(
                {
                    "status": "error",
                    "tool": "generate_chart",
                    "message": f"Unsupported chart type '{chart_type}'.",
                }
            )

        # Sort only for comparison charts
        if chart_type == "bar":
            df = df.sort_values(y_column, ascending=False)

        fig, ax = plt.subplots(figsize=(10, 6))

        if chart_type == "bar":
            ax.bar(df[x_column], df[y_column])

        elif chart_type == "line":
            ax.plot(df[x_column], df[y_column], marker="o")

        elif chart_type == "pie":
            ax.pie(df[y_column], labels=df[x_column], autopct="%1.1f%%")

        elif chart_type == "scatter":
            ax.scatter(df[x_column], df[y_column])

        if chart_type != "pie":
            ax.set_xlabel(x_column)
            ax.set_ylabel(y_column)

        ax.set_title(title)

        os.makedirs("charts", exist_ok=True)

        safe_title = re.sub(r"[^\w-]", "_", title).strip("_")

        chart_path = os.path.join("charts", f"{safe_title}.png")

        fig.savefig(chart_path, dpi=300, bbox_inches="tight")

        return pretty_json(
            {
                "status": "success",
                "tool": "generate_chart",
                "chart_path": chart_path,
                "chart_type": chart_type,
                "title": title,
            }
        )

    except Exception as e:
        return pretty_json(
            {
                "status": "error",
                "tool": "generate_chart",
                "message": str(e),
                "exception": type(e).__name__,
                "traceback": traceback.format_exc(),
            }
        )

    finally:
        if fig is not None:
            plt.close(fig)


TOOLS = [
    # get_schema,
    run_sql,
    # calculator,
    # joke_generator
    generate_chart,
]
