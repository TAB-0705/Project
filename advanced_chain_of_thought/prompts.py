from collections import Counter

SYSTEM_INSTRUCTION = (
    "You are a careful problem solver who handles math and logic puzzles. "
    "Be precise and do not skip steps."
)

SAMPLE_PUZZLES = {
    "Age riddle": (
        "A father is 4 times as old as his son. In 20 years, he will be "
        "twice as old as his son. How old are they now?"
    ),
    "Bat and ball": (
        "A bat and a ball cost $1.10 in total. The bat costs $1.00 more "
        "than the ball. How much does the ball cost?"
    ),
    "Coins": (
        "I have 12 coins. One is counterfeit and weighs slightly less. "
        "Using a balance scale, what is the minimum number of weighings "
        "needed to guarantee finding it, and briefly how?"
    ),
    "Logic grid": (
        "Anna, Ben, and Cara have a cat, a dog, and a fish (in some order). "
        "Anna does not own the fish. Ben owns the dog. Who owns the fish?"
    ),
}


def build_reasoning_prompt(puzzle: str) -> str:
    """One independent chain-of-thought path. Sampled at higher temperature
    so repeated calls explore DIFFERENT lines of reasoning."""
    return (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"Solve the following puzzle by thinking step by step. "
        f"Work through your reasoning explicitly. "
        f"End with a line that begins exactly with 'Final answer:'.\n\n"
        f"Puzzle:\n{puzzle}\n\n"
        f"Let's think step by step."
    )


def _format_tally(answers: list[str]) -> str:
    """Human-readable summary of how often each answer appeared."""
    counts = Counter(a.strip() for a in answers if a.strip())
    if not counts:
        return "(no parseable answers)"
    return "; ".join(f'"{ans}" appeared {n} time(s)' for ans, n in counts.most_common())


def build_evaluator_prompt(puzzle: str, paths: list[str], answers: list[str]) -> str:
    """The evaluator: reviews every candidate reasoning path, is shown how
    often each answer occurred, and selects the soundest one.

    Giving the evaluator the tally is deliberate: it must justify the result
    on the MERITS of the reasoning, and explicitly defend any decision to
    override the most frequent answer rather than just rubber-stamping it.

    Output format is fixed so it can be parsed reliably for the demo.
    """
    candidates = ""
    for i, path in enumerate(paths, 1):
        candidates += f"--- Reasoning Path {i} ---\n{path}\n\n"

    tally = _format_tally(answers)

    return (
        f"You are an expert evaluator of reasoning. Below is a puzzle and "
        f"several independent attempts to solve it. Some may contain errors.\n\n"
        f"Puzzle:\n{puzzle}\n\n"
        f"{candidates}"
        f"For reference, the final answers proposed were: {tally}.\n"
        f"Do NOT simply pick the most frequent answer. Check each path's logic "
        f"and arithmetic yourself. If the most common answer is wrong, say so "
        f"and choose the correct one, explaining why the majority erred.\n\n"
        f"Respond in EXACTLY this format:\n"
        f"Best path: <the path number>\n"
        f"Reason: <one or two sentences on why it is best>\n"
        f"Final answer: <the correct final answer>"
    )


def _extract_after(text: str, marker: str, single_line: bool) -> str:
    """Case-insensitive search for `marker`; return what follows it.

    Robust to capitalisation drift ('Best Path:', 'FINAL ANSWER:') and
    stray leading punctuation/markdown the model sometimes adds.
    """
    lower = text.lower()
    key = marker.lower()
    idx = lower.rfind(key) if "answer" in key else lower.find(key)
    if idx == -1:
        return ""
    rest = text[idx + len(marker):]
    if single_line:
        lines = rest.splitlines()
        rest = lines[0] if lines else ""
    return rest.strip().lstrip("*:-# ").strip()


def extract_answer(text: str) -> str:
    """Text after the last 'Final answer:' marker (case-insensitive)."""
    return _extract_after(text, "Final answer:", single_line=False)


def extract_best_path(text: str) -> str:
    """Value after 'Best path:' from the evaluator output (case-insensitive)."""
    return _extract_after(text, "Best path:", single_line=True)


def majority_vote(answers: list[str]) -> str:
    """Self-consistency: the most common final answer across paths.
    A cheap second selection signal that needs no extra API call."""
    cleaned = [a.strip().lower() for a in answers if a.strip()]
    if not cleaned:
        return ""
    return max(set(cleaned), key=cleaned.count)
