"""Dataset-scoped cache for completed, validated analysis responses."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CACHE_VERSION = "1"
DEFAULT_CACHE_PATH = Path(__file__).resolve().parents[3] / "memory" / "response_cache.db"


def normalize_question(question: str) -> str:
    """Normalize harmless formatting differences without changing meaning."""
    return re.sub(r"\s+", " ", question.strip().casefold())


class ResponseCache:
    def __init__(self, path: str | Path = DEFAULT_CACHE_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS response_cache (
                    cache_key TEXT PRIMARY KEY,
                    dataset_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )"""
            )

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    @staticmethod
    def _key(dataset_id: str, question: str) -> str:
        value = f"{CACHE_VERSION}:{dataset_id}:{normalize_question(question)}"
        return hashlib.sha256(value.encode()).hexdigest()

    def get(self, dataset_id: str, question: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT payload_json FROM response_cache WHERE cache_key = ?",
                (self._key(dataset_id, question),),
            ).fetchone()
        return json.loads(row["payload_json"]) if row else None

    def put(self, dataset_id: str, question: str, payload: dict[str, Any]) -> None:
        with self._connection() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO response_cache
                (cache_key, dataset_id, question, payload_json, created_at) VALUES (?, ?, ?, ?, ?)""",
                (
                    self._key(dataset_id, question),
                    dataset_id,
                    normalize_question(question),
                    json.dumps(payload, default=str),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )


response_cache = ResponseCache()
