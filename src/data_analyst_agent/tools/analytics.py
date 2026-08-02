import os
import re
import sqlite3
import logging
from contextvars import ContextVar
from hashlib import sha256
from pathlib import Path
from typing import Literal
from uuid import uuid4

import pandas as pd
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict

from ..utils.console import pretty_json, print_json

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "database" / "sales.db"
_database_path: ContextVar[Path] = ContextVar("database_path", default=DB_PATH)
logger = logging.getLogger(__name__)

matplotlib_cache = PROJECT_ROOT / ".cache" / "matplotlib"
matplotlib_cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_cache))

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt


class ChartDataPoint(BaseModel):
    """A single, explicit chart point for reliable tool-call validation."""

    model_config = ConfigDict(extra="forbid")

    label: str
    value: float


class ChartSeries(BaseModel):
    """One labelled series in a multi-series chart."""

    name: str
    data: list[ChartDataPoint]


def set_database_path(path: str | Path | None = None) -> Path:
    """Select the SQLite dataset for the current execution context.

    A context variable keeps concurrent dashboard sessions from selecting one
    another's database while retaining the bundled database as the default.
    """
    selected = Path(path) if path else DB_PATH
    _database_path.set(selected)
    return selected


def _active_database_path() -> Path:
    return _database_path.get()


