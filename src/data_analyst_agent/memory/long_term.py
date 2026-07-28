from __future__ import annotations

from datetime import datetime

from ..domain.models import MemoryItem
from .database import MemoryDatabase


class LongTermMemory:
    """
    Long-Term Memory backed by SQLite.

    This class exposes the same interface as ShortTermMemory while
    persisting memories across agent sessions.
    """

    def __init__(self) -> None:
        self._database = MemoryDatabase()

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def add(self, memory: MemoryItem) -> None:
        """
        Store a memory.
        """

        if not memory.content.strip():
            return

        with self._database.connection as conn:
            conn.execute(
                """
                INSERT INTO memories (
                    id,
                    content,
                    category,
                    importance,
                    timestamp
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    memory.id,
                    memory.content,
                    memory.category,
                    memory.importance,
                    memory.timestamp.isoformat(),
                ),
            )
            conn.commit()

    def add_unique(self, memory: MemoryItem) -> None:
        """
        Store a memory only if an equivalent memory
        does not already exist.
        """

        if not memory.content.strip():
            return

        with self._database.connection as conn:
            exists = conn.execute(
                """
                SELECT 1
                FROM memories
                WHERE category = ?
                  AND content = ?
                LIMIT 1
                """,
                (
                    memory.category,
                    memory.content,
                ),
            ).fetchone()

        if not exists:
            self.add(memory)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_all(self) -> list[MemoryItem]:
        """
        Return all long-term memories.
        """

        with self._database.connection as conn:
            rows = conn.execute(
                """
                SELECT
                    id,
                    content,
                    category,
                    importance,
                    timestamp
                FROM memories
                ORDER BY timestamp
                """
            ).fetchall()

        return [
            MemoryItem(
                id=row[0],
                content=row[1],
                category=row[2],
                importance=row[3],
                timestamp=datetime.fromisoformat(row[4]),
            )
            for row in rows
        ]

    def get_last(self) -> MemoryItem | None:
        """
        Return the most recently stored memory.
        """

        with self._database.connection as conn:
            row = conn.execute(
                """
                SELECT
                    id,
                    content,
                    category,
                    importance,
                    timestamp
                FROM memories
                ORDER BY timestamp DESC
                LIMIT 1
                """
            ).fetchone()

        if row is None:
            return None

        return MemoryItem(
            id=row[0],
            content=row[1],
            category=row[2],
            importance=row[3],
            timestamp=datetime.fromisoformat(row[4]),
        )

    def count(self) -> int:
        """
        Return the number of stored memories.
        """

        with self._database.connection as conn:
            (count,) = conn.execute(
                "SELECT COUNT(*) FROM memories"
            ).fetchone()

        return count

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, memory: MemoryItem) -> None:
        """
        Update an existing memory.
        """

        with self._database.connection as conn:
            cursor = conn.execute(
                """
                UPDATE memories
                SET
                    content = ?,
                    category = ?,
                    importance = ?,
                    timestamp = ?
                WHERE id = ?
                """,
                (
                    memory.content,
                    memory.category,
                    memory.importance,
                    memory.timestamp.isoformat(),
                    memory.id,
                ),
            )

            if cursor.rowcount == 0:
                conn.execute(
                    """
                    INSERT INTO memories (
                        id,
                        content,
                        category,
                        importance,
                        timestamp
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        memory.id,
                        memory.content,
                        memory.category,
                        memory.importance,
                        memory.timestamp.isoformat(),
                    ),
                )

            conn.commit()

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def remove(self, memory_id: str) -> None:
        """
        Remove a memory by its identifier.
        """

        with self._database.connection as conn:
            conn.execute(
                "DELETE FROM memories WHERE id = ?",
                (memory_id,),
            )
            conn.commit()

    def clear(self) -> None:
        """
        Remove all stored memories.
        """

        with self._database.connection as conn:
            conn.execute("DELETE FROM memories")
            conn.commit()