"""Model configuration.

llava = LLaVA 7B, a Vision Language Model that fuses a CLIP image encoder
with a language model. Good quality for diagrams and troubleshooting.

Lighter alternative for low-RAM machines:  VLM_MODEL = "moondream"  (~1.7GB)
Newer / stronger alternative:              VLM_MODEL = "llama3.2-vision"
Whichever you choose, pull it first:  ollama pull <model>
"""

VLM_MODEL = "llava"
