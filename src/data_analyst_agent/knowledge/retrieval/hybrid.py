import re
from ..models import KnowledgeHit

def _keyword(query, text):
    query_tokens = set(re.findall(r"[a-z0-9_]+", query.lower())); text_tokens = set(re.findall(r"[a-z0-9_]+", text.lower()))
    return len(query_tokens & text_tokens) / len(query_tokens) if query_tokens else 0.0
def _dot(left, right): return sum(a*b for a, b in zip(left, right))

class HybridRetriever:
    def __init__(self, repository, embedding_provider): self.repository, self.embedding_provider = repository, embedding_provider
    def retrieve(self, query, *, limit=5, tags=None, document_id=None):
        query_embedding = self.embedding_provider.embed([query])[0]
        hits = []
        for chunk in self.repository.chunks(document_id=document_id, tags=tags):
            dense = _dot(query_embedding, chunk.embedding) if chunk.embedding else 0.0
            keyword = _keyword(query, chunk.text)
            hits.append(KnowledgeHit(chunk=chunk, dense_score=dense, keyword_score=keyword, score=0.6*dense + 0.4*keyword))
        return sorted(hits, key=lambda item: item.score, reverse=True)[:limit]
