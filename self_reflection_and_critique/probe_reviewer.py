"""Adversarial probe: does the reviewer actually validate, or just rubber-stamp?

The normal pipeline only exercises the reviewer IF the writer makes a mistake.
On easy tasks it usually doesn't, so the loop exits on turn 1 and you learn
nothing. This script removes the writer: it feeds the reviewer code we KNOW is
correct and code we KNOW is broken, prints the reviewer's actual critique, and
checks the verdicts.

Reading the result:
  GOOD -> APPROVED, BAD -> NEEDS_WORK  => reviewer validates well.
  GOOD -> NEEDS_WORK                   => read the critique:
       - cites a REAL gap (e.g. non-string input)  -> reviewer is strict (good)
       - vague / invented objection                -> reviewer is over-strict
  BAD  -> APPROVED                     => reviewer is rubber-stamping.

Note: the same model is easier on code it wrote itself, so the app may APPROVE a
generation the probe would reject. That gap is the point -- self-review is an
inconsistent gate.

Run:  python probe_reviewer.py
"""

from dotenv import load_dotenv
load_dotenv()

from reflect.llm import generate
from reflect.prompts import build_review_prompt, is_approved
from reflect.config import REVIEWER_PROVIDER

CASES = [
    {
        "task": "Write is_palindrome(s) that ignores case, spaces, and punctuation.",
        # Hardened: type guard + Unicode-aware (isalnum/casefold). Hard to fault.
        "good": (
            "def is_palindrome(s):\n"
            "    if not isinstance(s, str):\n"
            "        return False\n"
            "    cleaned = [c.casefold() for c in s if c.isalnum()]\n"
            "    return cleaned == cleaned[::-1]\n"
        ),
        "bad": (  # never normalizes -> fails 'A man, a plan, a canal: Panama'
            "def is_palindrome(s):\n"
            "    return s == s[::-1]\n"
        ),
        "bad_breaks_on": "'A man, a plan, a canal: Panama'",
    },
    {
        "task": "Write safe_divide(a, b) returning a/b, handling division by zero "
                "and non-numeric input gracefully.",
        "good": (
            "def safe_divide(a, b):\n"
            "    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):\n"
            "        return None\n"
            "    return None if b == 0 else a / b\n"
        ),
        "bad": (  # no guards -> crashes on safe_divide(1, 0)
            "def safe_divide(a, b):\n"
            "    return a / b\n"
        ),
        "bad_breaks_on": "safe_divide(1, 0)  (ZeroDivisionError)",
    },
]


def review_one(task, code):
    text = generate(build_review_prompt(task, code), REVIEWER_PROVIDER)
    return is_approved(text), text.strip()


def show(label, expected_ok, ok, critique):
    got = "APPROVED" if ok else "NEEDS_WORK"
    mark = "OK" if ok == expected_ok else "MISS"
    print(f"  {label} -> {got:10} (expected {'APPROVED' if expected_ok else 'NEEDS_WORK':10}) {mark}")
    # Print the reviewer's own words so you can judge if the objection is real.
    snippet = critique if len(critique) < 700 else critique[:700] + " ...[truncated]"
    for line in snippet.splitlines():
        print(f"      | {line}")
    print()


def main():
    caught = 0
    for c in CASES:
        print("=" * 72)
        print("TASK:", c["task"])
        print()

        ok_good, crit_good = review_one(c["task"], c["good"])
        show("GOOD", True, ok_good, crit_good)

        ok_bad, crit_bad = review_one(c["task"], c["bad"])
        caught += (not ok_bad)
        print(f"    (planted bug fails on: {c['bad_breaks_on']})")
        show("BAD ", False, ok_bad, crit_bad)

    print("=" * 72)
    print(f"Reviewer caught {caught}/{len(CASES)} planted bugs.")


if __name__ == "__main__":
    main()
