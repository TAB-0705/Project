"""All tunable knobs live here so the rest of the code stays clean."""

# The SLM that generates answers. phi3 = Phi-3-mini (3.8B), a true small
# language model. For an even lighter footprint use "llama3.2" (3B).
GEN_MODEL = "phi3"

# A dedicated embedding model — small and fast, runs locally in Ollama.
EMBED_MODEL = "nomic-embed-text"

# Chunking: split documents into overlapping windows of words.
CHUNK_SIZE = 200      # words per chunk
CHUNK_OVERLAP = 40    # words shared between consecutive chunks

# Retrieval: how many chunks to feed the SLM as context.
TOP_K = 3
