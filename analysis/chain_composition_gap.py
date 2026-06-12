"""Composition-gap analysis for depth-1 chain diagnostics.

Reads a calibration JSON produced by tools/sample.py over a depth-1 chain pool
(rows carry chain.intermediate_gold per #46) and reports, per composite:

  - problem-level mean pass_rate and zone distribution
  - rollout-level intermediate_hit_rate: did the rollout text contain the
    step-A (feeder) answer?
  - the composition gap: P(pass | intermediate hit) vs P(pass | miss), and the
    hit-but-fail fraction — rollouts that computed the atom but failed the
    composite. High hit rate + low pass rate = the model can do the steps but
    cannot chain them, which is the signal depth-1 training targets.

Hit detection is text containment with numeric word boundaries. For
chain_constrained_divisor_count__modular_exponent the intermediate values are
small (4-20) and incidental matches inflate the loose rate, so a strict
chain-aware detector (a^{e} usage, or an explicit "e = <ig>") is reported
alongside; on the 06-12 n=300 run it moves the hit rate 0.856 -> 0.790 without
changing the conclusion.

Usage: python analysis/chain_composition_gap.py data/chain_depth1_base_diag_300.json
"""

import ast
import json
import re
import sys
from collections import defaultdict


def rollout_texts(row):
    t = row["rollout_texts"]
    return ast.literal_eval(t) if isinstance(t, str) else t


def loose_pattern(ig):
    return re.compile(r"(?<![\d.])" + re.escape(str(ig)) + r"(?![\d.])")


def strict_pattern_cdc_modexp(row):
    """Strict detector for the #55 chain: the fed param is the exponent."""
    ig, a = str(row["chain"]["intermediate_gold"]), str(row["knobs"]["a"])
    return re.compile(
        re.escape(a) + r"\^\{?" + re.escape(ig) + r"\}?(?!\d)"
        + r"|[a-zA-Z]\s*=\s*" + re.escape(ig) + r"(?!\d)"
        + r"|divisors[^.]{0,80}?(?:is|are|:)\s*\\?\[?\s*" + re.escape(ig) + r"(?!\d)"
    )


STRICT_DETECTORS = {
    "chain_constrained_divisor_count__modular_exponent": strict_pattern_cdc_modexp,
}


def analyze(rows, detector="loose"):
    agg = defaultdict(lambda: defaultdict(int))
    pass_sums = defaultdict(float)
    zones = defaultdict(lambda: defaultdict(int))
    for r in rows:
        c = r["skeleton_type"]
        a = agg[c]
        a["n"] += 1
        pass_sums[c] += r["pass_rate"]
        zones[c][r["zone"]] += 1
        pat = loose_pattern(r["chain"]["intermediate_gold"])
        if detector == "strict" and c in STRICT_DETECTORS:
            pat = STRICT_DETECTORS[c](r)
        for t, rew in zip(rollout_texts(r), r["rollout_rewards"]):
            hit, p = bool(pat.search(t)), rew == 1.0
            a["roll_n"] += 1
            a[("hit" if hit else "miss", "pass" if p else "fail")] += 1
    out = {}
    for c, a in agg.items():
        h = a[("hit", "pass")] + a[("hit", "fail")]
        m = a[("miss", "pass")] + a[("miss", "fail")]
        out[c] = {
            "n": a["n"],
            "mean_pass_rate": pass_sums[c] / a["n"],
            "zones": dict(zones[c]),
            "intermediate_hit_rate": h / a["roll_n"],
            "rollout_pass_rate": (a[("hit", "pass")] + a[("miss", "pass")]) / a["roll_n"],
            "p_pass_given_hit": a[("hit", "pass")] / h if h else None,
            "p_pass_given_miss": a[("miss", "pass")] / m if m else None,
            "hit_but_fail_frac": a[("hit", "fail")] / a["roll_n"],
        }
    return out


def main():
    rows = json.load(open(sys.argv[1]))
    rows = [r for r in rows if r.get("depth") == 1 and "chain" in r]
    for detector in ("loose", "strict"):
        print(f"\n===== detector: {detector} =====")
        for c, s in sorted(analyze(rows, detector).items()):
            print(f"\n{c}  (n={s['n']})")
            print(f"  mean pass_rate {s['mean_pass_rate']:.3f}   zones {s['zones']}")
            print(f"  intermediate_hit_rate {s['intermediate_hit_rate']:.3f}   "
                  f"rollout pass {s['rollout_pass_rate']:.3f}   "
                  f"gap {s['intermediate_hit_rate'] - s['rollout_pass_rate']:+.3f}")
            print(f"  P(pass|hit) {s['p_pass_given_hit']:.3f}   "
                  f"P(pass|miss) {s['p_pass_given_miss']:.3f}   "
                  f"hit-but-fail {s['hit_but_fail_frac']:.1%}")
    gl = sum(1 for r in rows if r["zone"] == "goldilocks")
    print(f"\nOVERALL: {len(rows)} problems, mean pass "
          f"{sum(r['pass_rate'] for r in rows) / len(rows):.3f}, goldilocks {gl}")


if __name__ == "__main__":
    main()
