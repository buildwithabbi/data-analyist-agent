import sqlite3

import pandas as pd

from data_analyst_agent.services.datasets import arrow_safe_preview, load_tabular_dataset


def test_csv_upload_creates_a_normalized_sales_table(tmp_path):
    database, rows, columns = load_tabular_dataset(
        b"Order Date,Total Sales\n2024-01-01,120\n2024-01-02,80\n",
        "monthly sales.csv",
        tmp_path / "uploaded.db",
    )

    with sqlite3.connect(database) as connection:
        count = connection.execute("SELECT COUNT(*) FROM sales").fetchone()[0]

    assert rows == count == 2
    assert columns == ["order_date", "total_sales"]


def test_preview_normalizes_mixed_numeric_object_columns():
    preview = arrow_safe_preview(pd.DataFrame({"aging": [12.0, "", 9.0], "name": ["A", None, "C"]}))

    assert str(preview["aging"].dtype) == "float64"
    assert preview["aging"].isna().sum() == 1
    assert str(preview["name"].dtype) == "string"
