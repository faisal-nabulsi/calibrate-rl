"""
Grader unit tests — lock in the hardened extract/compare behaviour so future
edits can't silently regress it. Run either way:

    python3 test_reward_func.py        # plain, no deps
    pytest test_reward_func.py

Covers the cases from the step-7 review: boxed integers/negatives/commas,
\\frac and \\dfrac (incl. negative), multiple boxed (take LAST), the gated
single-number fallback (candidate-listing must score ZERO), fraction<->decimal
equivalence, and no-answer.
"""
from reward_func import (
    extract_predicted_answer, extract_gold_answer, _numbers_match,
)


def graded(text, gold):
    """Return (is_correct, predicted, method) using the real grading path."""
    pred, method = extract_predicted_answer(text)
    g = extract_gold_answer(str(gold))
    correct = g is not None and pred is not None and _numbers_match(pred, g)
    return correct, pred, method


# (description, model_text, gold, expect_correct, expect_method_or_None)
CASES = [
    # --- boxed, the happy path ---
    ("boxed int",                 r"so \boxed{42}",            "42",   True,  "boxed"),
    ("boxed wrong",               r"so \boxed{41}",            "42",   False, "boxed"),
    ("boxed negative",            r"\boxed{-3}",               "-3",   True,  "boxed"),
    ("boxed with commas",         r"\boxed{1,000}",            "1000", True,  "boxed"),
    ("boxed with spaces",         r"\boxed{ 42 }",             "42",   True,  "boxed"),
    ("boxed units after",         r"\boxed{42} square units",  "42",   True,  "boxed"),

    # --- fractions (#5) ---
    ("frac vs decimal gold",      r"\boxed{\frac{1}{2}}",      "0.5",  True,  "boxed"),
    ("dfrac vs decimal gold",     r"\boxed{\dfrac{3}{4}}",     "0.75", True,  "boxed"),
    ("frac vs frac gold",         r"\boxed{\frac{1}{2}}",      "1/2",  True,  "boxed"),
    ("negative frac keeps sign",  r"\boxed{-\frac{1}{2}}",     "-0.5", True,  "boxed"),
    ("negative frac not pos",     r"\boxed{-\frac{1}{2}}",     "0.5",  False, "boxed"),
    ("bare fraction in 'answer is'", "the answer is 0.5",      "1/2",  True,  "the_answer_is"),

    # --- multiple boxed: take the LAST (#4) ---
    ("multi-boxed last correct",  r"\boxed{41} ... actually \boxed{42}", "42", True,  "boxed"),
    ("multi-boxed last wrong",    r"\boxed{42} ... oops \boxed{41}",     "42", False, "boxed"),

    # --- gated fallback: candidate-listing must NOT score (#4 hack) ---
    ("candidate list gold last",  "Could be 10, 20, 30, or 42.", "42", False, "no_answer"),
    ("candidate list gold mid",   "Maybe 42 or 99.",             "42", False, "no_answer"),
    ("right num in wrong work",   "since 6*7=42 we get 13",      "42", False, "no_answer"),
    ("lone number credited",      "42",                          "42", True,  "single_number_fallback"),

    # --- explicit answer markers still work ---
    ("the answer is",             "Therefore the answer is 42.", "42", True,  "the_answer_is"),
    ("bold answer",               "The result is **42**.",       "42", True,  "bold"),

    # --- nothing to grade ---
    ("no number at all",          "I cannot solve this.",        "42", False, "no_answer"),
]


def run():
    fails = []
    for desc, text, gold, exp_ok, exp_method in CASES:
        ok, pred, method = graded(text, gold)
        bad = (ok != exp_ok) or (exp_method is not None and method != exp_method)
        flag = "ok " if not bad else "FAIL"
        if bad:
            fails.append((desc, exp_ok, exp_method, ok, method, pred))
        print(f"  [{flag}] {desc:32} -> correct={ok} pred={pred} via {method}")
    print()
    if fails:
        print(f"{len(fails)} FAILURE(S):")
        for d, eo, em, ao, am, p in fails:
            print(f"  - {d}: expected correct={eo}/method={em}, got correct={ao}/method={am} (pred={p})")
        raise SystemExit(1)
    print(f"All {len(CASES)} grader cases passed.")


# pytest entry points
def test_grader_cases():
    for desc, text, gold, exp_ok, exp_method in CASES:
        ok, pred, method = graded(text, gold)
        assert ok == exp_ok, f"{desc}: correct={ok} pred={pred} method={method}"
        if exp_method is not None:
            assert method == exp_method, f"{desc}: method={method} pred={pred}"


if __name__ == "__main__":
    run()
