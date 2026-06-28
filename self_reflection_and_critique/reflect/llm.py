"""The only module that talks to an LLM. A single generate(prompt, provider)
function so the pipeline can use DIFFERENT models for different roles -- e.g.
Gemini writes the code while a free Groq-hosted model reviews it. Using a
separate model as the critic removes the self-leniency bias of a model grading
its own work.

Contract: generate(prompt, provider) -> str."""

import os
from .config import GEMINI_MODEL, GROQ_MODEL, GROK_MODEL, OLLAMA_MODEL


def generate(prompt: str, provider: str) -> str:
    if provider == "gemini":
        from google import genai
        from google.genai import types
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options=types.HttpOptions(timeout=60_000),  # ms
        )
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3),
        )
        return resp.text.strip()

    # Groq and xAI/Grok are BOTH OpenAI-compatible: same SDK, different
    # base_url + key + model. Groq is free; Grok is paid.
    if provider in ("groq", "grok"):
        from openai import OpenAI
        if provider == "groq":
            client = OpenAI(api_key=os.getenv("GROQ_API_KEY"),
                            base_url="https://api.groq.com/openai/v1", timeout=60)
            model = GROQ_MODEL
        else:
            client = OpenAI(api_key=os.getenv("XAI_API_KEY"),
                            base_url="https://api.x.ai/v1", timeout=60)
            model = GROK_MODEL
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # low: consistent critique, not creativity
        )
        return resp.choices[0].message.content.strip()

    if provider == "ollama":
        import ollama
        return ollama.generate(model=OLLAMA_MODEL, prompt=prompt)["response"].strip()

    raise ValueError(f"Unknown provider: {provider!r}")
