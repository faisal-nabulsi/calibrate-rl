from __future__ import annotations
import re
import logging
import json as _json

logger = logging.getLogger("tiny_math_solver")

_step_counter = 0
LOG_EVERY = 10
_reward_log = []


def _get_text(completion) -> str:
    if isinstance(completion, str):
        return completion
    if isinstance(completion, list):
        for msg in reversed(completion):
            if isinstance(msg, dict) and msg.get("content"):
                return msg["content"]
        return ""
    return str(completion)


def _normalize_number(s: str) -> float | None:
    if s is None:
        return None
    s = str(s).replace(",", "").strip()
    # handle fractions a/b
    if "/" in s:
        try:
            num, den = s.split("/")
            return float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _numbers_match(a: str, b: str) -> bool:
    a_f = _normalize_number(a)
    b_f = _normalize_number(b)
    if a_f is None or b_f is None:
        return False
    return abs(a_f - b_f) < 1e-6


def extract_gold_answer(label: str) -> str | None:
    if re.match(r"^-?[\d,\./]+$", str(label).strip()):
        return str(label).strip()
    match = re.search(r"####\s*(-?[\d,]+(?:\.\d+)?)", label)
    return match.group(1).replace(",", "") if match else None


def _clean_frac(s):
    # \frac{a}{b} or \dfrac{a}{b} -> "a/b"; plain numbers pass through (commas stripped)
    m = re.match(r"-?\\?d?frac\{(-?\d+)\}\{(-?\d+)\}", s)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return s.replace(",", "")


def extract_predicted_answer(text):
    # 1. \boxed{<number or \frac{a}{b}>} -- take the LAST boxed answer if several
    boxed = re.findall(
        r"\\boxed\{\s*(-?\\d?frac\{-?\d+\}\{-?\d+\}|-?[\d,]+(?:/\d+)?(?:\.\d+)?)",
        text,
    )
    if boxed:
        return _clean_frac(boxed[-1]), "boxed"

    # 2. #### <number>
    match = re.search(r"####\s*(-?[\d,]+(?:\.\d+)?)", text)
    if match:
        return match.group(1).replace(",", ""), "####"

    # 3. "the answer is <number>"
    match = re.search(
        r"[Tt]he\s+(?:final\s+)?answer\s+is\s*:?\s*\$?\s*(-?[\d,]+(?:\.\d+)?)", text
    )
    if match:
        return match.group(1).replace(",", ""), "the_answer_is"

    # 4. **<number>**
    matches = re.findall(r"\*\*(-?[\d,]+(?:\.\d+)?)\*\*", text)
    if matches:
        return matches[-1].replace(",", ""), "bold"

    # 5. GATED fallback: a bare number counts ONLY if it is the single number in the
    #    text. Kills candidate-listing ("could be 10, 20, or 42" -> no reward), which
    #    GRPO would otherwise learn to exploit, while still crediting a genuine lone
    #    answer that forgot the \boxed{}.
    numbers = re.findall(r"-?[\d,]+(?:\.\d+)?", text)
    if len(numbers) == 1:
        return numbers[0].replace(",", ""), "single_number_fallback"

    return None, "no_answer"


def correctness_reward(completions, answer, **kwargs) -> list[float]:
    global _step_counter
    _step_counter += 1

    rewards = []
    samples = []

    for completion, gold_label in zip(completions, answer):
        text = _get_text(completion)
        gold = extract_gold_answer(gold_label)
        pred, method = extract_predicted_answer(text)
        correct = gold is not None and pred is not None and _numbers_match(pred, gold)
        rewards.append(1.0 if correct else 0.0)
        samples.append((text, gold, pred, method, correct))

    for i, (text, gold, pred, method, correct) in enumerate(samples):
        _reward_log.append({
            'step': _step_counter,
            'gold': gold,
            'pred': pred,
            'correct': correct,
            'method': method,
            'problem_snippet': text[:100]
        })

    if _step_counter % 50 == 0:
        import os
        os.makedirs('logs', exist_ok=True)
        with open(f'logs/reward_log_step_{_step_counter}.json', 'w') as f:
            _json.dump(_reward_log[-500:], f)

    should_log = _step_counter <= 5 or _step_counter % LOG_EVERY == 0
    if should_log:
        n_correct = int(sum(rewards))
        n_parsed = sum(1 for _, _, pred, _, _ in samples if pred is not None)
        print(flush=True)
        print(f"{'='*70}", flush=True)
        print(f"  CORRECTNESS (step {_step_counter}) — "
              f"{n_correct}/{len(rewards)} correct, "
              f"{n_parsed}/{len(rewards)} parsed", flush=True)
        print(f"{'='*70}", flush=True)
        for i, (text, gold, pred, method, correct) in enumerate(samples[:4]):
            snippet = text[:500].replace('\n', ' | ')
            if len(text) > 500:
                snippet += "..."
            status = "CORRECT" if correct else "WRONG  "
            print(f"  [{status}] gold={gold}  pred={pred}  method={method}", flush=True)
            print(f"  Output: {snippet}", flush=True)
            print(f"  ---", flush=True)
        print(f"{'='*70}\n", flush=True)

    return rewards


def format_reward(completions, **kwargs) -> list[float]:
    rewards = []
    for completion in completions:
        text = _get_text(completion)
        has_boxed = bool(re.search(r"\\boxed\{-?[\d,]+(?:\.\d+)?", text))
        has_work = len(text.split()) > 30
        if has_boxed and has_work:
            rewards.append(0.1)
        elif not has_work:
            rewards.append(-0.2)
        else:
            rewards.append(0.0)
    return rewards
