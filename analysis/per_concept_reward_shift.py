#!/usr/bin/env python3
"""
per_concept_reward_shift.py — attribute a GRPO run's logged completions to their concepts
and measure each concept's reward shift from EARLY to LATE training.

This is the diagnostic behind the depth-0 INTERFERENCE finding (DAILY LOG 06-18): on the v12
28-concept run the flat aggregate train reward HIDES an 8-up/8-down tug-of-war — early-mastered
concepts DEGRADE on their own training data (modexp 0.88->0.55, divisor_sum 0.85->0.56) while
hard ones CLIMB (alternating_cubes 0.25->0.78), netting flat + peaking ~step 50. A concept
getting worse at its OWN training data is the optimizer actively degrading it (capacity
competition in the rank-32 LoRA), NOT under-fitting (that rises from low) or over-fit (train stays
high). This script is what produced the per-concept chart.

INPUT: a directory of log_completions parquets (cols: step, prompt, completion, correctness_reward,
format_reward, advantage). Current TRL logs completions to W&B (not local parquets), and a box's
./training_completions/ dir is NOT run-scoped — it can hold a PRIOR run's stale parquets (it bit us:
a trio pull came back as a stale 28-concept run). So get a RUN-SCOPED dir first via
tools/fetch_wandb_completions.py <entity>/<project>/<run_id> (writes the run's rows), then point this
at that — do NOT read a reused box's training_completions/. Concept attribution: each prompt's problem
text is matched (exact, then numbers->'#' template) against every data/*.json that carries skeleton_type.

  python3 analysis/per_concept_reward_shift.py <completions_dir> [--out results/x.json] [--md results/x.md]

Reusable on ANY run (depth-0, the trio, depth-1) to read per-concept trajectories offline without W&B.
"""
import os, re, json, glob, argparse
from collections import defaultdict
import pyarrow.parquet as pq

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(t):
    t = re.sub(r"-?\d+(?:\.\d+)?", "#", t)
    return re.sub(r"\s+", " ", t).strip()


def build_concept_maps():
    """problem-text -> skeleton_type, from every dataset that carries it (exact + template)."""
    exact, tmpl = {}, {}
    for f in glob.glob(os.path.join(REPO, "data", "*.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if isinstance(d, list) and d and isinstance(d[0], dict) and "skeleton_type" in d[0] and "problem" in d[0]:
            for r in d:
                exact[r["problem"]] = r["skeleton_type"]
                tmpl.setdefault(norm(r["problem"]), r["skeleton_type"])
    return exact, tmpl


def concept_of(prompt, exact, tmpl):
    body = prompt.split("\nuser\n", 1)[-1].split("\nassistant", 1)[0].strip()
    return exact.get(body) or tmpl.get(norm(body), "?")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("completions_dir", help="dir of log_completions *.parquet")
    ap.add_argument("--out", help="write the per-concept data as JSON")
    ap.add_argument("--md", help="write a markdown table")
    a = ap.parse_args()

    exact, tmpl = build_concept_maps()
    rows = []  # (step, concept, pass[0/1])
    for f in sorted(glob.glob(os.path.join(a.completions_dir, "*.parquet"))):
        t = pq.read_table(f).to_pydict()
        for st, pr, cr in zip(t["step"], t["prompt"], t["correctness_reward"]):
            rows.append((st, concept_of(pr, exact, tmpl), 1.0 if cr and cr >= 0.5 else 0.0))
    if not rows:
        raise SystemExit(f"no parquets found in {a.completions_dir}")

    maxstep = max(s for s, _, _ in rows)
    third = max(1, maxstep // 3)
    early, late = defaultdict(list), defaultdict(list)
    for s, c, v in rows:
        if c == "?":
            continue
        if s <= third:
            early[c].append(v)
        elif s > maxstep - third:
            late[c].append(v)

    res = []
    for c in sorted(set(list(early) + list(late))):
        e, l = early.get(c, []), late.get(c, [])
        me = round(sum(e) / len(e), 3) if e else None
        ml = round(sum(l) / len(l), 3) if l else None
        res.append(dict(concept=c, early=me, late=ml,
                        delta=(round(ml - me, 3) if (me is not None and ml is not None) else None),
                        n_early=len(e), n_late=len(l)))
    res.sort(key=lambda r: (r["delta"] is None, r["delta"] if r["delta"] is not None else 0))

    unmatched = sum(1 for s, c, v in rows if c == "?")
    summary = dict(run=os.path.basename(a.completions_dir.rstrip("/")), n_rollouts=len(rows),
                   unmatched=unmatched, max_step=maxstep,
                   early_window=[1, third], late_window=[maxstep - third + 1, maxstep])
    out = dict(summary=summary, concepts=res)
    if a.out:
        json.dump(out, open(a.out, "w"), indent=2)

    lines = [f"# per-concept reward shift — {summary['run']} ({len(rows)} rollouts, {maxstep} steps)",
             f"early = steps 1-{third}, late = steps {maxstep - third + 1}-{maxstep}; "
             f"reward = correctness (thresholded >=0.5); sorted by delta (decliners first).",
             "", "| concept | early | late | delta | nE/nL |", "|---|--|--|--|--|"]
    for r in res:
        if r["delta"] is None:
            ds, arrow = "—", ""
        else:
            ds = f"{r['delta']:+.2f}"
            arrow = " DOWN" if r["delta"] < -0.03 else (" UP" if r["delta"] > 0.03 else " flat")
        lines.append(f"| {r['concept']} | {r['early']} | {r['late']} | {ds}{arrow} | {r['n_early']}/{r['n_late']} |")
    md = "\n".join(lines)
    if a.md:
        open(a.md, "w").write(md + "\n")
    print(md if not a.md else f"{summary['run']}: {len(res)} concepts, {unmatched} unmatched -> {a.out or '(stdout)'}")


if __name__ == "__main__":
    main()
