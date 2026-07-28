"""SQLite implementation of the memory repository."""

import json
import sqlite3
from pathlib import Path

from .enums import MemoryKind, MemoryLifecycle
from .models import EpisodeMemory, Memory, SemanticMemory
from .repository import MemoryRepository


class SQLiteMemoryRepository(MemoryRepository):
    def __init__(self, database_path: str | Path = "memory/agent_memory.db") -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY, kind TEXT NOT NULL, lifecycle TEXT NOT NULL,
                    content_hash TEXT NOT NULL, metadata_json TEXT NOT NULL,
                    score_json TEXT NOT NULL, record_json TEXT NOT NULL
                )"""
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_memories_hash ON memories(content_hash)")

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _model(row: sqlite3.Row) -> Memory:
        payload = json.loads(row["record_json"])
        return EpisodeMemory.model_validate(payload) if row["kind"] == MemoryKind.EPISODE.value else SemanticMemory.model_validate(payload)

    def store(self, memory: Memory) -> Memory:
        payload = memory.model_dump(mode="json")
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?, ?)",
                (memory.id, memory.kind.value, memory.lifecycle.value, memory.content_hash,
                 json.dumps(payload["metadata"]), json.dumps(payload["score"]), json.dumps(payload)),
            )
        return memory

    def get(self, memory_id: str) -> Memory | None:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        return self._model(row) if row else None

    def search(self, *, kind=None, tags=None, dataset=None, tool_chain=None, lifecycle=MemoryLifecycle.ACTIVE) -> list[Memory]:
        clauses, values = ["lifecycle = ?"], [lifecycle.value]
        if kind:
            clauses.append("kind = ?")
            values.append(kind.value)
        with self._connection() as connection:
            rows = connection.execute(f"SELECT * FROM memories WHERE {' AND '.join(clauses)}", values).fetchall()
        memories = [self._model(row) for row in rows]
        if tags:
            required = set(tags)
            memories = [item for item in memories if required.issubset(set(item.metadata.tags))]
        if dataset:
            memories = [item for item in memories if item.metadata.dataset == dataset]
        if tool_chain:
            required = set(tool_chain)
            memories = [item for item in memories if required.issubset(set(item.metadata.tool_chain))]
        return memories

    def update(self, memory: Memory) -> Memory:
        payload = memory.model_dump(mode="json")
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE memories SET kind=?, lifecycle=?, content_hash=?, metadata_json=?, score_json=?, record_json=? WHERE id=?",
                (memory.kind.value, memory.lifecycle.value, memory.content_hash,
                 json.dumps(payload["metadata"]), json.dumps(payload["score"]), json.dumps(payload), memory.id),
            )
        if cursor.rowcount == 0:
            raise KeyError(f"Memory {memory.id} does not exist.")
        return memory

    def delete(self, memory_id: str) -> bool:
        with self._connection() as connection:
            return connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,)).rowcount > 0
