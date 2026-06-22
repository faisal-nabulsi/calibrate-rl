#!/usr/bin/env python3
"""
amc_failure_conversion.py — THE validation gate for depth-1.5 / depth-2.0.

The depth-1 trap: chain held-out pass-rate rises trivially via execution reliability and tells
us NOTHING about whether we moved the AMC failures. The only honest signal is: of the AMC problems
that FAILED before, how many CONVERT to solved after — BROKEN DOWN BY FAILURE SUB-MODE. If the
fabrication fails convert but the execution-slips don't (or vice versa), we know which lever worked
and which reduced to depth-0's capped one.

Buckets each AMC failure by sub-mode (heuristic over the transcript), then reports per-bucket
conversion before->after. Run after each new checkpoint's AMC eval.

Usage: python3 analysis/amc_failure_conversion.py <before.json> <after.json>
  (each = eval_amc_baseline.py output: list of {problem_id, gold_answer, predicted_answer,
   correct, model_response})
"""
import sys, json
from collections import Counter, defaultdict

_FAB_PHRASES = ["by trial and error", "it is known", "known to be", "we know it is", "we find that",
                "are consistent", "by symmetry", "it is clear", "it can be shown", "by inspection",
                "well-known", "by direct computation", "obvious", "it follows that"]

def classify(r):
    """Sub-mode of a FAILED AMC rollout. Heuristic, but stable + auditable:
    nonterm (no answer) | exec_slip (right method, |err|<=2) | fabrication (assertion phrase, or a
    plausible far-off number after a long derivation) | recognition (far-off, no assertion tell)."""
    pred, gold, resp = r.get("predicted_answer"), r.get("gold_answer"), r.get("model_response", "")
    if pred in (None, "None", ""):
        return "nonterm"
    low = resp.lower()
    fab = any(p in low for p in _FAB_PHRASES)
    try:
        err = abs(float(pred) - float(gold))
    except (TypeError, ValueError):
        err = None
    if err is not None and err <= 2 and not fab:
        return "exec_slip"          # right method, terminal arithmetic/enumeration slip
    if fab:
        return "fabrication"        # asserted a number instead of finishing
    if err is not None and err <= 2:
        return "exec_slip"
    return "recognition"            # wrong structure from the start (far-off, no assertion tell)

def main():
    if len(sys.argv) < 3:
        sys.exit("usage: amc_failure_conversion.py <before.json> <after.json>")
    before = {r["problem_id"]: r for r in json.load(open(sys.argv[1]))}
    after = {r["problem_id"]: r for r in json.load(open(sys.argv[2]))}
    b_solved = sum(1 for r in before.values() if r.get("correct"))
    a_solved = sum(1 for r in after.values() if r.get("correct"))
    n = len(before)
    print(f"AMC: before {b_solved}/{n}  ->  after {a_solved}/{n}   (net {a_solved-b_solved:+d})\n")

    # for each BEFORE-failure, its sub-mode + whether it converted (solved after)
    by_mode = defaultdict(lambda: {"n": 0, "converted": 0, "pids_fixed": [], "pids_still": []})
    regressed = []
    for pid, rb in before.items():
        ra = after.get(pid, {})
        if rb.get("correct"):
            if not ra.get("correct"):
                regressed.append(pid)
            continue
        mode = classify(rb)
        by_mode[mode]["n"] += 1
        if ra.get("correct"):
            by_mode[mode]["converted"] += 1
            by_mode[mode]["pids_fixed"].append(pid)
        else:
            by_mode[mode]["pids_still"].append(pid)

    print(f"{'sub-mode':14} {'failed':>7} {'converted':>10} {'rate':>7}   fixed pids")
    order = ["exec_slip", "fabrication", "recognition", "nonterm"]
    tot_n = tot_c = 0
    for m in order:
        d = by_mode.get(m)
        if not d:
            continue
        tot_n += d["n"]; tot_c += d["converted"]
        rate = d["converted"] / d["n"] if d["n"] else 0
        print(f"{m:14} {d['n']:>7} {d['converted']:>10} {rate:>6.0%}   {d['pids_fixed']}")
    print(f"{'TOTAL':14} {tot_n:>7} {tot_c:>10} {(tot_c/tot_n if tot_n else 0):>6.0%}")
    if regressed:
        print(f"\nREGRESSED (solved before, failed after): {regressed}")
    print("\nGATE READ: did the targeted sub-modes convert? execution-slip conversion validates the "
          "finish-bound lever; fabrication conversion validates the no-solution oracle. If a targeted "
          "mode's rate is ~0, that lever reduced to depth-0's capped one — pivot, don't ship.")

if __name__ == "__main__":
    main()
