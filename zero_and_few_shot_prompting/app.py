import streamlit as st
from prompts import build_zero_shot_prompt, build_few_shot_prompt
from gemini_client import generate_reply

st.set_page_config(page_title="Support Email Responder", page_icon="✉️")
st.title("✉️ Customer Support Email Responder")
st.caption("Zero-shot vs Few-shot prompting demo")

mode = st.radio("Prompting strategy", ["Zero-shot", "Few-shot"], horizontal=True)

customer_email = st.text_area(
    "Paste the customer's email",
    height=160,
    placeholder="e.g. My order arrived damaged and I'd like a replacement...",
)

show_prompt = st.checkbox("Show the prompt sent to the model")

if st.button("Generate reply", type="primary"):
    if not customer_email.strip():
        st.warning("Please paste a customer email first.")
    else:
        prompt = (
            build_zero_shot_prompt(customer_email)
            if mode == "Zero-shot"
            else build_few_shot_prompt(customer_email)
        )
        if show_prompt:
            with st.expander("Prompt sent to the model"):
                st.code(prompt)
        with st.spinner("Generating..."):
            try:
                st.subheader("Generated reply")
                st.write(generate_reply(prompt))
            except Exception as e:
                st.error(f"Error: {e}")
