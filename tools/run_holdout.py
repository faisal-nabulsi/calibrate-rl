#!/usr/bin/env python3
"""
Batch-run the base model on the held-out 100 and save graded rollouts for the
UI's Results page (and for the team to read / compare against post-RL).

Default: 8 rollouts/problem at temp 1.0 (shows the distribution + per-problem
pass-rate, the goldilocks signal). Set ROLLOUTS=1 for greedy (temp auto -> 0).

Run (key stays with you, never sent anywhere but the API):
    OPENROUTER_API_KEY=sk-or-... python3 tools/run_holdout.py

Knobs (env): MODEL, BASE_URL, ROLLOUTS, TEMPERATURE, MAX_TOKENS, WORKERS.
Writes tools/holdout_results.json, which the UI serves at /results.
"""
import os, sys, json, ssl, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
from core.reward_func import extract_predicted_answer, extract_gold_answer, _numbers_match
from holdout_eval import SYSTEM_PROMPT

API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("QWEN_API_KEY")
BASE_URL = os.environ.get("BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.environ.get("MODEL", "qwen/qwen-2.5-7b-instruct")
ROLLOUTS = int(os.environ.get("ROLLOUTS", "8"))
TEMPERATURE = float(os.environ.get("TEMPERATURE", "1.0" if ROLLOUTS > 1 else "0.0"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "1024"))
WORKERS = int(os.environ.get("WORKERS", "8"))
OUT = os.path.join(HERE, "holdout_results.json")

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    CTX = ssl.create_default_context()


def call_once(problem):
    payload = {"model": MODEL,
               "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": problem}],
               "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS}
    req = urllib.request.Request(
        BASE_URL.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {API_KEY}"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
                return json.loads(r.read().decode())["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt == 2:
                return f"[ERROR: {type(e).__name__}: {e}]"
            time.sleep(2 * (attempt + 1))


def grade(text, gold):
    pred, method = extract_predicted_answer(text)
    g = extract_gold_answer(str(gold))
    return pred, method, bool(g is not None and pred is not None and _numbers_match(pred, g))


def zone(pr):
    if pr == 0: return "too_hard"
    if pr == 1: return "too_easy"
    if 0.25 <= pr <= 0.75: return "goldilocks"
    return "borderline"


def main():
    if not API_KEY:
        sys.exit("Set OPENROUTER_API_KEY (or QWEN_API_KEY), e.g.\n"
                 "  OPENROUTER_API_KEY=sk-or-... python3 tools/run_holdout.py")
    hold = json.load(open(os.path.join(REPO, "data/goldilocks_holdout_v10.json")))
    hold = sorted(hold, key=lambda r: (r.get("skeleton_type", ""), str(r.get("answer"))))
    total = len(hold) * ROLLOUTS
    print(f"{len(hold)} problems x {ROLLOUTS} rollouts @ temp {TEMPERATURE} via {MODEL} "
          f"({total} calls, {WORKERS} workers)")

    results = [{"concept": r.get("skeleton_type"), "gold": r.get("answer"),
                "problem": r["problem"], "rollouts": []} for r in hold]
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {}
        for i, r in enumerate(hold):
            for _ in range(ROLLOUTS):
                futs[ex.submit(call_once, r["problem"])] = i
        for fut in as_completed(futs):
            i = futs[fut]
            text = fut.result()
            pred, method, correct = grade(text, hold[i]["gold"] if "gold" in hold[i] else hold[i]["answer"])
            results[i]["rollouts"].append({"text": text, "pred": pred,
                                           "method": method, "correct": correct})
            done += 1
            if done % 50 == 0 or done == total:
                print(f"  {done}/{total}", flush=True)

    for r in results:
        r["n"] = len(r["rollouts"])
        r["n_correct"] = sum(1 for x in r["rollouts"] if x["correct"])
        r["pass_rate"] = r["n_correct"] / r["n"] if r["n"] else 0.0
        r["zone"] = zone(r["pass_rate"])

    meta = {"model": MODEL, "rollouts": ROLLOUTS, "temperature": TEMPERATURE,
            "n_problems": len(hold),
            "overall_pass_rate": round(sum(r["n_correct"] for r in results)
                                       / max(1, sum(r["n"] for r in results)), 4),
            "zones": {z: sum(1 for r in results if r["zone"] == z)
                      for z in ("too_hard", "borderline", "goldilocks", "too_easy")},
            "generated_unix": int(time.time())}
    json.dump({"meta": meta, "results": results}, open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT}")
    print(f"overall pass-rate {meta['overall_pass_rate']}  | zones {meta['zones']}")


if __name__ == "__main__":
    main()
