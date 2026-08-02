"""Inspect a durable-memory database without modifying it.

Examples:
    python scripts/check_memory_db.py
    python scripts/check_memory_db.py --limit 20
    python scripts/check_memory_db.py --db /path/to/agent_memory.db
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_ROOT / "memory" / "agent_memory.db"


def read_only_connection(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(f"Memory database not found: {path}")
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def inspect_database(path: Path, *, include_records: bool, limit: int) -> dict:
    with read_only_connection(path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "memories" not in tables:
            raise ValueError("Not a memory database; missing table: memories")
        rows = connection.execute(
            "SELECT id, kind, lifecycle, metadata_json, score_json, record_json FROM memories ORDER BY rowid DESC"
        ).fetchall()
        result = {
            "database": str(path.resolve()),
            "memories": len(rows),
            "kinds": dict(sorted(Counter(row["kind"] for row in rows).items())),
            "lifecycles": dict(sorted(Counter(row["lifecycle"] for row in rows).items())),
        }
        if include_records:
            records = []
            for row in rows[:limit]:
                metadata = json.loads(row["metadata_json"])
                score = json.loads(row["score_json"])
                payload = json.loads(row["record_json"])
                records.append(
                    {
                        "id": row["id"],
                        "kind": row["kind"],
                        "lifecycle": row["lifecycle"],
                        "created_at": metadata.get("created_at"),
                        "dataset": metadata.get("dataset"),
                        "tags": metadata.get("tags", []),
                        "overall_score": score.get("overall_score"),
                        "content": payload.get("content", "")[:200],
                    }
                )
            result["records"] = records
        return result


def print_report(report: dict) -> None:
    print(f"Memory database: {report['database']}")
    print(f"Memories: {report['memories']}")
    print(f"Kinds: {report['kinds'] or 'none'}")
    print(f"Lifecycles: {report['lifecycles'] or 'none'}")
    for index, record in enumerate(report.get("records", []), start=1):
        print(f"\n[{index}] {record['kind']} ({record['lifecycle']})")
        print(f"    ID: {record['id']}")
        print(f"    Created: {record['created_at'] or 'unknown'}")
        print(f"    Dataset: {record['dataset'] or 'none'}")
        print(f"    Tags: {', '.join(record['tags']) or 'none'}")
        print(f"    Score: {record['overall_score'] if record['overall_score'] is not None else 'unknown'}")
        print(f"    Content: {record['content'] or '(empty)'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a durable-memory SQLite database.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DATABASE, help="Database path.")
    parser.add_argument("--summary", action="store_true", help="Show counts only, without memory records.")
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
