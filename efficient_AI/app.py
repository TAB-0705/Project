import streamlit as st
from rag.pipeline import RAGPipeline
from rag.config import GEN_MODEL, EMBED_MODEL

st.set_page_config(page_title="Local RAG", page_icon="📚")
st.title("📚 Fully Local RAG")
st.caption(f"Retrieval-Augmented Generation · SLM: {GEN_MODEL} · "
           f"embeddings: {EMBED_MODEL} · all running in Ollama")

# Persist the pipeline across Streamlit reruns.
if "rag" not in st.session_state:
    st.session_state.rag = RAGPipeline()
rag = st.session_state.rag

# --- 1. Ingest a document --------------------------------------------------
st.subheader("1. Add a document")
uploaded = st.file_uploader("Upload a .txt file", type=["txt"])
pasted = st.text_area("...or paste text here", height=150)

if st.button("Ingest", type="primary"):
    text = ""
    if uploaded is not None:
        text = uploaded.read().decode("utf-8", errors="ignore")
    elif pasted.strip():
        text = pasted
    if not text.strip():
        st.warning("Upload a file or paste some text first.")
    else:
        with st.spinner("Chunking and embedding..."):
            try:
                n = rag.ingest(text)
                st.success(f"Ingested {n} chunks. Ask a question below.")
            except Exception as e:
                st.error(f"Error (is Ollama running?): {e}")

# --- 2. Ask a question -----------------------------------------------------
st.subheader("2. Ask a question")
question = st.text_input("Your question")

if st.button("Answer"):
    if not question.strip():
        st.warning("Type a question first.")
    elif rag.store.is_empty():
        st.warning("Ingest a document before asking.")
    else:
        with st.spinner("Retrieving and generating..."):
            try:
                answer, hits = rag.query(question)
                st.markdown("### Answer")
                st.write(answer)
                with st.expander("Retrieved context (what the SLM was given)"):
                    for i, (chunk, score) in enumerate(hits, 1):
                        st.markdown(f"**Chunk {i}** — similarity {score:.3f}")
                        st.write(chunk)
                        st.divider()
            except Exception as e:
                st.error(f"Error (is Ollama running?): {e}")
