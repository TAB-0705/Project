"""
Streamlit demo UI for the fine-tuned BERT sentiment model.

Loads ./sentiment-model (produced by train.py) and classifies sentences live.
Run:  streamlit run app.py
The model is cached, so it loads once and stays warm across interactions.
"""

import streamlit as st
from transformers import pipeline

MODEL_DIR = "./sentiment-model"

# Measured on the 500-example SST-2 validation slice during the train.py run.
# These are real numbers from the actual training run, not placeholders.
# Re-run train.py and update these if the numbers change.
METRICS = {
    "baseline_acc": 0.4660,   # random head, before fine-tuning
    "acc": 0.8900,
    "f1": 0.8968,
    "precision": 0.8918,
    "recall": 0.9019,
}

# Preset examples. The last one is the "bidirectional showcase": sentiment
# only resolves on the back half of the sentence, so a left-to-right reader
# can be fooled by the early positive-ish word ("okay").
EXAMPLES = {
    "Clear positive": "This movie was an absolute masterpiece, I loved every minute.",
    "Clear negative": "Worst purchase I've ever made. Completely useless.",
    "Bidirectional showcase": "The food was okay but the service was painfully slow.",
    "Strong positive": "Honestly one of the best experiences of my life.",
}


@st.cache_resource(show_spinner="Loading fine-tuned BERT (one-time)...")
def load_classifier():
    """Load the sentiment pipeline once and reuse it across reruns."""
    return pipeline(
        "sentiment-analysis",
        model=MODEL_DIR,
        tokenizer=MODEL_DIR,
        top_k=None,  # return scores for BOTH classes, so we can show a full bar
    )


def classify(clf, text):
    """Return (top_label, top_score, {label: score}) for one sentence."""
    scores = clf(text)[0]  # list of {"label": ..., "score": ...} for all classes
    by_label = {d["label"]: d["score"] for d in scores}
    top = max(scores, key=lambda d: d["score"])
    return top["label"], top["score"], by_label


def label_color(label):
    return "#1a9850" if label.lower() == "positive" else "#d73027"


def render_result(label, score, by_label):
    color = label_color(label)
    st.markdown(
        f"<h3 style='color:{color};margin-bottom:0'>"
        f"{label.upper()} &nbsp;·&nbsp; {score*100:.1f}% confident</h3>",
        unsafe_allow_html=True,
    )
    # Per-class probability bars.
    for lbl in ("positive", "negative"):
        if lbl in by_label:
            st.caption(f"{lbl.capitalize()}: {by_label[lbl]*100:.1f}%")
            st.progress(min(max(by_label[lbl], 0.0), 1.0))


def main() -> None:
    st.set_page_config(page_title="BERT Sentiment Demo", page_icon="🧠")

    st.title("🧠 Fine-Tuned BERT — Sentiment Analysis")
    st.write(
        "A `bert-base-uncased` model fine-tuned on SST-2. Type any sentence "
        "and the model predicts **positive** or **negative** with a confidence "
        "score — running fully locally on the saved model."
    )

    # ---- Metrics panel: the before/after story -------------------------------
    with st.container():
        st.subheader("Measured performance (SST-2 validation, 500 examples)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Accuracy",
            f"{METRICS['acc']*100:.1f}%",
            delta=f"{(METRICS['acc']-METRICS['baseline_acc'])*100:+.1f} pts vs. baseline",
        )
        c2.metric("F1", f"{METRICS['f1']*100:.1f}%")
        c3.metric("Precision", f"{METRICS['precision']*100:.1f}%")
        c4.metric("Recall", f"{METRICS['recall']*100:.1f}%")
        st.caption(
            f"Baseline (random head, before fine-tuning): "
            f"{METRICS['baseline_acc']*100:.1f}% accuracy. "
            f"Fine-tuning lifted accuracy "
            f"{METRICS['baseline_acc']*100:.0f}% → {METRICS['acc']*100:.0f}% — "
            f"the gain is what the fine-tuning bought."
        )

    st.divider()

    clf = load_classifier()

    tab_single, tab_batch = st.tabs(["Single sentence", "Batch mode"])

    # ---- Single-sentence tab -------------------------------------------------
    with tab_single:
        st.write("**Try a preset, or type your own below.**")
        cols = st.columns(len(EXAMPLES))
        # Use session_state so example buttons populate the text box.
        if "text" not in st.session_state:
            st.session_state.text = EXAMPLES["Bidirectional showcase"]

        for col, (name, sentence) in zip(cols, EXAMPLES.items()):
            if col.button(name, use_container_width=True):
                st.session_state.text = sentence

        text = st.text_area(
            "Sentence to classify",
            key="text",
            height=90,
        )

        if st.button("Classify", type="primary"):
            if text.strip():
                label, score, by_label = classify(clf, text)
                render_result(label, score, by_label)

                # Call out the bidirectional showcase when it's the input.
                if text.strip() == EXAMPLES["Bidirectional showcase"]:
                    st.info(
                        "This sentence opens with a mildly positive word "
                        "(\"okay\") and only turns negative at the end "
                        "(\"painfully slow\"). BERT reads the whole sentence "
                        "in both directions at once, so it weights the ending "
                        "correctly — a left-to-right model is easier to fool here."
                    )
            else:
                st.warning("Type a sentence first.")

    # ---- Batch tab -----------------------------------------------------------
    with tab_batch:
        st.write("**One sentence per line.** All are classified at once.")
        batch_text = st.text_area(
            "Sentences",
            value="\n".join(EXAMPLES.values()),
            height=160,
            key="batch",
        )
        if st.button("Classify all", type="primary", key="batch_btn"):
            lines = [ln.strip() for ln in batch_text.splitlines() if ln.strip()]
            if not lines:
                st.warning("Add at least one sentence.")
            else:
                rows = []
                for ln in lines:
                    label, score, _ = classify(clf, ln)
                    rows.append(
                        {
                            "Sentence": ln,
                            "Prediction": label.capitalize(),
                            "Confidence": f"{score*100:.1f}%",
                        }
                    )
                st.dataframe(rows, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
