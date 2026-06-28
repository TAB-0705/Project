"""Settings in one place."""

# "gemini" follows the strict ReAct format reliably (recommended for the demo).
# "ollama" runs fully local but small models sometimes break the format.
LLM_PROVIDER = "gemini"

# gemini-2.5-flash: stronger reasoning than flash-lite and faster on multi-step
# ReAct chains, while keeping a generous free quota. Drop to
# "gemini-2.5-flash-lite" if you need maximum quota, or "gemini-2.5-pro" for the
# most capable (but slower, lower-quota) option. You can also switch live from
# the Streamlit sidebar.
GEMINI_MODEL = "gemini-2.5-flash"
OLLAMA_MODEL = "llama3.2"

# 0.0 = deterministic reasoning, which is what you want for an agent loop.
TEMPERATURE = 0.0

# Wikipedia tool: how many articles to pull and how much text to keep.
WIKI_TOP_K = 3
WIKI_MAX_CHARS = 2000

# Safety cap so a confused agent can't loop forever. 10 gives room for
# multi-hop questions (most finish in 1-3 steps); the Streamlit sidebar can
# raise it live up to 15. Removing the cap entirely is unsafe — a stuck agent
# would loop forever and burn quota.
MAX_ITERATIONS = 10
