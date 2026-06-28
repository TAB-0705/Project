"""The only module that knows which LLM backend is used. Swapping providers
is a config change; nothing else in the agent has to change."""

import os
from .config import LLM_PROVIDER, GEMINI_MODEL, OLLAMA_MODEL, TEMPERATURE


def build_llm():
    if LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=OLLAMA_MODEL, temperature=TEMPERATURE)

    # default: Gemini
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=TEMPERATURE,
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )
