import json

from data_analyst_agent.tools import run_sql, set_database_path
from data_analyst_agent.tools.analytics import DB_PATH


def test_run_sql_returns_sales_rows() -> None:
    result = json.loads(run_sql.invoke({"query": "SELECT * FROM sales LIMIT 1"}))

    assert result["status"] == "success"
    assert result["row_count"] == 1


def test_sql_authorizer_allows_keywords_in_literals_and_denies_writes() -> None:
    allowed = json.loads(run_sql.invoke({"query": "SELECT 'update' AS note"}))
    denied = json.loads(run_sql.invoke({"query": "WITH candidate AS (SELECT 1) DELETE FROM sales"}))

    assert allowed["status"] == "success"
    assert denied["status"] == "error"


def test_database_selection_is_context_scoped(tmp_path) -> None:
    database = tmp_path / "isolated.db"
    import sqlite3

    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE sales (value INTEGER)")
        connection.execute("INSERT INTO sales VALUES (42)")

    set_database_path(database)
    try:
        result = json.loads(run_sql.invoke({"query": "SELECT value FROM sales"}))
        assert result["rows"] == [{"value": 42}]
    finally:
        set_database_path(DB_PATH)
