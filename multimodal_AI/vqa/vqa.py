"""Turns a chosen mode + optional user question into the right instruction
for the VLM. The two task use-cases (explain a diagram, troubleshoot a photo)
are just different system instructions over the same image+text call."""

from .vlm_client import ask

# Mode -> base instruction. "Ask a question" has no fixed instruction.
MODE_INSTRUCTIONS = {
    "Explain diagram": (
        "You are an expert at reading technical diagrams. Look at the image "
        "and explain what it shows: identify the key components, how they "
        "connect or relate, and what the overall diagram represents. Be clear "
        "and structured."
    ),
    "Troubleshoot": (
        "You are a troubleshooting assistant. Examine the photo, identify any "
        "visible problem or fault, explain the likely cause, and give concrete "
        "steps to fix it. If you are unsure, say what additional information "
        "you would need."
    ),
    "Ask a question": None,
}


def build_prompt(mode: str, question: str) -> str:
    instruction = MODE_INSTRUCTIONS.get(mode)

    if instruction is None:  # free-question mode
        return question.strip() or "Describe this image in detail."

    if question.strip():
        return f"{instruction}\n\nAlso address this specific question: {question.strip()}"
    return instruction


def answer(image_bytes: bytes, mode: str, question: str) -> str:
    prompt = build_prompt(mode, question)
    return ask(image_bytes, prompt)
