"""
Streamlit UI for the Wikipedia ReAct Agent.

Place this file in the PROJECT ROOT — the same folder that contains main.py and
the react_agent/ package. Then run:

    streamlit run streamlit_app.py

Why this is faithful to the real agent: it imports the SAME building blocks as
main.py (build_llm, build_tools, REACT_PROMPT, config). The only difference is
the executor is built with return_intermediate_steps=True so the UI can render
the agent's Thought -> Action -> Observation loop visually instead of printing
it to a terminal. Nothing in the react_agent/ package is changed.
"""

import os
import sys
import time

# Make `react_agent` importable no matter which directory Streamlit is launched
# from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # picks up GEMINI_API_KEY from .env if present

# langchain 1.x moved the classic string-ReAct agent + executor into the
# langchain-classic package. (On langchain 0.3.x, these were in
# `langchain.agents`.) Falling back keeps this working on either version.
try:
    from langchain_classic.agents import create_react_agent, AgentExecutor
except ImportError:
    from langchain.agents import create_react_agent, AgentExecutor

from react_agent.llm import build_llm
from react_agent.tools import build_tools
from react_agent.prompt import REACT_PROMPT
from react_agent import config as agent_config

# Optional live streaming of the reasoning loop. Present in recent
# langchain-community versions; degrade gracefully if missing.
try:
    from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
    _HAS_LIVE = True
except Exception:
    _HAS_LIVE = False


# --------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------
st.set_page_config(page_title="Wikipedia ReAct Agent", page_icon="🧭", layout="wide")


def build_executor() -> AgentExecutor:
    """Same wiring as react_agent/agent.py, but returns intermediate steps so
    the UI can show the reasoning trace."""
    llm = build_llm()
    tools = build_tools()
    agent = create_react_agent(llm, tools, REACT_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,                              # we render our own trace
        handle_parsing_errors=True,
        max_iterations=agent_config.MAX_ITERATIONS,
        return_intermediate_steps=True,
    )


def extract_thought(log: str) -> str:
    """The model's raw output for a step looks like:

        <reasoning text>
        Action: wikipedia
        Action Input: <query>

    Everything before 'Action:' is the Thought."""
    for marker in ("\nAction:", "Action:"):
        idx = log.find(marker)
        if idx != -1:
            return log[:idx].strip()
    return log.strip()


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")

    active_model = (
        agent_config.GEMINI_MODEL
        if agent_config.LLM_PROVIDER == "gemini"
        else agent_config.OLLAMA_MODEL
    )
    st.markdown(
        f"""
- **Provider:** `{agent_config.LLM_PROVIDER}`
- **Model:** `{active_model}`
- **Temperature:** `{agent_config.TEMPERATURE}`
- **Max iterations:** `{agent_config.MAX_ITERATIONS}`
"""
    )
    st.caption(
        "Provider/model come from `react_agent/config.py` — the single source "
        "of truth. Change them there to swap backends."
    )

    st.divider()

    if agent_config.LLM_PROVIDER == "gemini":
        key_input = st.text_input(
            "Gemini API key (optional override)",
            type="password",
            help="Leave blank to use the key from your .env file. Paste a key "
                 "from a fresh Google Cloud project here if you hit quota limits.",
        )
        if key_input:
            os.environ["GEMINI_API_KEY"] = key_input.strip()
        st.markdown(
            "✅ API key detected" if os.getenv("GEMINI_API_KEY")
            else "⚠️ No API key found"
        )

        # Model override — the fastest way around a temporary 503 overload is
        # to switch to a different model. Defaults to the one in config.py.
        model_options = [
            agent_config.GEMINI_MODEL,
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
        ]
        _seen = set()
        model_options = [m for m in model_options
                         if not (m in _seen or _seen.add(m))]
        chosen_model = st.selectbox(
            "Model (override if one is busy)",
            model_options,
            index=0,
            help="If you hit a 503 'high demand' error, switch models here.",
        )
        agent_config.GEMINI_MODEL = chosen_model

    st.divider()

    live = False
    if _HAS_LIVE:
        live = st.toggle(
            "Stream reasoning live",
            value=True,
            help="Watch the loop appear in real time, then see a clean summary "
                 "below. The full trace renders either way.",
        )
    else:
        st.caption(
            "Live streaming isn't available in this langchain-community "
            "version; the full trace still renders after the run."
        )

    st.divider()
    max_iters = st.slider(
        "Max reasoning steps",
        min_value=3, max_value=15,
        value=agent_config.MAX_ITERATIONS,
        help="How many Thought→Action→Observation cycles the agent may take "
             "before it's stopped. Higher = can handle harder, multi-hop "
             "questions; too high risks looping and burning quota.",
    )
    agent_config.MAX_ITERATIONS = max_iters

    st.divider()
    st.markdown("**Try an example:**")
    examples = [
        "Who wrote the novel that inspired the film Blade Runner?",
        "What year did the Eiffel Tower open, and how tall is it?",
        "Which scientist is the element Curium named after?",
        "What language is most spoken in the country where the Nile ends?",
    ]
    for i, ex in enumerate(examples):
        if st.button(ex, use_container_width=True, key=f"ex_{i}"):
            st.session_state["question"] = ex


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
st.title("🧭 Wikipedia ReAct Agent")
st.markdown(
    "Ask a question. The agent **reasons** about what it needs, **acts** by "
    "searching Wikipedia, **observes** the result, and repeats until it can "
    "answer — the ReAct loop, shown step by step."
)

