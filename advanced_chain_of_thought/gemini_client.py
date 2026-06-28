import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.5-flash-lite"  # highest free RPD


def generate(prompt: str, temperature: float = 0.2) -> str:
    """Single text completion.

    Temperature is exposed because this technique relies on it:
      - HIGH temperature when generating reasoning paths, so the paths
        actually diverge and explore different approaches.
      - LOW temperature for the evaluator, so its judgement is stable.
    """
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(
        prompt,
        generation_config={"temperature": temperature},
        request_options={"timeout": 30},
    )
    return response.text.strip()