def active_dataset_id() -> str:
    """Return a content fingerprint used to isolate durable memory by dataset."""
    digest = sha256()
    with _active_database_path().open("rb") as database:
        for block in iter(lambda: database.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def get_schema_text():
    conn = sqlite3.connect(_active_database_path())
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(sales)")
    cols = cursor.fetchall()
    conn.close()
    return "Table `sales` columns: " + ", ".join(c[1] for c in cols)


_DENIED_SQLITE_ACTIONS = frozenset(
    getattr(sqlite3, name)
    for name in (
        "SQLITE_INSERT", "SQLITE_UPDATE", "SQLITE_DELETE", "SQLITE_CREATE_INDEX",
        "SQLITE_CREATE_TABLE", "SQLITE_CREATE_TEMP_INDEX", "SQLITE_CREATE_TEMP_TABLE",
        "SQLITE_CREATE_TEMP_TRIGGER", "SQLITE_CREATE_TEMP_VIEW", "SQLITE_CREATE_TRIGGER",
        "SQLITE_CREATE_VIEW", "SQLITE_CREATE_VTABLE", "SQLITE_DROP_INDEX",
        "SQLITE_DROP_TABLE", "SQLITE_DROP_TEMP_INDEX", "SQLITE_DROP_TEMP_TABLE",
        "SQLITE_DROP_TEMP_TRIGGER", "SQLITE_DROP_TEMP_VIEW", "SQLITE_DROP_TRIGGER",
        "SQLITE_DROP_VIEW", "SQLITE_DROP_VTABLE", "SQLITE_ALTER_TABLE", "SQLITE_ATTACH",
        "SQLITE_DETACH", "SQLITE_PRAGMA", "SQLITE_REINDEX", "SQLITE_ANALYZE",
        "SQLITE_TRANSACTION", "SQLITE_SAVEPOINT",
    )
    if hasattr(sqlite3, name)
)


def _read_only_authorizer(action: int, _arg1: str | None, _arg2: str | None, _database: str | None, _source: str | None) -> int:
    """Reject writes/admin operations regardless of SQL spelling or CTE shape."""
    return sqlite3.SQLITE_DENY if action in _DENIED_SQLITE_ACTIONS else sqlite3.SQLITE_OK


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

    # This is a common PostgreSQL/MySQL habit. Catch it before SQLite returns
    # the unhelpful "near FROM" syntax error so the repair loop gets an
    # actionable, dialect-specific correction.
    if re.search(r"\bEXTRACT\s*\(", query, flags=re.IGNORECASE):
        return pretty_json(
            {
                "status": "error",
                "tool": "run_sql",
                "query": query,
                "message": (
                    "SQLite does not support EXTRACT(...). For dates use "
                    "strftime('%Y', order_date), strftime('%m', order_date), "
                    "or strftime('%Y-%m', order_date)."
                ),
            }
        )

    # Only allow read-only queries
    if not (query_upper.startswith("SELECT") or query_upper.startswith("WITH")):
        return pretty_json(
            {
                "status": "error",
                "tool": "run_sql",
                "message": ("Only SELECT and WITH queries are allowed."),
            }
        )

    conn = None

    try:

        conn = sqlite3.connect(_active_database_path())
        conn.row_factory = sqlite3.Row
        conn.set_authorizer(_read_only_authorizer)

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
        logger.exception("Unexpected SQL tool failure")

        return pretty_json(
            {
                "status": "error",
                "tool": "run_sql",
                "query": query,
                "message": "Unexpected database execution error.",
                "exception": type(e).__name__,
            }
        )

    finally:
        if conn is not None:
            conn.close()


@tool
def generate_chart(
    chart_type: Literal["bar", "line", "pie", "scatter"],
    title: str,
    data: list[ChartDataPoint] | None = None,
    series: list[ChartSeries] | None = None,
) -> str:
    """
    Generate a chart from SQL query results.

    PURPOSE
    -------
    Use this tool to visualize tabular data returned by the `run_sql` tool.

    IMPORTANT
    ---------
    - Always call `run_sql` FIRST.
    - Pass a compact list of points, each containing only `label` and `value`.
    - Use `label` for the X-axis/category and `value` for the metric.

    Args:
        data:
            Array of chart points.

            Example:
            [
                {"label": "Alice", "value": 1200},
                {"label": "Bob", "value": 950},
                {"label": "Charlie", "value": 780}
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
        if series:
            if chart_type != "line":
                return pretty_json(
                    {
                        "status": "error",
                        "tool": "generate_chart",
                        "message": "Multi-series charts currently require chart_type 'line'.",
                    }
                )

            fig, ax = plt.subplots(figsize=(12, 7))
            for chart_series in series:
                rows = [point.model_dump() for point in chart_series.data]
                if not rows:
                    return pretty_json(
                        {"status": "error", "tool": "generate_chart", "message": "A chart series is empty."}
                    )
                df = pd.DataFrame(rows).dropna(subset=["label", "value"])
                ax.plot(df["label"], df["value"], marker="o", label=chart_series.name)

            ax.set_xlabel("label")
            ax.set_ylabel("value")
            ax.set_title(title)
            ax.legend()
            fig.autofmt_xdate()

            charts_dir = PROJECT_ROOT / "charts"
            charts_dir.mkdir(exist_ok=True)
            safe_title = re.sub(r"[^\w-]", "_", title).strip("_")
            chart_path = charts_dir / f"{safe_title or 'chart'}_{uuid4().hex}.png"
            fig.savefig(chart_path, dpi=300, bbox_inches="tight")
            return pretty_json(
                {
                    "status": "success",
                    "tool": "generate_chart",
                    "chart_path": str(chart_path.relative_to(PROJECT_ROOT)),
                    "chart_type": chart_type,
                    "title": title,
                    "series_count": len(series),
                    "series": [item.name for item in series],
                }
            )

        if data is None:
            return pretty_json(
                {"status": "error", "tool": "generate_chart", "message": "Provide data or series."}
            )

        rows = [point.model_dump() for point in data]

        if not rows:
            return pretty_json(
                {
                    "status": "error",
                    "tool": "generate_chart",
                    "message": "Input data is empty.",
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

        x_column = "label"
        y_column = "value"

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

        charts_dir = PROJECT_ROOT / "charts"
        charts_dir.mkdir(exist_ok=True)

        safe_title = re.sub(r"[^\w-]", "_", title).strip("_")

        chart_path = charts_dir / f"{safe_title or 'chart'}_{uuid4().hex}.png"

        fig.savefig(chart_path, dpi=300, bbox_inches="tight")

        return pretty_json(
            {
                "status": "success",
                "tool": "generate_chart",
                "chart_path": str(chart_path.relative_to(PROJECT_ROOT)),
                "chart_type": chart_type,
                "title": title,
                "series_count": 1,
            }
        )

    except Exception as e:
        logger.exception("Chart generation failed")
        return pretty_json(
            {
                "status": "error",
                "tool": "generate_chart",
                "message": "Chart generation failed.",
                "exception": type(e).__name__,
            }
        )

    finally:
        if fig is not None:
            plt.close(fig)


TOOLS = [
    run_sql,
    generate_chart,
]
