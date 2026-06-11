#!/usr/bin/env python3
"""
static_checks.py — Phase 0, PR 3 of the auto-calibrator plan (design §2c).

CPU-only gate to run AFTER ANY KNOB EDIT, before anything touches a GPU:
generate N (default 200) fresh problems per concept straight from the injector,
then run three checks per concept:

  golds    independent recomputation of every parseable gold via the
           brute-force recomputers in prep/check_dataset.py (where available;
           concepts without a recomputer are reported UNCHECKED, honestly).
           Any mismatch, any conflicting gold (same problem text with two
           different answers), or a recomputer that parses ZERO rows (the gate
           would be claiming verification while verifying nothing) -> FAIL.
  dedupe   survival after dedupe-by-problem-text must be >= 0.90
           (same dedupe as prep/gen_clean.py; low survival = the edit shrank
           the generator's cardinality and the pool will collapse).
  top3     share of the 3 most common answers must be <= 0.30
           (same definition as analyze_calibration.py answer_top3_share;
           guards the answer-hack failure mode: gold%% != answer-diversity,
           see multi_constraint_square / CLAUDE.md CURRENTLY DOING).

Standalone CLI — deliberately NOT wired into any orchestrator yet (§2c).
Exit 0 iff every check on every selected concept passes; nonzero otherwise.
Per-check report goes to stdout.

Usage:
    # default: every concept that has a knob file (the only edit surface)
    python3 automation/calibrator/static_checks.py

    # one concept, or any comma-separated set, or every depth-0 concept
    python3 automation/calibrator/static_checks.py --concept log_laws
    python3 automation/calibrator/static_checks.py --concept all

    # knobs of the run
    ... --n 200 --seed 42 --min-survival 0.90 --max-top3 0.30 \
        --injector generate/skeleton_injector_v12.py

Determinism: each concept is seeded with f"{seed}:{concept}", so checking one
concept reproduces exactly the rows it gets when checking all of them.
"""
import argparse
import importlib.util
import json
import os
import random
import sys
from collections import Counter, defaultdict
from fractions import Fraction

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KNOB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knobs")
DEFAULT_INJECTOR = "generate/skeleton_injector_v12.py"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def knob_concepts():
    """Concepts that have a knob file — the calibrator's only edit surface."""
    return sorted(f[:-5] for f in os.listdir(KNOB_DIR) if f.endswith(".json"))


def generate_rows(inj, concept, n, seed):
    """Generate up to n rows for one concept (same loop shape as gen_clean.py).

    Returns (rows, attempts): rows is what the generator actually produced
    (None returns are retried up to a guard); attempts counts every call.
    """
    random.seed(f"{seed}:{concept}")
    gens = {name: fn for name, fn, _ in inj.REGISTRY}
    fn = gens[concept]
    rows, attempts, guard = [], 0, 0
    while len(rows) < n and guard < n * 200:
        guard += 1
        attempts += 1
        r = fn()
        if r is None:
            continue
        rows.append({"problem": r[0], "answer": str(r[1]), "skeleton_type": concept})
    return rows, attempts


# ── the three §2c checks ─────────────────────────────────────────────────────
# Each returns {"ok": bool|None, "detail": str}. ok=None means UNCHECKED
# (no recomputer exists) — reported, never silently counted as verified.

def check_golds(rows, recomputer):
    """Recompute every parseable gold; compare like check_dataset.py does."""
    # conflicting golds: same problem text carrying 2+ answers (how the
    # continued_fraction bug was found) — fatal regardless of recomputer.
    by_prob = defaultdict(set)
    for r in rows:
        by_prob[r["problem"]].add(str(r["answer"]))
    conflicts = sum(1 for a in by_prob.values() if len(a) > 1)

    if recomputer is None:
        if conflicts:
            return {"ok": False, "detail": f"{conflicts} conflicting golds (no recomputer)"}
        return {"ok": None, "detail": "UNCHECKED — no recomputer in prep/check_dataset.py"}

    checked = 0
    mismatches = []
    seen = set()
    for r in rows:
        if r["problem"] in seen:           # duplicates recompute identically
            continue
        seen.add(r["problem"])
        try:
            got = recomputer(r["problem"])
        except Exception:
            got = None
        if got is None:
            continue
        checked += 1
        try:
            stored = float(Fraction(str(r["answer"])))
        except Exception:
            stored = None
        if stored is None or abs(float(got) - stored) > 1e-6:
            if len(mismatches) < 5:
                mismatches.append((r["answer"], got, r["problem"][:60]))
            else:
                mismatches.append(None)

    n_unique = len(seen)
    cov = f"{checked}/{n_unique} parsed ({checked / n_unique:.0%})" if n_unique else "0/0"
    if conflicts:
        return {"ok": False, "detail": f"{conflicts} conflicting golds; {cov}"}
    if n_unique and checked == 0:
        return {"ok": False,
                "detail": f"{cov} — recomputer parses NOTHING; gate would verify nothing. "
                          "Fix the recomputer or the phrasing before trusting this concept."}
    if mismatches:
        ex = "; ".join(f"stored={s} correct={g} :: {p}" for s, g, p in
                       [m for m in mismatches if m][:3])
        return {"ok": False,
                "detail": f"{len(mismatches)} mismatches over {cov} — e.g. {ex}"}
    return {"ok": True, "detail": f"{cov}, 0 mismatches, 0 conflicting golds"}


