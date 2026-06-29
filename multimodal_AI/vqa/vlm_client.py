"""The only module that talks to the VLM. It takes image bytes plus a text
prompt and returns the model's answer. Because both image and text go into a
single call, the model reasons over them jointly — that's what 'multimodal'
means here."""

import ollama
from .config import VLM_MODEL


def ask(image_bytes: bytes, prompt: str) -> str:
    """Send one image + one text prompt to the local VLM and return its reply."""
    response = ollama.generate(
        model=VLM_MODEL,
        prompt=prompt,
        images=[image_bytes],  # ollama base64-encodes the bytes for us
    )
    return response["response"].strip()
