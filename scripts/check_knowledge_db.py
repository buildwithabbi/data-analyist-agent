"""Inspect a knowledge database without modifying it.

Examples:
    python scripts/check_knowledge_db.py
    python scripts/check_knowledge_db.py --limit 20
    python scripts/check_knowledge_db.py --db /path/to/knowledge.db
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_ROOT / "knowledge" / "knowledge.db"


def read_only_connection(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(f"Knowledge database not found: {path}")
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def inspect_database(path: Path, *, include_records: bool, limit: int) -> dict:
    with read_only_connection(path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        required = {"documents", "chunks"}
        missing = required - tables
        if missing:
            raise ValueError(f"Not a knowledge database; missing table(s): {', '.join(sorted(missing))}")

        documents = [json.loads(row["payload"]) for row in connection.execute("SELECT payload FROM documents")]
        chunk_count = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        result = {
            "database": str(path.resolve()),
            "documents": len(documents),
            "chunks": chunk_count,
            "document_types": dict(sorted(Counter(item.get("type", "unknown") for item in documents).items())),
            "statuses": dict(sorted(Counter(item.get("status", "unknown") for item in documents).items())),
        }
        if include_records:
            result["records"] = [
                {
                    "id": item.get("id"),
                    "type": item.get("type"),
                    "status": item.get("status"),
                    "title": item.get("metadata", {}).get("title"),
                    "source": item.get("metadata", {}).get("source"),
                    "tags": item.get("metadata", {}).get("tags", []),
                }
                for item in documents[:limit]
            ]
        return result


def print_report(report: dict) -> None:
    print(f"Knowledge database: {report['database']}")
    print(f"Documents: {report['documents']} | Chunks: {report['chunks']}")
    print(f"Types: {report['document_types'] or 'none'}")
    print(f"Statuses: {report['statuses'] or 'none'}")
    for index, record in enumerate(report.get("records", []), start=1):
        print(f"\n[{index}] {record['title'] or '(untitled)'}")
        print(f"    ID: {record['id']}")
        print(f"    Type: {record['type']} | Status: {record['status']}")
        print(f"    Source: {record['source']}")
        print(f"    Tags: {', '.join(record['tags']) or 'none'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a knowledge SQLite database.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DATABASE, help="Database path.")
    parser.add_argument("--summary", action="store_true", help="Show counts only, without document records.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a readable report.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum records to show (default: 10).")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be at least 1")
    try:
        report = inspect_database(args.db, include_records=not args.summary, limit=args.limit)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print_report(report)
    except (FileNotFoundError, ValueError, sqlite3.Error, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
