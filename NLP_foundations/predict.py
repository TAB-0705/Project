"""
Load the fine-tuned sentiment model and classify new sentences.
Run this AFTER train.py has produced ./sentiment-model.
"""

from transformers import pipeline

MODEL_DIR = "./sentiment-model"

# The trained model now carries id2label in its config, so the pipeline
# returns "negative"/"positive" directly. This fallback only matters if you
# point MODEL_DIR at an older model that still emits LABEL_0/LABEL_1.
FALLBACK = {"LABEL_0": "negative", "LABEL_1": "positive"}

SAMPLES = [
    "This movie was an absolute masterpiece, I loved every minute.",
    "Worst purchase I've ever made. Completely useless.",
    "The food was okay but the service was painfully slow.",
    "Honestly one of the best experiences of my life.",
]


def main() -> None:
    clf = pipeline("sentiment-analysis", model=MODEL_DIR, tokenizer=MODEL_DIR)
    for text in SAMPLES:
        result = clf(text)[0]
        label = FALLBACK.get(result["label"], result["label"])
        print(f"[{label:8}] ({result['score']:.2f})  {text}")


if __name__ == "__main__":
    main()
