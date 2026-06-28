# Wikipedia ReAct Agent (LangChain)

A LangChain agent that answers questions by **reasoning** and **acting** —
the ReAct framework. It decides when it needs information, calls a Wikipedia
search tool, reads the result, and repeats until it can answer.

## Files

```
main.py                 CLI: run a query, watch the ReAct trace
react_agent/
  config.py             provider, models, tool settings
  llm.py                builds the LLM (Gemini default; Ollama optional)
  tools.py              the Wikipedia search tool (the "acting" half)
  prompt.py             the ReAct prompt template  <-- the core deliverable
  agent.py              wires LLM + tools + prompt into an executor
```

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Rename `.env.example` to `.env` and add your Gemini key (use your fresh Google
Cloud project's key to avoid quota issues).

## Run

```powershell
python main.py "Who wrote the novel that inspired the film Blade Runner?"
```
`verbose=True` prints the agent's reasoning loop:
```
Thought: I should look up the novel behind Blade Runner.
Action: wikipedia
Action Input: Blade Runner novel
Observation: ... Do Androids Dream of Electric Sheep? by Philip K. Dick ...
Thought: I now know the final answer.
Final Answer: Philip K. Dick wrote "Do Androids Dream of Electric Sheep?"...
```

## Switching to local (no quota)

In `config.py` set `LLM_PROVIDER = "ollama"` and `ollama pull llama3.2`.
Note: small local models sometimes break the strict ReAct format; Gemini is
more reliable for the demo.

## Talking points

- **ReAct = Reasoning + Acting.** Plain chain-of-thought only *reasons*; a tool
  agent only *acts*. ReAct interleaves them: think, act, observe, think again.
- **The prompt is the mechanism.** The Thought/Action/Action Input/Observation
  scaffold in `prompt.py` is what makes the model emit tool calls in a parseable
  format. That template, plus the tool, is the entire agent.
- **Why `handle_parsing_errors=True` and `max_iterations`.** Real safeguards:
  recover when the model mis-formats a step, and stop a confused agent from
  looping forever.
- **Grounded answers.** The agent answers from what Wikipedia returned
  (Observations), not from the model's memory — reducing hallucination.
