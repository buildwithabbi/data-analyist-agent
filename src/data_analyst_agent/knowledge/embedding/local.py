"""Small deterministic embedding for local development and tests."""
import hashlib
import re
from math import sqrt
from .provider import EmbeddingProvider

class HashEmbeddingProvider(EmbeddingProvider):
    dimensions = 128
    def embed(self, texts):
        vectors = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for token in re.findall(r"[a-z0-9_]+", text.lower()):
                vector[int(hashlib.sha256(token.encode()).hexdigest(), 16) % self.dimensions] += 1
            norm = sqrt(sum(v * v for v in vector)) or 1
            vectors.append([v / norm for v in vector])
        return vectors
