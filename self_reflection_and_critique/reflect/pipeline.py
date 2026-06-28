"""The self-reflection loop, now with a SEPARATE reviewer model:

    write (writer) -> [review (reviewer) -> approved? stop -> fix (writer)] xN

Splitting writer and reviewer across two different models is what makes the
critique trustworthy: the reviewer has no investment in code it didn't write,
so it won't approve its own work out of self-leniency."""

from .llm import generate
from .prompts import (
    build_generate_prompt,
    build_review_prompt,
    build_fix_prompt,
    strip_code_fences,
    is_approved,
)
from .config import MAX_ITERATIONS, WRITER_PROVIDER, REVIEWER_PROVIDER


def run_pipeline(task: str, max_iterations: int = MAX_ITERATIONS):
    """Returns (final_code, steps). steps entries:
      {"type": "generate", "code": ...}
      {"type": "review",   "review": ..., "approved": bool, "reviewer": str}
      {"type": "fix",      "code": ...}
    """
    steps = []

    # Turn 1: the WRITER produces the first version.
    code = strip_code_fences(generate(build_generate_prompt(task), WRITER_PROVIDER))
    steps.append({"type": "generate", "code": code})

    for _ in range(max_iterations):
        # The independent REVIEWER critiques the current code.
        review = generate(build_review_prompt(task, code), REVIEWER_PROVIDER)
        approved = is_approved(review)
        steps.append({
            "type": "review",
            "review": review,
            "approved": approved,
            "reviewer": REVIEWER_PROVIDER,
        })

        if approved:
            break

        # The WRITER rewrites the code to address the reviewer's critique.
        code = strip_code_fences(generate(build_fix_prompt(task, code, review), WRITER_PROVIDER))
        steps.append({"type": "fix", "code": code})

    return code, steps
