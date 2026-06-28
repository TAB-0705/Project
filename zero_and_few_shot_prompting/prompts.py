SYSTEM_INSTRUCTION = (
    "You are a professional customer support agent for an e-commerce company. "
    "Write clear, empathetic, and concise email replies. "
    "Keep a polite, helpful tone and end with a courteous sign-off."
)

# Few-shot examples: (incoming customer email, ideal support reply)
FEW_SHOT_EXAMPLES = [
    (
        "I ordered a pair of shoes last week and they still haven't arrived. Order #12345.",
        "Hi there,\n\nThanks for reaching out, and I'm sorry your order #12345 hasn't arrived yet. "
        "I've checked and your package is in transit, expected within 2 business days. "
        "I'll keep an eye on it and follow up if there's any delay.\n\nBest regards,\nSupport Team",
    ),
    (
        "The blender I bought stopped working after two days. I want a refund.",
        "Hi,\n\nI'm sorry your blender stopped working so soon — that's not the experience we want for you. "
        "You're fully eligible for a refund, which I've started; you'll see it on your original payment "
        "method within 5-7 business days. A prepaid return label is on its way to your email.\n\nWarm regards,\nSupport Team",
    ),
]


def build_zero_shot_prompt(customer_email: str) -> str:
    """No examples — the model relies purely on the instruction."""
    return (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f'Customer email:\n"""\n{customer_email}\n"""\n\n'
        f"Write the support reply:"
    )


def build_few_shot_prompt(customer_email: str) -> str:
    """A few example pairs steer the model's tone and structure."""
    examples_block = ""
    for i, (email, reply) in enumerate(FEW_SHOT_EXAMPLES, 1):
        examples_block += (
            f"Example {i}\n"
            f'Customer email:\n"""\n{email}\n"""\n'
            f'Support reply:\n"""\n{reply}\n"""\n\n'
        )
    return (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"Here are examples of well-handled replies:\n\n"
        f"{examples_block}"
        f"Now write a reply in the same style.\n"
        f'Customer email:\n"""\n{customer_email}\n"""\n'
        f"Support reply:"
    )
