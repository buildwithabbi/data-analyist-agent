import json

from data_analyst_agent.tools import run_sql
from data_analyst_agent.tools.analytics import calculator


def test_run_sql_returns_sales_rows() -> None:
    result = json.loads(run_sql.invoke({"query": "SELECT * FROM sales LIMIT 1"}))

    assert result["status"] == "success"
    assert result["row_count"] == 1


def test_calculator_allows_arithmetic_but_rejects_code_execution() -> None:
    assert calculator.invoke({"expression": "25 * (12 + 10)"}) == "550"
    assert "Invalid expression" in calculator.invoke({"expression": "__import__('os').system('id')"})
