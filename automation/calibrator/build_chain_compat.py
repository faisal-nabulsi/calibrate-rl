#!/usr/bin/env python3
"""
build_chain_compat.py — static (A, B, param) chain-compatibility map for depth-1.

For every ordered pair of knob-wired concepts (A feeds B) and every param of B,
answers: would A's gold-answer distribution land inside B's knob ENVELOPE if the
chain "A's answer parameterizes B" were built? Purely static — knobs/*.json plus
the calibration gold answers (the PR-2 report's source data); no GPU, no model.

A param is FEEDABLE only if a scalar integer can legally become its value:
  randint      — A's answer replaces the draw; legal iff inside the envelope.
  choice       — legal iff the pool is scalar-numeric and the answer fits the
                 numeric envelope. Categorical pools (strings) and structured
                 pools (lists, e.g. divisor_triples) are not scalar-feedable.
  const        — never feedable: the value is a [lo,hi] range constant, not a
                 per-problem draw.

Because the chain generator can RESAMPLE A until its answer fits B's envelope,
partial containment is usable. A (A, B, param) edge is `valid` iff
  frac_in_envelope >= MIN_FRAC_IN_ENVELOPE   (resampling isn't degenerate) and
  distinct_in_envelope >= MIN_DISTINCT       (no intermediate-collapse: the v2
                                              failure of 4-distinct-value steps).

Caveat recorded in the artifact: A-answer stats come from the ~9-24 calib
problems per concept, so fractions are coarse. The map is a pruning device for
design review, not a guarantee — every composite still gets calibrated by the
loop like any concept.

Usage:
    python3 automation/calibrator/build_chain_compat.py \
        --calib data/calib_v12_2048_7B.json \
        --out data/chain_compat_v1.json
"""
import argparse
import json
import os
import statistics
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
KNOB_DIR = os.path.join(HERE, "knobs")

SCHEMA_VERSION = 1
MIN_FRAC_IN_ENVELOPE = 0.5
MIN_DISTINCT = 5

# §5/§6 transfer targets: AMC #55 = modular_exponent x constrained_divisor_count
# x divisor_sum_filter; #75 = constrained_divisor_count x prime_power_divisors.
# Of those ingredients only constrained_divisor_count is knob-wired today, so a
# pair is tagged when it includes it; the missing partners are listed so the
# gap is explicit in the artifact.
AMC_TARGET_CONCEPTS = {"constrained_divisor_count": [55, 75]}
AMC_MISSING_PARTNERS = ["modular_exponent", "divisor_sum_filter", "prime_power_divisors"]


def load_knobs():
    knobs = {}
    for fn in sorted(os.listdir(KNOB_DIR)):
        if fn.endswith(".json"):
            with open(os.path.join(KNOB_DIR, fn)) as f:
                knobs[fn[:-5]] = json.load(f)
    return knobs


def gold_answers(calib_rows, concept):
    """Integer golds for one concept; non-integer golds are counted, not fed."""
    vals, non_int = [], 0
    for r in calib_rows:
        if r.get("skeleton_type") != concept:
            continue
        try:
            vals.append(int(str(r["gold"])))
        except (ValueError, TypeError):
            non_int += 1
    return vals, non_int


def feed_target(spec):
    """(feedable, envelope_or_None, reason)."""
    t, env, val = spec["type"], spec["envelope"], spec["value"]
    if t == "const":
        return False, None, "const: range-valued constant, not a per-problem draw"
    if t == "randint":
        return True, env, None
    # choice: scalar-numeric pools only
    if all(isinstance(e, str) for e in env):
        return False, None, "categorical pool (strings), no scalar feed"
    if any(isinstance(o, (list, tuple)) for o in val):
        return False, None, "structured options (tuples), no scalar feed"
    return True, env, None


def pair_entry(a_vals, spec, env):
    lo, hi = env
    inside = [v for v in a_vals if lo <= v <= hi]
    frac = round(len(inside) / len(a_vals), 4) if a_vals else 0.0
    distinct = len(set(inside))
    return {
        "frac_in_envelope": frac,
        "n_answers": len(a_vals),
        "n_in_envelope": len(inside),
        "distinct_in_envelope": distinct,
        "envelope": list(env),
        "param_type": spec["type"],
        "knob_class": spec["knob_class"],
        "valid": frac >= MIN_FRAC_IN_ENVELOPE and distinct >= MIN_DISTINCT,
    }


