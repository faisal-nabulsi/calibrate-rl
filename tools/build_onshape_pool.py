#!/usr/bin/env python3
"""
build_onshape_pool.py — build an ON-SHAPE calibration pool of REAL AMC problems with PUBLISHED answers
(the "published-key" path: gold is the answer key, NOT an oracle we compute — sidesteps the missing
free-form grader, our hardest unbuilt piece).

SAME SOURCE AS THE TEST, by design. The 83-problem test (AI-MO/aimo-validation-amc) is AMC12 2022+2023,
adapted to integer answers. So we keep training STRICTLY to AMC (NOT AIME — AIME is harder + a different
distribution, which would reintroduce the train!=test shape mismatch this whole program is trying to remove).
Source = NuminaMath (AI-MO's own corpus, same family), filtered to AMC problems, deduped vs the 83 test
problems. Excludes AIME explicitly.

This is also a DISCOVERY pass: it prints the corpus's source-field distribution so we can confirm the AMC
filter is clean before trusting the pool. Keeps the published answer as-is (the reward_func does math-
equivalence, not integer-only), but requires a parseable numeric answer for reliable exact grading.

Runs ON A BOX (needs `datasets` + HF; local pip is sandboxed). Dispatched as an `eval`-type job.

Usage (on a box):  python tools/build_onshape_pool.py --out onshape_amc_pool.json
"""
import argparse, json, re, sys, os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "eval"))


def _field(r, *names):
    for n in names:
        if n in r and r[n] not in (None, ""):
            return r[n]
    return None


_CHOICE_A = re.compile(r'(?:\$\s*)?(?:\\(?:textbf|text|mathbf|mathrm)\b\s*)?\{?\s*\(\s*A\s*\)')

def _strip_choices(prob):
    """AMC = multiple-choice (has (A) followed by (B) and (C)); AIME = free-response (no choices).
    Returns the problem STEM with the choice block removed (free-response, matching the test) if it's
    multiple-choice; else None (so AIME/non-MC rows are dropped)."""
    for mm in _CHOICE_A.finditer(prob):
        rest = prob[mm.start():]
        if re.search(r'\(\s*B\s*\)', rest) and re.search(r'\(\s*C\s*\)', rest):
            stem = prob[:mm.start()].rstrip()
            stem = re.sub(r'[\$\\{}\s]+$', '', stem).rstrip()
            stem = re.sub(r'(?:\bis\b|:|=|\bequals\b)\s*$', '', stem).rstrip()
            return stem if len(stem) > 15 else None
    return None

def _norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="onshape_amc_pool.json")
    ap.add_argument("--sources", default="AI-MO/NuminaMath-1.5")   # AI-MO corpus, same family as the test
    ap.add_argument("--amc-only", type=int, default=1)             # 1 = keep AMC, drop AIME/others
    ap.add_argument("--max", type=int, default=0)
    a = ap.parse_args()
    from datasets import load_dataset

    try:
        from holdout_eval import load_amc
        amc_probs = {p["problem"].strip() for p in load_amc()}
        print(f"loaded {len(amc_probs)} AMC test problems to dedup against", flush=True)
    except Exception as e:
        amc_probs = set(); print(f"WARN: no AMC dedup ({e})", flush=True)
    # Dedup on the NORMALIZED, CHOICE-STRIPPED form: NuminaMath stores AMC as multiple-choice while the 83
    # test problems are free-response (choices removed), so a raw text-match misses the overlap. (Caught 56
    # of the 83 test problems leaking through as MC otherwise.)
    test_full = {_norm(p) for p in amc_probs}
    test_pref = {_norm(p)[:60] for p in amc_probs}

    rows, seen = [], set()
    for src in [s.strip() for s in a.sources.split(",") if s.strip()]:
        try:
            ds = load_dataset(src, split="train")
        except Exception as e:
            print(f"!! {src}: load failed: {str(e)[:140]}", flush=True); continue
        fields = list(ds[0].keys())
        print(f"{src}: {len(ds)} rows | fields={fields}", flush=True)
        # DISCOVERY: report the source-field distribution so the AMC filter is auditable
        sfield = next((f for f in ("source", "problem_source", "competition", "type") if f in fields), None)
        if sfield:
            dist = Counter(str(r.get(sfield)) for r in ds)
            print(f"  source-field '{sfield}' distribution (top 15): {dist.most_common(15)}", flush=True)
        kept = 0
        for r in ds:
            prob = _field(r, "problem", "question", "Problem")
            ans = _field(r, "answer", "Answer", "solution_answer", "final_answer")
            if prob is None or ans is None:
                continue
            src_tag = str(r.get(sfield)).lower() if sfield else ""
            if a.amc_only and "amc" not in src_tag:           # amc_aime is the AMC-bearing source
                continue
            stem = _strip_choices(prob)                        # MC-only (=AMC, drops AIME); strip -> free-response
            if stem is None:
                continue
            ans_s = str(ans).strip()
            if not re.fullmatch(r"-?\d+(?:/\d+)?", ans_s):    # whole answer numeric -> clean exact grade
                continue
            nk = _norm(stem)
            if nk in test_full or nk[:60] in test_pref or nk in seen:   # dedup vs the 83 (normalized) + within-pool
                continue
            seen.add(nk)
            rows.append({"problem": stem, "answer": ans_s,
                         "skeleton_type": "onshape_amc", "depth": 2})
            kept += 1
        print(f"  kept {kept} AMC, numeric-answer, disjoint problems from {src}", flush=True)

    if a.max and len(rows) > a.max:
        rows = rows[:a.max]
    json.dump(rows, open(a.out, "w"), indent=2)
    print(f"\nbuilt {len(rows)} on-shape AMC problems -> {a.out}", flush=True)
    if rows:
        cc = Counter(r["answer"] for r in rows)
        print(f"distinct answers={len(cc)} | top3={cc.most_common(3)}", flush=True)
        print("example:", rows[0]["problem"][:120], "-> gold", rows[0]["answer"], flush=True)


if __name__ == "__main__":
    main()
