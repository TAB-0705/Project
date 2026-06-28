import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from reflect.pipeline import run_pipeline
from reflect.config import MAX_ITERATIONS

st.set_page_config(page_title="Self-Reviewing Coder", page_icon="🔁")
st.title("🔁 Self-Reviewing Code Pipeline")
st.caption("The AI writes code, reviews its own work, and fixes bugs — looping "
           "until the review passes.")

SAMPLES = {
    "Palindrome (ignores case/punctuation)":
        "Write a function is_palindrome(s) that returns True if s is a "
        "palindrome, ignoring case, spaces, and punctuation.",
    "Median of a list":
        "Write a function median(nums) that returns the median of a list of "
        "numbers, correctly handling both odd and even length lists.",
    "Safe integer division":
        "Write a function safe_divide(a, b) that returns a / b, handling "
        "division by zero and non-numeric inputs gracefully.",
}

choice = st.selectbox("Sample task (or write your own below)", ["—"] + list(SAMPLES))
task = st.text_area("Coding task", value=SAMPLES.get(choice, ""), height=110)
iters = st.slider("Max review→fix rounds", 1, MAX_ITERATIONS, 2)

if st.button("Run pipeline", type="primary"):
    if not task.strip():
        st.warning("Enter a coding task first.")
    else:
        with st.spinner("Writing, reviewing, and fixing..."):
            try:
                final_code, steps = run_pipeline(task, max_iterations=iters)
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

        round_no = 0
        for step in steps:
            if step["type"] == "generate":
                st.subheader("✍️ Initial code")
                st.code(step["code"], language="python")
            elif step["type"] == "review":
                round_no += 1
                st.subheader(f"🔍 Review {round_no}")
                if step["approved"]:
                    st.success("VERDICT: APPROVED")
                else:
                    st.warning("VERDICT: NEEDS_WORK")
                with st.expander("Reviewer's critique"):
                    st.write(step["review"])
            elif step["type"] == "fix":
                st.subheader(f"🛠️ Revised code (after review {round_no})")
                st.code(step["code"], language="python")

        st.divider()
        st.subheader("✅ Final code")
        st.code(final_code, language="python")
