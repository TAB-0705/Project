"""The three roles the AI plays across turns, plus helpers to read its output.

  1. WRITER  - produce code for the task
  2. REVIEWER - critique its own code, ending with a clear verdict
  3. FIXER   - rewrite the code to address the critique

The reviewer's verdict ('APPROVED' vs 'NEEDS_WORK') is the loop's stop signal.
"""

import re


def build_generate_prompt(task: str) -> str:
    return (
        "You are an expert Python developer.\n"
        "Write Python code that solves the task below.\n"
        "Return ONLY the code — no explanation, no markdown fences.\n\n"
        f"Task:\n{task}"
    )


def build_review_prompt(task: str, code: str) -> str:
    return (
        "You are a strict senior code reviewer. Review the code for the task.\n"
        "Look hard for bugs, unhandled edge cases, incorrect logic, and bad "
        "practices. Be specific and concise.\n\n"
        "If the code is fully correct AND handles edge cases, reply with only:\n"
        "VERDICT: APPROVED\n\n"
        "Otherwise, list the concrete issues, then end with a final line:\n"
        "VERDICT: NEEDS_WORK\n\n"
        f"Task:\n{task}\n\n"
        f"Code:\n{code}"
    )


def build_fix_prompt(task: str, code: str, review: str) -> str:
    return (
        "You are an expert Python developer. Below is a task, your previous "
        "code, and a reviewer's critique. Rewrite the code to fix EVERY issue "
        "raised.\n"
        "Return ONLY the corrected code — no explanation, no markdown fences.\n\n"
        f"Task:\n{task}\n\n"
        f"Previous code:\n{code}\n\n"
        f"Reviewer's critique:\n{review}"
    )


def strip_code_fences(text: str) -> str:
    """Remove ```python ... ``` fences if the model added them anyway."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]  # drop opening fence line
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]  # drop closing fence
        text = "\n".join(lines)
    return text.strip()


def is_approved(review: str) -> bool:
    """Read the reviewer's verdict. Approved only if a verdict line clearly
    says APPROVED and not NEEDS_WORK."""
    for line in review.splitlines():
        low = line.lower()
        if "verdict" in low:
            return "approved" in low and "needs" not in low
    return False  # no verdict found -> assume more work needed
