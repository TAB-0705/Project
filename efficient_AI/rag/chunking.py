"""Splitting documents into chunks is the first half of RAG. Overlap keeps
sentences that straddle a boundary from being cut off from their context."""

from .config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str,
               chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    if not words:
        return []

    step = max(1, chunk_size - overlap)
    chunks = []
    for start in range(0, len(words), step):
        window = words[start:start + chunk_size]
        if window:
            chunks.append(" ".join(window))
        if start + chunk_size >= len(words):
            break
    return chunks
