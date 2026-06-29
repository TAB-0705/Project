# Visual Question Answering (VQA) Bot — Local VLM

A multimodal bot that takes an image **and** a text prompt together and
answers questions about the image. Two built-in modes match the task's use
cases: **explain a diagram** and **troubleshoot from a photo**, plus a free
"ask a question" mode. Runs entirely locally on LLaVA via Ollama — no API
key, no quota.

## Architecture

```
app.py                Streamlit UI: upload image, pick mode, get answer
vqa/
  config.py           which VLM to use
  vlm_client.py       the ONLY file that calls Ollama (image + text -> text)
  vqa.py              builds the mode-specific prompt, orchestrates the call
```

The VLM call is isolated in one file; the modes are just different prompts
over the same call. Swapping LLaVA for another VLM (or for Gemini Vision) is a
change in `vlm_client.py` only.

## Setup

### 1. Ollama + the VLM (one-time)
Ollama should already be installed from the RAG task. Pull the vision model:
```powershell
ollama pull llava
```
(~4.7GB, needs ~8GB RAM. Low on RAM? Use `ollama pull moondream` and set
`VLM_MODEL = "moondream"` in vqa/config.py.)

### 2. Python deps
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Run
```powershell
python -m streamlit run app.py
```

## Demo flow

- **Explain diagram:** upload a circuit diagram, network topology, or flowchart
  → mode "Explain diagram" → it identifies components and relationships.
- **Troubleshoot:** upload a photo of an error screen, a miswired breadboard,
  or a leaking connector → mode "Troubleshoot" → it names the likely issue and
  suggests fixes.
- **Ask a question:** upload anything and ask a specific question about it.

Pre-run one analysis before the demo so the model is loaded into memory and
the first (slow) load isn't happening live.

## Talking points

- **What a VLM does:** an image encoder (CLIP-style) turns the picture into
  embeddings, a projection layer maps them into the language model's space, and
  the LLM then reasons over image + text tokens jointly. That joint reasoning
  is what lets it answer questions *about* the image.
- **Why local LLaVA:** matches the task example, no key/quota, fully offline.
- **Honest limits:** small local VLMs are weaker at dense text/OCR and fine
  detail than GPT-4V. For diagrams with lots of tiny labels, results vary —
  a good thing to acknowledge rather than hide.