question = st.text_input(
    "Your question",
    key="question",
    placeholder="e.g. Who wrote the novel that inspired Blade Runner?",
)

if st.button("▶️ Run agent", type="primary"):
    q = (question or "").strip()
    if not q:
        st.warning("Please enter a question first.")
        st.stop()

    if agent_config.LLM_PROVIDER == "gemini" and not os.getenv("GEMINI_API_KEY"):
        st.error("No Gemini API key found. Add one to your .env file or paste "
                 "one in the sidebar.")
        st.stop()

    try:
        executor = build_executor()
    except Exception as e:
        st.error(f"Couldn't build the agent: {e}")
        st.stop()

    # --- Run with retry + backoff. Gemini occasionally returns HTTP 503 when
    # a model is briefly overloaded; re-issuing the request usually succeeds.
    MAX_ATTEMPTS = 4
    result = None
    status = st.empty()
    live_area = st.empty()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        callbacks = []
        if live and _HAS_LIVE:
            container = live_area.container()
            container.subheader("🔴 Live reasoning")
            callbacks.append(StreamlitCallbackHandler(container))
        try:
            spin = "Thinking..." if attempt == 1 else f"Retrying (attempt {attempt})..."
            with st.spinner(spin):
                result = executor.invoke(
                    {"input": q},
                    config={"callbacks": callbacks} if callbacks else None,
                )
            status.empty()
            break
        except Exception as e:
            msg = str(e).lower()
            # Quota exhaustion — retrying won't help.
            if any(s in msg for s in ("quota", "429", "resourceexhausted", "rate limit")):
                status.empty()
                st.error("Gemini quota exhausted. Paste a key from a fresh Google "
                         "Cloud project in the sidebar, or set LLM_PROVIDER = "
                         "'ollama' in config.py.")
                st.stop()
            # Transient overload / server hiccup — back off and retry.
            transient = any(s in msg for s in (
                "503", "unavailable", "overloaded", "high demand",
                "internal", "500", "deadline", "timeout"))
            if transient and attempt < MAX_ATTEMPTS:
                wait = 2 ** attempt  # 2s, 4s, 8s
                live_area.empty()
                status.warning(f"Model busy (503). Retrying in {wait}s… "
                               f"(attempt {attempt} of {MAX_ATTEMPTS})")
                time.sleep(wait)
                continue
            # Non-transient, or out of retries.
            status.empty()
            if transient:
                st.error("The model stayed overloaded after several retries — a "
                         "temporary issue on Google's side. Wait a moment and "
                         "click Run again, switch models in the sidebar, or set "
                         "LLM_PROVIDER = 'ollama' in config.py.")
            else:
                st.error(f"The agent run failed: {e}")
            st.stop()

    if result is None:
        st.stop()

    output = result.get("output", "(no output)")
    steps = result.get("intermediate_steps", [])

    # If the agent hit its step limit before stating a Final Answer, don't throw
    # away the work it did — compose a best-effort answer from the observations
    # it already gathered.
    if "Agent stopped due to iteration limit" in output and steps:
        notes = "\n\n".join(
            f"Search: {a.tool_input}\nResult: {obs}" for a, obs in steps
        )
        synth_prompt = (
            "Answer the question using ONLY the notes gathered from Wikipedia "
            "below. Give the most complete answer you can; if the notes are "
            "insufficient, state what is known and what is still missing.\n\n"
            f"Question: {q}\n\nNotes:\n{notes}\n\nAnswer:"
        )
        try:
            with st.spinner("Step limit reached — composing an answer from what "
                            "was gathered..."):
                synth = build_llm().invoke(synth_prompt)
            output = getattr(synth, "content", None) or str(synth)
            st.info("⏱️ The agent reached its step limit, so this answer was "
                    "composed from the information it had already gathered. "
                    "Raise **Max reasoning steps** in the sidebar to give it "
                    "more room.")
        except Exception:
            st.warning("The agent reached its step limit before finishing, and "
                       "the fallback summary couldn't be generated. Try raising "
                       "Max reasoning steps or simplifying the question.")

    # Final answer
    st.subheader("✅ Final answer")
    st.success(output)

    # Reasoning trace
    st.subheader("🧠 Reasoning trace")
    st.caption(f"{len(steps)} tool call(s) before answering.")

    if not steps:
        st.info("The agent answered directly without needing a tool.")
    else:
        for i, (action, observation) in enumerate(steps, start=1):
            with st.container(border=True):
                st.markdown(f"**Step {i}**")
                thought = extract_thought(getattr(action, "log", "") or "")
                if thought:
                    st.markdown(f"💭 **Thought:** {thought}")
                st.markdown(
                    f"🔧 **Action:** `{action.tool}`  ·  "
                    f"**Input:** `{action.tool_input}`"
                )
                obs = str(observation)
                st.markdown("📄 **Observation:**")
                st.text(obs if len(obs) <= 600 else obs[:600] + " …")
                if len(obs) > 600:
                    with st.expander("Show full observation"):
                        st.text(obs)

st.divider()
st.caption(
    "ReAct = Reasoning + Acting. The Thought/Action/Observation scaffold in "
    "`react_agent/prompt.py` is what makes the model emit parseable tool calls. "
    "Answers are grounded in Wikipedia observations, not the model's memory."
)
