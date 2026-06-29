"""
Fine-tune a pre-trained BERT model for binary sentiment analysis (SST-2).

Pipeline:
  1. Load a pre-trained BERT (bidirectional encoder) + its tokenizer.
  2. Load a small slice of the SST-2 sentiment dataset.
  3. Tokenize text into the token IDs BERT expects.
  4. Attach a fresh classification head and fine-tune end-to-end.
  5. Evaluate accuracy/F1/precision/recall and save the model to disk.

It also reports a BEFORE-fine-tuning baseline (random head, ~50%) so the
jump to the fine-tuned score makes the value of transfer learning obvious.

Run on Colab (GPU) or a Python 3.11/3.12 venv. Do NOT use Python 3.14 —
PyTorch has no wheel for it yet.
"""

import numpy as np
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
)

# bert-base-uncased = the classic BERT. For a faster CPU demo, swap to
# "distilbert-base-uncased" (a distilled BERT: ~60% faster, ~97% of the
# accuracy, same bidirectional-encoder idea). One line, nothing else changes.
MODEL_NAME = "bert-base-uncased"
OUTPUT_DIR = "./sentiment-model"

# Keep the slices small so a demo finishes quickly. Raise these for accuracy.
N_TRAIN = 2000
N_EVAL = 500

# Human-readable label names. Baked into the model config below so the saved
# model emits "negative"/"positive" directly instead of LABEL_0/LABEL_1.
ID2LABEL = {0: "negative", 1: "positive"}
LABEL2ID = {"negative": 0, "positive": 1}


def compute_metrics(eval_pred):
    """Accuracy plus F1/precision/recall (positive class = 1)."""
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)

    accuracy = float((preds == labels).mean())

    # Confusion counts for the positive class.
    tp = float(((preds == 1) & (labels == 1)).sum())
    fp = float(((preds == 1) & (labels == 0)).sum())
    fn = float(((preds == 0) & (labels == 1)).sum())

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "accuracy": accuracy,
        "f1": f1,
        "precision": precision,
        "recall": recall,
    }


def main() -> None:
    # 1. Dataset: SST-2 (sentences labelled 0 = negative, 1 = positive).
    #    Use the official parquet mirror (stanfordnlp/sst2) rather than the
    #    legacy script-based "glue" loader: newer huggingface_hub requires
    #    namespaced repo IDs, and newer datasets no longer runs dataset scripts.
    raw = load_dataset("stanfordnlp/sst2")
    train_ds = raw["train"].shuffle(seed=42).select(range(N_TRAIN))
    # SST-2's test labels are hidden, so we evaluate on the validation split.
    eval_ds = raw["validation"].select(range(N_EVAL))

    # 2. Tokenizer turns text into the input IDs / attention masks BERT reads.
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize(batch):
        return tokenizer(batch["sentence"], truncation=True, max_length=128)

    train_ds = train_ds.map(tokenize, batched=True)
    eval_ds = eval_ds.map(tokenize, batched=True)

    # Pads each batch to the longest sequence in that batch (efficient).
    collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # 3. Model: pre-trained BERT body + an untrained 2-class head on top.
    #    id2label / label2id bake the human-readable names into the saved
    #    config, so the model outputs "negative"/"positive" not LABEL_0/1.
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=2,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    # 4. Training configuration. Small + short for a demo run.
    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=2,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        learning_rate=2e-5,
        logging_steps=20,
        report_to="none",  # no W&B / external loggers
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        processing_class=tokenizer,  # was `tokenizer=`; renamed in recent transformers
        data_collator=collator,
        compute_metrics=compute_metrics,
    )

    # 4a. BASELINE: evaluate BEFORE any training. The classification head is
    #     randomly initialised, so this should score ~0.50 — pure chance on a
    #     balanced 2-class task. This is the "before" number that makes the
    #     value of fine-tuning concrete.
    print("Evaluating BEFORE fine-tuning (random head, expect ~0.50)...")
    baseline = trainer.evaluate()
    print(
        f"  baseline  acc={baseline['eval_accuracy']:.4f}  "
        f"f1={baseline['eval_f1']:.4f}"
    )

    print("\nFine-tuning... (first run downloads the model, ~400MB)")
    trainer.train()

    print("\nEvaluating AFTER fine-tuning...")
    metrics = trainer.evaluate()
    print(
        f"  fine-tuned  acc={metrics['eval_accuracy']:.4f}  "
        f"f1={metrics['eval_f1']:.4f}  "
        f"precision={metrics['eval_precision']:.4f}  "
        f"recall={metrics['eval_recall']:.4f}"
    )

    # Headline before/after for the demo slide.
    print(
        f"\nFine-tuning lifted accuracy "
        f"{baseline['eval_accuracy']:.2f} -> {metrics['eval_accuracy']:.2f}"
    )

    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"\nSaved fine-tuned model to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
