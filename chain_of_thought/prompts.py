SYSTEM_INSTRUCTION = (
    "You are a careful problem solver who handles math and logic puzzles. "
    "Be precise and do not skip steps."
)

# Sample puzzles for the demo (label -> puzzle text)
SAMPLE_PUZZLES = {
    "Train speeds": (
        "Two trains start 300 km apart and move toward each other. "
        "One travels at 60 km/h, the other at 40 km/h. "
        "How long until they meet, and how far has the faster train gone?"
    ),
    "Age riddle": (
        "A father is 4 times as old as his son. In 20 years, he will be "
        "twice as old as his son. How old are they now?"
    ),
    "Logic grid": (
        "Anna, Ben, and Cara have a cat, a dog, and a fish (in some order). "
        "Anna does not own the fish. Ben owns the dog. Who owns the fish?"
    ),
    "Bat and ball": (
        "A bat and a ball cost $1.10 in total. The bat costs $1.00 more "
        "than the ball. How much does the ball cost?"
    ),
}


def build_direct_prompt(puzzle: str) -> str:
    """No reasoning requested — model is pushed to answer immediately."""
    return (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"Solve the following. Give ONLY the final answer, no explanation.\n\n"
        f"Puzzle:\n{puzzle}\n\n"
        f"Final answer:"
    )


def build_cot_prompt(puzzle: str) -> str:
    """Forces explicit step-by-step reasoning before the answer."""
    return (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"Solve the following puzzle by thinking step by step. "
        f"Work through the reasoning explicitly, one step at a time. "
        f"After the reasoning, state the result on a new line that begins "
        f"exactly with 'Final answer:'.\n\n"
        f"Puzzle:\n{puzzle}\n\n"
        f"Let's think step by step."
    )


def split_reasoning_and_answer(text: str):
    """Separate the chain of thought from the final answer for clean display.

    Returns (reasoning, answer). If no marker is found, returns (text, "").
    """
    marker = "Final answer:"
    idx = text.rfind(marker)
    if idx == -1:
        return text.strip(), ""
    reasoning = text[:idx].strip()
    answer = text[idx + len(marker):].strip()
    return reasoning, answer
