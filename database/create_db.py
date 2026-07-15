"""Create the SQLite sales database from the e-commerce CSV dataset.

Run from the repository root with:
    python database/create_db.py
"""

import csv
import json
import os
import sqlite3
from pathlib import Path

DATABASE_DIR = Path(__file__).resolve().parent
CSV_PATH = DATABASE_DIR / "E-commerce Dataset.csv"
DB_PATH = DATABASE_DIR / "sales.db"
TEMP_DB_PATH = DATABASE_DIR / "sales.tmp.db"

# The CSV headers are converted to stable, SQLite-friendly column names.
COLUMNS = (
    ("order_date", "TEXT"),
    ("time", "TEXT"),
    ("aging", "REAL"),
    ("customer_id", "INTEGER"),
    ("gender", "TEXT"),
    ("device_type", "TEXT"),
    ("customer_login_type", "TEXT"),
    ("product_category", "TEXT"),
    ("product", "TEXT"),
    ("sales", "REAL"),
    ("quantity", "REAL"),
    ("discount", "REAL"),
    ("profit", "REAL"),
    ("shipping_cost", "REAL"),
    ("order_priority", "TEXT"),
    ("payment_method", "TEXT"),
)


def create_database() -> int:
    """Import the CSV into ``sales.db`` and return the number of rows loaded."""
    if not CSV_PATH.is_file():
        raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")

    if TEMP_DB_PATH.exists():
        TEMP_DB_PATH.unlink()

    with CSV_PATH.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader, None)
        expected_header = [
            "Order_Date",
            "Time",
            "Aging",
            "Customer_Id",
            "Gender",
            "Device_Type",
            "Customer_Login_type",
            "Product_Category",
            "Product",
            "Sales",
            "Quantity",
            "Discount",
            "Profit",
            "Shipping_Cost",
            "Order_Priority",
            "Payment_method",
        ]
        if header != expected_header:
            raise ValueError(
                "The CSV header does not match the expected e-commerce schema."
            )

        conn = sqlite3.connect(TEMP_DB_PATH)
        try:
            definitions = ",\n    ".join(
                f"{column} {data_type}" for column, data_type in COLUMNS
            )
            conn.execute(f"CREATE TABLE sales (\n    {definitions}\n)")

            placeholders = ", ".join("?" for _ in COLUMNS)
            insert_sql = f"INSERT INTO sales VALUES ({placeholders})"
            conn.executemany(insert_sql, reader)
            conn.execute("CREATE INDEX idx_sales_order_date ON sales(order_date)")
            conn.execute(
                "CREATE INDEX idx_sales_product_category ON sales(product_category)"
            )
            conn.commit()

            row_count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        finally:
            conn.close()

    os.replace(TEMP_DB_PATH, DB_PATH)
    return row_count


if __name__ == "__main__":
    rows_loaded = create_database()
    print(
        json.dumps(
            {"database": str(DB_PATH), "records_loaded": rows_loaded},
            indent=2,
        )
    )
