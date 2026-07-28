import json
import sqlite3
from pathlib import Path

from .models import KnowledgeChunk, KnowledgeDocument
from .repository import KnowledgeRepository


class SQLiteKnowledgeRepository(KnowledgeRepository):
    def __init__(self, path: str | Path = "knowledge/knowledge.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute("CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS chunks (id TEXT PRIMARY KEY, document_id TEXT NOT NULL, payload TEXT NOT NULL)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id)")
    def _connect(self):
        con = sqlite3.connect(self.path); con.row_factory = sqlite3.Row; return con
    def store_document(self, document):
        with self._connect() as con: con.execute("INSERT INTO documents VALUES (?, ?)", (document.id, document.model_dump_json()))
        return document
    def store_chunks(self, chunks):
        with self._connect() as con:
            con.executemany("INSERT INTO chunks VALUES (?, ?, ?)", [(c.id, c.document_id, c.model_dump_json()) for c in chunks])
        return chunks
    def get_document(self, document_id):
        with self._connect() as con: row = con.execute("SELECT payload FROM documents WHERE id=?", (document_id,)).fetchone()
        return KnowledgeDocument.model_validate_json(row["payload"]) if row else None
    def chunks(self, *, document_id=None, tags=None):
        sql, values = "SELECT payload FROM chunks", []
        if document_id: sql += " WHERE document_id=?"; values.append(document_id)
        with self._connect() as con: rows = con.execute(sql, values).fetchall()
        chunks = [KnowledgeChunk.model_validate_json(row["payload"]) for row in rows]
        if tags: chunks = [c for c in chunks if set(tags).issubset(set(c.metadata.get("tags", "").split(",")))]
        return chunks
    def delete_document(self, document_id):
        with self._connect() as con:
            con.execute("DELETE FROM chunks WHERE document_id=?", (document_id,))
            return con.execute("DELETE FROM documents WHERE id=?", (document_id,)).rowcount > 0
