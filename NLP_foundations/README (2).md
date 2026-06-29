# Fine-Tuning BERT for Sentiment Analysis

Fine-tunes a pre-trained **BERT** (`bert-base-uncased`) on the SST-2 sentiment
dataset, then classifies new sentences. Demonstrates the full transfer-learning
loop: pre-trained bidirectional encoder → task-specific head → fine-tune → save → infer.

---

## ⚠️ Read this first: Python version

**PyTorch has no wheel for Python 3.14 yet.** Running this on your default
3.14 interpreter will fail at `pip install torch`. Use ONE of:

### Option A — Google Colab (recommended, easiest)
1. Go to https://colab.research.google.com → New notebook.
2. Runtime → Change runtime type → **T4 GPU**.
3. In a cell: `!pip install transformers datasets` (torch is preinstalled).
4. Upload `train.py` and `predict.py`, then in cells:
   `!python train.py` then `!python predict.py`.
Training takes ~2-3 minutes on the GPU.

### Option B — Local with Python 3.11 or 3.12
Install 3.12 alongside 3.14 (do not remove 3.14), then:
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install torch transformers datasets
python train.py
python predict.py
```
On CPU this is slow — reduce N_TRAIN in train.py to ~500 for a quick demo.

---

## What each file does

- `train.py` — loads BERT + SST-2, tokenizes, fine-tunes, evaluates accuracy,
  saves the model to `./sentiment-model`.
- `predict.py` — loads the saved model and classifies sample sentences.

## Demo tips

- **Pre-run `train.py` once before the demo.** The first run downloads the
  model (~400MB) and dataset; you don't want that happening live.
- After training, `predict.py` is your visual: it prints each sentence with a
  predicted label and confidence — clear proof the fine-tuned model works.
- For a faster CPU run, set `MODEL_NAME = "distilbert-base-uncased"` and lower
  `N_TRAIN`.
