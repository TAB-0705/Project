"""Orchestration layer: ties chunking, embeddings, retrieval, and generation
into the two operations a RAG system exposes — ingest() and query().

This is the 'Retrieval-Augmented Generation' itself:
  query -> embed -> retrieve relevant chunks -> stuff them into the prompt ->
  let the SLM answer grounded in that retrieved context."""

from .ollama_client import embed, generate
from .chunking import chunk_text
from .vector_store import VectorStore
from .config import TOP_K


def build_prompt(context: str, question: str) -> str:
    return (
        "You are a helpful assistant. Answer the question using ONLY the "
        "context below. If the answer is not in the context, say you don't "
        "know — do not make anything up.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer:"
    )


class RAGPipeline:
    def __init__(self) -> None:
        self.store = VectorStore()

    def ingest(self, text: str) -> int:
        """Chunk a document, embed each chunk, store the vectors.
        Returns the number of chunks added."""
        chunks = chunk_text(text)
        embeddings = [embed(c) for c in chunks]
        self.store.add(chunks, embeddings)
        return len(chunks)

    def query(self, question: str) -> tuple[str, list[tuple[str, float]]]:
        """Retrieve relevant chunks and generate a grounded answer.
        Returns (answer, retrieved_chunks_with_scores)."""
        if self.store.is_empty():
            return "No documents have been ingested yet.", []

        question_vec = embed(question)
        hits = self.store.search(question_vec, k=TOP_K)
        context = "\n\n".join(chunk for chunk, _ in hits)
        answer = generate(build_prompt(context, question))
        return answer, hits
