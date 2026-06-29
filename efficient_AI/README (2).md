# Fully Local RAG with an SLM + Ollama

A Retrieval-Augmented Generation pipeline that runs entirely on your machine —
no API keys, no quota, no cloud. A small language model (Phi-3) generates
answers grounded in documents you ingest, with retrieval done by a local
embedding model. All inference happens inside **Ollama**.

## Architecture (clean layering)

```
app.py                  Streamlit UI
rag/
  config.py             model names + chunk/retrieval params
  chunking.py           split documents into overlapping chunks
  ollama_client.py      the ONLY file that talks to Ollama (embed + generate)
  vector_store.py       in-memory cosine-similarity search (hand-written)
  pipeline.py           orchestrates ingest() and query()
```

Each module does one job; the pipeline depends on the modules, not the other
way around. The Ollama backend and the vector store are both isolated, so
either could be swapped without touching the rest.

## Setup

### 1. Install Ollama (independent of Python)
Download from https://ollama.com/download and install. It runs as a local
server on `http://localhost:11434`.

### 2. Pull the models (one-time, ~2.5GB total)
```powershell
ollama pull phi3
ollama pull nomic-embed-text
```
Confirm Ollama is serving: `ollama list` should show both models.

### 3. Python deps
These are pure-wheel packages and should install on Python 3.14. If you hit
any wheel issue, use a Python 3.12 venv — but note Ollama itself does NOT
depend on your Python version.
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. Run
```powershell
python -m streamlit run app.py
```

## Demo flow

1. Upload `sample_docs/indus_valley.txt` (or paste any text) → **Ingest**.
2. Ask: *"How many people lived in Mohenjo-daro?"* → the answer (~40,000)
   comes from the retrieved chunk, shown in the expander.
3. Ask something NOT in the document → the model should say it doesn't know,
   proving the answer is grounded in retrieval, not made up.

## Why this matters (talking points)

- **SLM, low overhead:** Phi-3-mini (3.8B) runs comfortably on a laptop. Swap
  to `llama3.2` (3B) in `config.py` for even less.
- **Why RAG instead of just asking the model:** the SLM answers from YOUR
  documents, with citations (the retrieved chunks), and won't hallucinate
  facts that aren't in the context.
