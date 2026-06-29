"""The ONLY module that talks to Ollama. Everything else depends on these
two functions, not on Ollama's API — so the SLM/embedding backend could be
swapped without touching the pipeline."""

import ollama
from .config import GEN_MODEL, EMBED_MODEL


def embed(text: str) -> list[float]:
    """Turn text into a vector using the local embedding model."""
    response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return response["embedding"]


def generate(prompt: str) -> str:
    """Generate an answer from the local SLM."""
    response = ollama.generate(model=GEN_MODEL, prompt=prompt)
    return response["response"].strip()
