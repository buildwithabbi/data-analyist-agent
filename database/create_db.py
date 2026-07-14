import sqlite3
import random

from anyio import Path

DB_PATH = Path(__file__).parent / "sales.db"

print(f"Creating database at: {DB_PATH}")


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
DROP TABLE IF EXISTS sales
""")

cursor.execute("""
CREATE TABLE sales(
    customer_name TEXT,
    region TEXT,
    sales REAL
)
""")

customers = [
    "Alice", "Bob", "Charlie", "David", "Eva",
    "Frank", "Grace", "Helen", "Ivan", "Jack"
]

regions = [
    "North",
    "South",
    "East",
    "West"
]

rows = []

for _ in range(200):
    rows.append((
        random.choice(customers),
        random.choice(regions),
        random.randint(100, 5000)
    ))

cursor.executemany(
    "INSERT INTO sales VALUES (?, ?, ?)",
    rows
)
cursor.execute("PRAGMA table_info(sales)")

print(cursor.fetchall())
conn.commit()
conn.close()

print("Database created!")