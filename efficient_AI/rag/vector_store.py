"""A tiny in-memory vector store. Written by hand (rather than Chroma/FAISS)
so the retrieval mechanism is fully visible and explainable: store chunk
vectors, then rank by cosine similarity to the query vector.

To scale up later, this class can be reimplemented over Chroma/FAISS and the
pipeline won't change."""

import numpy as np


class VectorStore:
    def __init__(self) -> None:
        self._chunks: list[str] = []
        self._embeddings: np.ndarray | None = None

    def is_empty(self) -> bool:
        return self._embeddings is None

    def add(self, chunks: list[str], embeddings: list[list[float]]) -> None:
        arr = np.array(embeddings, dtype=float)
        self._chunks.extend(chunks)
        if self._embeddings is None:
            self._embeddings = arr
        else:
            self._embeddings = np.vstack([self._embeddings, arr])

    def search(self, query_embedding: list[float], k: int) -> list[tuple[str, float]]:
        """Return the k chunks most similar to the query, with scores."""
        if self._embeddings is None:
            return []
        q = np.array(query_embedding, dtype=float)

        # cosine similarity = (A . B) / (|A| |B|), computed for every chunk.
        dots = self._embeddings @ q
        norms = np.linalg.norm(self._embeddings, axis=1) * np.linalg.norm(q)
        sims = dots / (norms + 1e-10)

        top = np.argsort(-sims)[:k]
        return [(self._chunks[i], float(sims[i])) for i in top]
