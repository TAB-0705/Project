import streamlit as st
from prompts import (
    SAMPLE_PUZZLES,
    build_direct_prompt,
    build_cot_prompt,
    split_reasoning_and_answer,
)
from gemini_client import generate

st.set_page_config(page_title="CoT Puzzle Solver", page_icon="🧩")
st.title("🧩 Chain-of-Thought Puzzle Solver")
st.caption("Direct answer vs step-by-step reasoning")

mode = st.radio(
    "Prompting strategy",
    ["Chain-of-Thought", "Direct (no reasoning)"],
    horizontal=True,
)

sample = st.selectbox("Load a sample puzzle (optional)", ["—"] + list(SAMPLE_PUZZLES))
default_text = SAMPLE_PUZZLES.get(sample, "")

puzzle = st.text_area(
    "Math or logic puzzle",
    value=default_text,
    height=140,
    placeholder="e.g. A bat and a ball cost $1.10. The bat costs $1 more than the ball...",
)

show_prompt = st.checkbox("Show the prompt sent to the model")

if st.button("Solve", type="primary"):
    if not puzzle.strip():
        st.warning("Please enter a puzzle first.")
    else:
        is_cot = mode == "Chain-of-Thought"
        prompt = build_cot_prompt(puzzle) if is_cot else build_direct_prompt(puzzle)

        if show_prompt:
            with st.expander("Prompt sent to the model"):
                st.code(prompt)

        with st.spinner("Thinking..."):
            try:
                output = generate(prompt)
                if is_cot:
                    reasoning, answer = split_reasoning_and_answer(output)
                    st.subheader("Reasoning")
                    st.write(reasoning)
                    if answer:
                        st.subheader("Final answer")
                        st.success(answer)
                else:
                    st.subheader("Answer")
                    st.write(output)
            except Exception as e:
                st.error(f"Error: {e}")