def check_dedupe(rows, min_survival):
    raw = len(rows)
    if raw == 0:
        return {"ok": False, "detail": "generator produced 0 rows"}
    unique = len({r["problem"] for r in rows})
    s = unique / raw
    op = ">=" if s >= min_survival else "<"
    return {"ok": s >= min_survival,
            "detail": f"survival {s:.3f} {op} {min_survival} ({unique}/{raw} unique)"}


def top3_share(answers):
    """Same definition as analyze_calibration.py _top3_share (design §2b)."""
    c = Counter(answers)
    tot = sum(c.values())
    if not tot:
        return 0.0
    return sum(n for _, n in c.most_common(3)) / tot


def check_top3(rows, max_top3):
    if not rows:
        return {"ok": False, "detail": "generator produced 0 rows"}
    # measure on deduped rows — duplicates would double-count their answer
    answers = [r["answer"] for r in {r["problem"]: r for r in rows}.values()]
    share = top3_share(answers)
    top = ", ".join(f"{a}×{n}" for a, n in Counter(answers).most_common(3))
    op = "<=" if share <= max_top3 else ">"
    return {"ok": share <= max_top3,
            "detail": f"share {share:.3f} {op} {max_top3} "
                      f"({len(set(answers))} distinct; top: {top})"}


# ── driver ───────────────────────────────────────────────────────────────────

def run_checks(concepts, n, seed, min_survival, max_top3, injector_path):
    """Run the §2c gate. Returns {concept: {check: {ok, detail}, ...}}."""
    inj = _load(os.path.join(REPO, injector_path), "static_checks_injector")
    cd = _load(os.path.join(REPO, "prep/check_dataset.py"), "static_checks_cd")
    registry = {name for name, _, _ in inj.REGISTRY}
    results = {}
    for concept in concepts:
        if concept not in registry:
            results[concept] = {"golds": {"ok": False, "detail": f"unknown concept (not in {injector_path})"},
                                "dedupe": {"ok": False, "detail": "not generated"},
                                "top3": {"ok": False, "detail": "not generated"}}
            continue
        rows, attempts = generate_rows(inj, concept, n, seed)
        res = {
            "golds": check_golds(rows, cd.RECOMPUTERS.get(concept)),
            "dedupe": check_dedupe(rows, min_survival),
            "top3": check_top3(rows, max_top3),
        }
        if attempts > len(rows):
            res["_note"] = f"{attempts - len(rows)} None-returns retried ({attempts} calls for {len(rows)} rows)"
        results[concept] = res
    return results


def report(results, n):
    """Per-check report to stdout. Returns True iff everything passed."""
    ok_all = True
    n_pass = 0
    for concept, res in results.items():
        marks = []
        for check in ("golds", "dedupe", "top3"):
            r = res[check]
            if r["ok"] is False:
                ok_all = False
            tag = "PASS" if r["ok"] else ("UNCHECKED" if r["ok"] is None else "FAIL")
            marks.append((check, tag, r["detail"]))
        c_ok = all(res[c]["ok"] is not False for c in ("golds", "dedupe", "top3"))
        n_pass += c_ok
        print(f"== {concept}  ({n} requested) ==")
        for check, tag, detail in marks:
            print(f"  {check:<7} {tag:<9} {detail}")
        if "_note" in res:
            print(f"  note    {res['_note']}")
    verdict = "PASS" if ok_all else "FAIL"
    print(f"\nSTATIC CHECKS: {verdict} ({n_pass}/{len(results)} concepts clean)")
    return ok_all


def main():
    ap = argparse.ArgumentParser(description="§2c post-knob-edit static gate (CPU-only)")
    ap.add_argument("--concept", default="knobs",
                    help="concept name, comma-separated list, 'knobs' (default: every "
                         "concept with a knob file), or 'all' (every depth-0 concept)")
    ap.add_argument("--n", type=int, default=200, help="problems per concept (default 200)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--min-survival", type=float, default=0.90)
    ap.add_argument("--max-top3", type=float, default=0.30)
    ap.add_argument("--injector", default=os.environ.get("INJECTOR", DEFAULT_INJECTOR))
    args = ap.parse_args()

    if args.concept == "knobs":
        concepts = knob_concepts()
    elif args.concept == "all":
        inj = _load(os.path.join(REPO, args.injector), "static_checks_inj_list")
        concepts = sorted(name for name, _, _ in inj.REGISTRY
                          if name not in inj.DEPTH1_PARTNERS)
    else:
        concepts = [c.strip() for c in args.concept.split(",") if c.strip()]

    results = run_checks(concepts, args.n, args.seed,
                         args.min_survival, args.max_top3, args.injector)
    sys.exit(0 if report(results, args.n) else 1)


if __name__ == "__main__":
    main()
