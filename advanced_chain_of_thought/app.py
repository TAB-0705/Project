import streamlit as st
from prompts import (
    SAMPLE_PUZZLES,
    build_reasoning_prompt,
    build_evaluator_prompt,
    extract_answer,
    extract_best_path,
    majority_vote,
)
from gemini_client import generate

st.set_page_config(page_title="ToT Evaluator", page_icon="🌳")
st.title("🌳 Tree-of-Thoughts Evaluator")
st.caption("Generate multiple reasoning paths, then select the best one")

sample = st.selectbox("Load a sample puzzle (optional)", ["—"] + list(SAMPLE_PUZZLES))
default_text = SAMPLE_PUZZLES.get(sample, "")

puzzle = st.text_area(
    "Math or logic puzzle",
    value=default_text,
    height=130,
    placeholder="e.g. A father is 4 times as old as his son...",
)

num_paths = st.slider("Number of reasoning paths", 2, 4, 3)
st.caption(f"⚠️ This uses {num_paths} generation calls + 1 evaluator call = "
           f"{num_paths + 1} Gemini calls per solve.")

if st.button("Solve with multiple paths", type="primary"):
    if not puzzle.strip():
        st.warning("Please enter a puzzle first.")
    else:
        try:
            # 1) Generate diverse reasoning paths (high temperature).
            paths, answers = [], []
            with st.spinner("Generating reasoning paths..."):
                for _ in range(num_paths):
                    text = generate(build_reasoning_prompt(puzzle), temperature=0.8)
                    paths.append(text)
                    answers.append(extract_answer(text))

            st.subheader("Reasoning paths")
            for i, (text, ans) in enumerate(zip(paths, answers), 1):
                with st.expander(f"Path {i} — answer: {ans or '(none found)'}"):
                    st.write(text)

            # 2) Cheap self-consistency signal (no API call).
            vote = majority_vote(answers)
            if vote:
                st.info(f"Majority vote across paths: **{vote}**")

            # 3) Evaluator selects the best path (low temperature).
            with st.spinner("Evaluating paths..."):
                verdict = generate(
                    build_evaluator_prompt(puzzle, paths, answers), temperature=0.2
                )

            st.subheader("Evaluator verdict")
            best = extract_best_path(verdict)
            final = extract_answer(verdict)
            if best:
                st.write(f"**Selected path:** {best}")
            with st.expander("Evaluator's full reasoning"):
                st.write(verdict)
            if final:
                st.success(f"Final answer: {final}")

        except Exception as e:
            st.error(f"Error: {e}")