def concept_summary(calib_rows, concept, vals, non_int):
    rs = [r for r in calib_rows if r.get("skeleton_type") == concept]
    zones = Counter(r["zone"] for r in rs)
    return {
        "n_calib_problems": len(rs),
        "mean_pass_rate": round(
            sum(r["pass_rate"] for r in rs) / len(rs), 4) if rs else None,
        "zone_frac": {z: round(c / len(rs), 4) for z, c in sorted(zones.items())},
        "answers": {
            "n": len(vals),
            "n_non_int": non_int,
            "min": min(vals) if vals else None,
            "max": max(vals) if vals else None,
            "median": statistics.median(vals) if vals else None,
            "distinct": len(set(vals)),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calib", default="data/calib_v12_2048_7B.json")
    ap.add_argument("--out", default="data/chain_compat_v1.json")
    args = ap.parse_args()

    knobs = load_knobs()
    calib_rows = json.load(open(args.calib))

    answers, concepts = {}, {}
    for c in knobs:
        vals, non_int = gold_answers(calib_rows, c)
        answers[c] = vals
        concepts[c] = concept_summary(calib_rows, c, vals, non_int)

    pairs = []
    for a in sorted(knobs):
        if not answers[a]:
            continue
        for b in sorted(knobs):
            if a == b:
                continue
            for pname, spec in knobs[b]["params"].items():
                feedable, env, reason = feed_target(spec)
                entry = {"A": a, "B": b, "param": pname, "feedable": feedable}
                if feedable:
                    entry.update(pair_entry(answers[a], spec, env))
                else:
                    entry["reason"] = reason
                if a in AMC_TARGET_CONCEPTS or b in AMC_TARGET_CONCEPTS:
                    entry["amc_targets"] = sorted(
                        set(AMC_TARGET_CONCEPTS.get(a, [])
                            + AMC_TARGET_CONCEPTS.get(b, [])))
                pairs.append(entry)

    valid = [p for p in pairs if p.get("valid")]
    report = {
        "schema_version": SCHEMA_VERSION,
        "calib_file": args.calib,
        "knob_dir": "automation/calibrator/knobs",
        "rules": {
            "min_frac_in_envelope": MIN_FRAC_IN_ENVELOPE,
            "min_distinct_in_envelope": MIN_DISTINCT,
            "note": ("frac < 1.0 is usable because the chain generator resamples "
                     "A until its answer fits B's envelope; distinct guards the "
                     "v2 intermediate-collapse failure. Answer stats come from "
                     "the per-concept calib sample (~9-24 problems) — coarse. "
                     "frac/distinct_in_envelope measure FEED diversity (what can "
                     "legally flow into B's param), not the composite's ANSWER "
                     "diversity: for choice params the envelope, not the curated "
                     "pool, is the legality wall, so chains may feed values the "
                     "pool never produces, and a large fed threshold can still "
                     "collapse B's answer to a near-constant small count. "
                     "Composite calibration + the static entropy gate are the "
                     "checks on answer diversity."),
        },
        "semantic_caveats": [
            {"target": "constrained_divisor_count.num_pool",
             "note": ("pool is curated highly-composite numbers; the envelope "
                      "admits any integer in [60, 2520], but feeding e.g. a "
                      "prime collapses the divisor structure to a degenerate "
                      "problem. A composite using this edge must resample A "
                      "until the fed value has rich divisor structure (or the "
                      "loop will see ghosts).")},
            {"target": "constrained_divisor_count.gt_thresholds/lt_thresholds",
             "note": ("param is dead unless cond draws the matching branch: the "
                      "generator picks cond in {odd,gt,lt} and only reads "
                      "gt_thresholds when cond=gt (resp. lt) — see "
                      "skeleton_injector_v11.py c_divfilter. A chain feeding "
                      "these params must LOCK cond to the consuming branch in "
                      "the composite's knob file, or ~2/3 of generated problems "
                      "silently ignore the fed value (surface text references "
                      "A's quantity, gold does not — wrong training data that "
                      "looks chained).")},
        ],
        "amc_transfer_note": {
            "targets": {"55": ["modular_exponent", "constrained_divisor_count",
                               "divisor_sum_filter"],
                        "75": ["constrained_divisor_count", "prime_power_divisors"]},
            "knob_wired_today": sorted(knobs),
            "missing_partners": AMC_MISSING_PARTNERS,
        },
        "concepts": concepts,
        "n_pairs_checked": len(pairs),
        "n_valid": len(valid),
        "valid_pairs": [
            {k: p[k] for k in ("A", "B", "param", "frac_in_envelope",
                               "distinct_in_envelope", "knob_class")
             } | ({"amc_targets": p["amc_targets"]} if "amc_targets" in p else {})
            for p in valid
        ],
        "pairs": pairs,
    }

    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)
        f.write("\n")

    print(f"{len(pairs)} (A,B,param) edges checked; {len(valid)} valid")
    for p in valid:
        tag = f"  AMC{p['amc_targets']}" if "amc_targets" in p else ""
        print(f"  {p['A']:28} -> {p['B']}.{p['param']:<18} "
              f"frac={p['frac_in_envelope']:.2f} distinct={p['distinct_in_envelope']}"
              f" [{p['knob_class']}]{tag}")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
