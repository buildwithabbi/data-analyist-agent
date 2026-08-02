"""Unit tests for HyDE Retriever and Parent-Child Chunker."""

from data_analyst_agent.knowledge.manager import knowledge_manager
from data_analyst_agent.knowledge.retrieval.hyde import HyDEGenerator, HyDERetriever, ParentChildChunker


def test_hyde_generator():
    hypo = HyDEGenerator.generate_hypothetical_document("sales by region")
    assert "sales by region" in hypo
    assert "dataset schema" in hypo


def test_parent_child_chunker():
    text = " ".join([f"word_{i}" for i in range(500)])
    parents, children = ParentChildChunker.create_parent_child_chunks(text, parent_size=200, child_size=50)

    assert len(parents) > 0
    assert len(children) > 0
    assert "parent_id" in children[0]


def test_hyde_retriever_execution():
    hyde_retriever = HyDERetriever(knowledge_manager.retriever, knowledge_manager.embedding_provider)
    hits = hyde_retriever.retrieve("monthly profit trends", limit=3)
    assert isinstance(hits, list)
