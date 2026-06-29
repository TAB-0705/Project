import streamlit as st
from vqa.vqa import answer, MODE_INSTRUCTIONS
from vqa.config import VLM_MODEL

st.set_page_config(page_title="VQA Bot", page_icon="🖼️")
st.title("🖼️ Visual Question Answering Bot")
st.caption(f"Explain diagrams or troubleshoot photos · local VLM: {VLM_MODEL} (Ollama)")

uploaded = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])

if uploaded is not None:
    st.image(uploaded, caption="Uploaded image", use_container_width=True)

mode = st.radio("Mode", list(MODE_INSTRUCTIONS.keys()), horizontal=True)

question = st.text_input(
    "Question (optional for the first two modes, required for 'Ask a question')",
    placeholder="e.g. Why might this circuit not power on?",
)

if st.button("Analyze", type="primary"):
    if uploaded is None:
        st.warning("Please upload an image first.")
    elif mode == "Ask a question" and not question.strip():
        st.warning("Type a question for this mode.")
    else:
        with st.spinner("The VLM is looking at your image..."):
            try:
                image_bytes = uploaded.getvalue()
                result = answer(image_bytes, mode, question)
                st.markdown("### Answer")
                st.write(result)
            except Exception as e:
                st.error(f"Error (is Ollama running and the model pulled?): {e}")
