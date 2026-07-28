from __future__ import annotations

import sqlite3
from pathlib import Path

DATABASE_NAME = "agent_memory.db"


class MemoryDatabase:
    """
    SQLite database used for Long-Term Memory.
    """

    def __init__(self, database_path: str | None = None) -> None:
        self._database = Path(database_path or DATABASE_NAME)
        self._initialize()

    @property
    def connection(self) -> sqlite3.Connection:
        """
        Return a new SQLite connection.

        A fresh connection is opened for every operation.
        """

        return sqlite3.connect(self._database)

    def _initialize(self) -> None:
        """
        Create required database objects.
        """

        with self.connection as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    importance REAL NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )
            conn.commit()