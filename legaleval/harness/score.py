"""Scoring stage: deterministic math, no LLM.

    python -m harness.score runs/<run_id>

Per LegalEval v6 §6.2: raw dimension total -> normalize to prompt max ->
cap at 0.40 on any gate trip. Emits results/<run_id>_<judge>.csv per judge
plus a human-confirm queue.

Reporting design:
  - The HEADLINE is a pair, not a blend: gate-trip rate (the floor — is the
    output safe?) and quality-given-pass (the ceiling — how good when safe?).
    The capped blend is also printed but mixes the two questions.
  - Weighting is stated explicitly: equal-per-prompt (each prompt counts the
    same) is primary; points-weighted (a /16 prompt worth ~1.8x a /9) is
    printed alongside. They can rank models differently.
  - 95% CI by cluster bootstrap over source contracts — 9 of 14 prompts share
    one underlying MSA, so per-prompt scores are not independent.
  - Cross-judge: when 2+ judge families have graded the run, gate
    disagreements are printed and routed to the confirm queue.
  - Tier 0 deterministic flags (B1/D2/D3) route to the confirm queue.
"""

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE_CAP = 0.40
DIMENSIONS = ["faithfulness", "directionality", "coverage", "soundness", "actionability"]
GATES = ("gate_faithfulness", "gate_directionality")


def score_one(grade: dict, max_points: float) -> dict:
    agg = grade["aggregate"]
    raw = sum(agg[d] for d in DIMENSIONS)
    norm = raw / max_points
    tripped = [g for g in GATES if agg[g]["tripped"]]
    precision = agg.get("precision")
    return {
        "raw": raw,
        "max": max_points,
        "norm_uncapped": round(norm, 4),
        "norm": round(min(norm, GATE_CAP) if tripped else norm, 4),
        "gates_tripped": tripped,
        "capped": bool(tripped) and norm > GATE_CAP,
        "precision": round(precision, 4) if precision is not None else None,
        "needs_human_confirm": any(agg[g]["needs_human_confirm"] for g in GATES),
        "tier0_flags": (grade.get("tier0") or {}).get("flags", []),
    }


def load_grades(run_dir: Path) -> dict[str, list[dict]]:
    """Group grade records by judge. Supports grades/<judge>/*.json and the
    legacy flat grades/*.json layout."""
    by_judge: dict[str, list[dict]] = defaultdict(list)
    grades_root = run_dir / "grades"
    for path in sorted(grades_root.rglob("*.json")):
        grade = json.loads(path.read_text())
        judge = path.parent.name if path.parent != grades_root \
            else grade.get("judge_model", "unknown")
        grade["_file"] = str(path.relative_to(run_dir))
        by_judge[judge].append(grade)
    return dict(by_judge)


def cluster_bootstrap_ci(cell_means: dict[str, float], clusters: dict[str, list[str]],
                         n_boot: int = 2000, seed: int = 0) -> tuple[float, float] | None:
    """95% CI for the equal-per-prompt mean, resampling source contracts."""
    contracts = sorted(c for c, pids in clusters.items()
                       if any(p in cell_means for p in pids))
    if len(contracts) < 2:
        return None
    rng = random.Random(seed)
    stats = []
    for _ in range(n_boot):
        draw = [rng.choice(contracts) for _ in contracts]
        vals = [cell_means[p] for c in draw for p in clusters[c] if p in cell_means]
        if vals:
            stats.append(sum(vals) / len(vals))
    stats.sort()
    return stats[int(0.025 * len(stats))], stats[int(0.975 * len(stats))]


