"""A replaceable reranker; lexical overlap is a safe default without ML downloads."""
from .hybrid import _keyword
class Reranker:
    def rerank(self, query, hits, limit=5):
        return sorted(hits, key=lambda hit: 0.8*hit.score + 0.2*_keyword(query, hit.chunk.text), reverse=True)[:limit]
