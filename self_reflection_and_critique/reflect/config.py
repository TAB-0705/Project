"""Settings in one place."""

# Each ROLE can use a different model. Writer != Reviewer ("cross-model review")
# is the whole point: an independent critic won't rubber-stamp code it didn't
# write, which a single self-reviewing model tends to do.
WRITER_PROVIDER   = "gemini"   # writes the first draft AND applies the fixes
REVIEWER_PROVIDER = "groq"     # critiques the code as an independent model

# Providers and whether they cost money:
#   "gemini" - Google, free tier
#   "groq"   - Groq (open models, e.g. Llama), FREE tier, no credit card  <-- note: Groq, not Grok
#   "ollama" - local, free, offline
#   "grok"   - xAI, PAID (only the one-time $25 trial is free)
GEMINI_MODEL = "gemini-2.5-flash"
GROQ_MODEL   = "llama-3.3-70b-versatile"   # strong, free on Groq's tier
GROK_MODEL   = "grok-4.3"                   # xAI, paid
OLLAMA_MODEL = "llama3.2"

# How many review->fix rounds at most before we stop.
MAX_ITERATIONS = 3