def summarize(rows: list[dict], clusters: dict[str, list[str]]) -> dict[str, dict]:
    """Per-model summary from per-sample rows."""
    by_model: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_model[r["provider"]].append(r)
    out = {}
    for model, rs in by_model.items():
        passed = [r for r in rs if not r["gates_tripped"]]
        # equal-per-prompt: mean over samples within a prompt, then over prompts
        per_prompt: dict[str, list[float]] = defaultdict(list)
        for r in rs:
            per_prompt[r["prompt_id"]].append(r["norm"])
        cell_means = {p: sum(v) / len(v) for p, v in per_prompt.items()}
        blended_equal = sum(cell_means.values()) / len(cell_means)
        prec = [r["precision"] for r in rs if r["precision"] is not None]
        out[model] = {
            "samples": len(rs),
            "prompts": len(cell_means),
            "gate_trip_rate": sum(bool(r["gates_tripped"]) for r in rs) / len(rs),
            "quality_given_pass": (sum(r["norm_uncapped"] for r in passed) / len(passed)
                                   if passed else None),
            "mean_precision": sum(prec) / len(prec) if prec else None,  # v7 §6.2a
            "blended_equal_prompt": blended_equal,
            "blended_points_weighted": sum(r["raw"] for r in rs) / sum(r["max"] for r in rs),
            "ci95_equal_prompt": cluster_bootstrap_ci(cell_means, clusters),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    args = ap.parse_args()

    suite = json.loads((ROOT / "suite" / "prompts.json").read_text())
    max_points = {p["id"]: p["max_points"] for p in suite["prompts"]}
    clusters: dict[str, list[str]] = defaultdict(list)
    for p in suite["prompts"]:
        clusters[p.get("source_contract", "unknown")].append(p["id"])

    by_judge = load_grades(args.run_dir)
    if not by_judge:
        raise SystemExit(f"no grades found under {args.run_dir / 'grades'}")

    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    run_id = args.run_dir.name

    confirm_queue, rows_by_judge = [], {}
    for judge, grades in by_judge.items():
        rows = []
        for grade in grades:
            s = score_one(grade, max_points[grade["prompt_id"]])
            rows.append({
                "prompt_id": grade["prompt_id"],
                "provider": grade["provider"],
                "sample": grade.get("sample", 0),
                **{k: s[k] for k in ("raw", "max", "norm_uncapped", "norm",
                                     "capped", "precision")},
                "gates_tripped": ";".join(s["gates_tripped"]),
                "tier0_flags": ";".join(s["tier0_flags"]),
                "_gates": s["gates_tripped"], "_file": grade["_file"],
            })
            if s["needs_human_confirm"] or s["gates_tripped"] or s["tier0_flags"]:
                confirm_queue.append({
                    "judge": judge, "file": grade["_file"],
                    **{k: s[k] for k in ("norm", "gates_tripped",
                                         "needs_human_confirm", "tier0_flags")},
                })
        rows_by_judge[judge] = rows

        csv_path = results_dir / f"{run_id}_{judge.replace('/', '-')}.csv"
        public = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(public[0].keys()))
            writer.writeheader()
            writer.writerows(public)
        print(f"[{judge}] score matrix -> {csv_path}")

        summary = summarize(rows, clusters)
        order = sorted(summary, key=lambda m: -(summary[m]["blended_equal_prompt"]))
        print(f"[{judge}] {'model':24s} {'gate-trip':>9s} {'qual|pass':>9s} "
              f"{'precision':>9s} {'eq-prompt':>9s} {'pts-wtd':>8s}  95% CI (cluster)")
        for model in order:
            s = summary[model]
            qual = f"{s['quality_given_pass']:.3f}" if s["quality_given_pass"] is not None else "  n/a"
            prec = f"{s['mean_precision']:.3f}" if s["mean_precision"] is not None else "  n/a"
            ci = (f"[{s['ci95_equal_prompt'][0]:.3f}, {s['ci95_equal_prompt'][1]:.3f}]"
                  if s["ci95_equal_prompt"] else "n/a")
            print(f"  {model:24s} {s['gate_trip_rate']:>8.0%} {qual:>9s} {prec:>9s} "
                  f"{s['blended_equal_prompt']:>9.3f} {s['blended_points_weighted']:>8.3f}  {ci}")
        print()

    # cross-judge gate disagreements (criterion-contamination / self-preference control)
    if len(rows_by_judge) >= 2:
        keyed = {j: {(r["prompt_id"], r["provider"], r["sample"]): set(r["_gates"])
                     for r in rows} for j, rows in rows_by_judge.items()}
        judges = sorted(keyed)
        disagreements = 0
        for key in sorted(set.intersection(*(set(k) for k in keyed.values()))):
            verdicts = {j: keyed[j][key] for j in judges}
            if len({frozenset(v) for v in verdicts.values()}) > 1:
                disagreements += 1
                confirm_queue.append({
                    "judge": "CROSS-JUDGE DISAGREEMENT",
                    "item": list(key),
                    "gate_verdicts": {j: sorted(v) for j, v in verdicts.items()},
                })
                print(f"cross-judge gate disagreement {key}: "
                      + "; ".join(f"{j}={sorted(v) or 'clean'}" for j, v in verdicts.items()))
        print(f"cross-judge: {disagreements} gate disagreement(s) "
              f"across {len(judges)} judges\n")

    queue_path = results_dir / f"{run_id}_confirm_queue.json"
    queue_path.write_text(json.dumps(confirm_queue, indent=2))
    print(f"human-confirm queue ({len(confirm_queue)}) -> {queue_path}")


if __name__ == "__main__":
    main()
