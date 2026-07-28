from data_analyst_agent.knowledge.manager import KnowledgeManager
from data_analyst_agent.knowledge.sqlite_repository import SQLiteKnowledgeRepository

def test_hybrid_retrieval_returns_grounded_citation(tmp_path):
    manager = KnowledgeManager(SQLiteKnowledgeRepository(tmp_path / "knowledge.db"))
    document, chunks = manager.add_text("# Revenue Policy\n\nRevenue is recognised after delivery. Refunds reduce recognised revenue.", source="policy.md", tags=["finance"])
    hits = manager.retrieve("When is revenue recognised?", tags=["finance"])
    assert hits[0].chunk.document_id == document.id
    assert "policy.md" in hits[0].citation
    assert hits[0].score > 0

def test_knowledge_chunks_preserve_headings(tmp_path):
    manager = KnowledgeManager(SQLiteKnowledgeRepository(tmp_path / "knowledge.db"))
    _, chunks = manager.add_text("# Sales\n\nMonthly sales are measured by order date.")
    assert chunks[0].heading == "Sales"
