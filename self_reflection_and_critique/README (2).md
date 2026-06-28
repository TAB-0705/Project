# Self-Reviewing Code Pipeline (Reflexion)

A multi-turn pipeline where the AI **writes** code, **reviews** its own output
as a strict critic, and **fixes** the bugs it found — looping until the review
passes or a round limit is hit.

## Files

```
app.py                  Streamlit UI showing every turn of the loop
reflect/
  config.py             provider, model, max rounds
  llm.py                isolated LLM call (Gemini default, Ollama optional)
  prompts.py            the three role prompts + verdict/fence parsing
  pipeline.py           the write -> review -> fix loop with stop condition
```

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Rename `.env.example` to `.env` and add your Gemini key (use your fresh Google
Cloud project's key).

## Run

```powershell
python -m streamlit run app.py
```
Pick a sample task (the palindrome one is a good demo — naive code often misses
punctuation/spaces, so the reviewer has something real to catch), then watch the
initial code, each review verdict, and each revision.

## How it works (talking points)

- **The loop, not the three steps, is the point.** Anyone can prompt
  generate→review→fix once. The reflection is the *cycle*: review the fix, and
  only stop when the critic says APPROVED. The verdict line is the stop signal.
- **Why separate writer and reviewer prompts.** Giving the model a distinct
  'strict reviewer' role makes it critique more harshly than if it just
  continued its own writing — it's likelier to find its own bugs when reframed
  as an adversary to the code.
- **The safeguards.** `max_iterations` stops infinite loops; `is_approved`
  refuses to stop unless a clear verdict line says so; fence-stripping keeps the
  code clean if the model wraps it in markdown.

## Honest limits

- The reviewer is the same model grading its own work, so it can rubber-stamp
  buggy code or invent issues. A stronger version would also RUN the code
  against test cases and feed real pass/fail back in — execution-grounded
  reflection. That's the natural next step beyond pure self-critique.
