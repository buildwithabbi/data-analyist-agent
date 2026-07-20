import json

from data_analyst_agent.tools import run_sql


def test_run_sql_returns_sales_rows() -> None:
    result = json.loads(run_sql.invoke({"query": "SELECT * FROM sales LIMIT 1"}))

    assert result["status"] == "success"
    assert result["row_count"] == 1


def test_run_sql_explains_unsupported_extract_syntax() -> None:
    result = json.loads(
        run_sql.invoke(
            {"query": "SELECT EXTRACT(YEAR FROM order_date) FROM sales"}
        )
    )

    assert result["status"] == "error"
    assert "does not support EXTRACT" in result["message"]
    assert "strftime" in result["message"]
