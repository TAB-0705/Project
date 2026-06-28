import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.5-flash-lite"  # highest free RPD


def generate(prompt: str) -> str:
    """Single text completion.

    Temperature is kept low for deterministic, checkable reasoning. The
    model's own 'thinking' is left off on purpose — the step-by-step
    reasoning is produced by the PROMPT, which is the whole point of the
    chain-of-thought demonstration.
    """
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.2},
        request_options={"timeout": 30},
    )
    return response.text.strip()
