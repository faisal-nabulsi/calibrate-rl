"""
analyze_calibration.py — turn calibration output into the protocol's Step 7-9 info.
Usage:  python3 analyze_calibration.py ~/data/calib_7B.json [~/data/calib_1.5B.json ...]

Machine-readable report (Phase 0 PR-2, auto-calibrator design §2b):
    python3 analyze_calibration.py data/calib_v11_2048_7B.json \
        --json report.json [--pool data/pool.json]

--json is ADDITIVE: terminal output is unchanged. It emits a per-concept report
(schema agreed with Michael in #calibrate-rl-agents, 2026-06-10) with zone_frac,
pass_rate_hist, answer_top3_share, answer_entropy, truncation_rate,
dedupe_survival, ghost_frac, failure_modes, param_vs_passrate. Requires exactly
one calib file. --pool joins calib rows back to the generation pool by problem
text to read gen_clean's stamped "knobs" metadata (param_vs_passrate) and the
pool's .meta.json gen-stats sidecar (dedupe_survival); without --pool those
fields are null, never a crash.

Field definitions (pinned in the Slack schema agreement):
  truncation_rate   frac of rollouts with NO \\boxed{ in the text. Validated:
                    reproduces the known v10 13.0% (~14%) and v11 0.9% (~1%).
  ghost_frac        frac of problems with pass_rate exactly 0 or 1 (zero
                    within-group variance -> zero GRPO gradient).
  zone_frac         read from the calib rows' existing "zone" field — never
                    re-derived, so the report cannot disagree with the
                    measure script.
  answer_entropy    Shannon entropy (bits) of the gold-answer distribution.
  failure_modes     analyze_gaps.classify_failure on the first wrong rollout
                    per problem (same-problem correct rollout as reference
                    when one exists); fractions over n_classified.
"""
import argparse, json, sys, glob, os, random, math
import numpy as np
from collections import defaultdict, Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:                       # re-derive parse-rate from saved transcripts (F4 / Step 4)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from core.reward_func import extract_predicted_answer
    HAVE_GRADER = True
except Exception:
    HAVE_GRADER = False

SCHEMA_VERSION = 1
ZONES = ("too_easy", "goldilocks", "borderline", "too_hard")


# ── §2b report helpers ──────────────────────────────────────────────────────

def _is_truncated(text):
    """No \\boxed{ in the rollout = it never reached a final answer.

    The only definition computable from calib JSONs (no token counts saved)
    that reproduces the known numbers: v10 calib 13.0%, v11 calib 0.9%.
    """
    return "\\boxed" not in text


def _entropy_bits(counter):
    tot = sum(counter.values())
    if not tot:
        return 0.0
    return -sum((c / tot) * math.log2(c / tot) for c in counter.values())


def _top3_share(counter):
    tot = sum(counter.values())
    if not tot:
        return 0.0
    return sum(c for _, c in counter.most_common(3)) / tot


def _zone_frac(rs):
    z = Counter(x["zone"] for x in rs)
    return {k: round(z.get(k, 0) / len(rs), 4) for k in ZONES}


def _truncation_rate(rs):
    tot = hit = 0
    for x in rs:
        for t in x.get("rollout_texts", []):
            tot += 1
            hit += _is_truncated(t)
    return round(hit / tot, 4) if tot else None


def _ghost_frac(rs):
    """Problems where every rollout agrees: zero advantage, zero gradient."""
    return round(sum(1 for x in rs
                     if x["correct"] in (0, x["total_rollouts"])) / len(rs), 4)


def _load_failure_classifier():
    """Import classify_failure from analyze_gaps (needs repo root for core.*)."""
    try:
        for p in (REPO, os.path.dirname(os.path.abspath(__file__))):
            if p not in sys.path:
                sys.path.insert(0, p)
        from analyze_gaps import classify_failure
        return classify_failure
    except Exception:
        return None


def _failure_modes(rs, classify):
    """Fractions per analyze_gaps category over problems with >=1 wrong rollout."""
    if classify is None:
        return None
    cats, n = Counter(), 0
    for r in rs:
        texts = r.get("rollout_texts", [])
        rewards = r.get("rollout_rewards", [])
        wrong = next((t for t, w in zip(texts, rewards) if w == 0.0), None)
        if wrong is None:
            continue
        correct = next((t for t, w in zip(texts, rewards) if w == 1.0), None)
        try:
            cat, _ = classify(question=r["problem"], gold_label="",
                              wrong_response=wrong, correct_response=correct,
                              gold_answer=r.get("gold"))
        except Exception:
            continue
        cats[cat] += 1
        n += 1
    if not n:
        return None
    out = {k: round(v / n, 4) for k, v in sorted(cats.items())}
    out["n_classified"] = n
    return out


def _param_vs_passrate(rs, pool_idx):
    """Per-knob-value mean pass rates, from gen_clean's stamped 'knobs'."""
    if not pool_idx:
        return None
    agg = defaultdict(lambda: defaultdict(list))   # param -> value-key -> [pass_rates]
    for r in rs:
        p = pool_idx.get(r["problem"])
        if not p or not isinstance(p.get("knobs"), dict):
            continue
        for param, val in p["knobs"].items():
            agg[param][json.dumps(val)].append(r["pass_rate"])
    if not agg:
        return None
    return {param: {vk: {"pass_rate": round(float(np.mean(prs)), 4), "n": len(prs)}
                    for vk, prs in sorted(vals.items())}
            for param, vals in sorted(agg.items())}


def build_report(rows, path, pool_rows=None, pool_meta=None):
    """The §2b machine-readable calibration report (schema_version 1)."""
    N = rows[0]["total_rollouts"]
    classify = _load_failure_classifier()
    pool_idx = {p["problem"]: p for p in pool_rows} if pool_rows else {}
    meta_concepts = (pool_meta or {}).get("concepts", {})

    byc = defaultdict(list)
    for r in rows:
        byc[r.get("skeleton_type", "unknown")].append(r)

    concepts = {}
    for c, rs in sorted(byc.items()):
        hist = Counter(x["correct"] for x in rs)
        golds = Counter(str(x["gold"]) for x in rs)
        ms = meta_concepts.get(c)
        concepts[c] = {
            "n": len(rs),
            "rollouts": N,
            "zone_frac": _zone_frac(rs),
            "pass_rate_hist": [hist.get(k, 0) for k in range(N + 1)],
            "answer_top3_share": round(_top3_share(golds), 4),
            "answer_entropy": round(_entropy_bits(golds), 4),
            "truncation_rate": _truncation_rate(rs),
            "dedupe_survival": (round(ms["survival"], 4) if ms else None),
            "ghost_frac": _ghost_frac(rs),
            "failure_modes": _failure_modes(rs, classify),
            "param_vs_passrate": _param_vs_passrate(rs, pool_idx),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "file": path,
        "n_problems": len(rows),
        "rollouts": N,
        "overall": {
            "mean_pass": round(float(np.mean([r["pass_rate"] for r in rows])), 4),
            "zone_frac": _zone_frac(rows),
            "truncation_rate": _truncation_rate(rows),
            "ghost_frac": _ghost_frac(rows),
        },
        "concepts": concepts,
    }


def _load_pool(pool_path):
    """Pool rows + the gen-stats sidecar gen_clean writes next to the pool."""
    pool_rows = json.load(open(pool_path))
    pool_meta = None
    for cand in (os.path.splitext(pool_path)[0] + ".meta.json",
                 pool_path + ".meta.json"):
        if os.path.exists(cand):
            pool_meta = json.load(open(cand))
            break
    return pool_rows, pool_meta


# ── terminal analysis (unchanged) ───────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--json", dest="json_out", default=None,
                    help="also write the §2b machine-readable report here "
                         "(requires exactly one calib file)")
    ap.add_argument("--pool", default=None,
                    help="generation pool to join for param_vs_passrate / "
                         "dedupe_survival (optional, used with --json)")
    args = ap.parse_args()

    files = args.files or sorted(glob.glob("/home/faisalnab25/data/calib_*.json"))
    if not files:
        print("usage: python3 analyze_calibration.py file1.json [file2.json ...]"); sys.exit(1)
    if args.json_out and len(files) != 1:
        print("--json requires exactly one calib file"); sys.exit(1)

    summary = {}
    for path in files:
        rows = json.load(open(path))
        tag = os.path.basename(path).replace("calib_", "").replace(".json", "")
        N = rows[0]["total_rollouts"]
        print("=" * 72)
        print(f"FILE: {path}   ({len(rows)} problems x {N} rollouts)")
        print("=" * 72)

        mean_reward = float(np.mean([r["pass_rate"] for r in rows]))
        zones = Counter(r["zone"] for r in rows)
        print(f"Overall mean reward: {mean_reward:.3f}")
        print("Zones: " + "  ".join(f"{k}={v}" for k, v in zones.items()))

        # Step 7: distribution of goldilocks pass rate (0..N correct)
        hist = Counter(r["correct"] for r in rows)
        print(f"\nCorrect-count histogram (0..{N}):")
        for k in range(N + 1):
            print(f"  {k:2d}/{N}: {hist.get(k,0):3d} {'#'*hist.get(k,0)}")

        # Step 7: distribution of mean |advantage|
        maa = [r.get("mean_abs_advantage", 0.0) for r in rows]
        near0 = sum(1 for x in maa if x < 0.05)
        print(f"\nMean |advantage|: mean={np.mean(maa):.3f} median={np.median(maa):.3f}  "
              f"({near0}/{len(rows)} near 0 = no learning signal)")

        # per-concept (your eval philosophy: track per-concept, not one number)
        byc = defaultdict(list)
        for r in rows:
            byc[r.get("skeleton_type", "unknown")].append(r)
        print("\nPer-concept (sorted by mean pass-rate — watch the extremes):")
        print(f"  {'concept':26} {'n':>3} {'mean':>5} {'gold':>4} {'easy':>4} {'hard':>4}")
        for c, rs in sorted(byc.items(), key=lambda kv: np.mean([x['pass_rate'] for x in kv[1]])):
            m = np.mean([x['pass_rate'] for x in rs]); zc = Counter(x['zone'] for x in rs)
            print(f"  {c:26} {len(rs):3d} {m:5.2f} {zc.get('goldilocks',0):4d} "
                  f"{zc.get('too_easy',0):4d} {zc.get('too_hard',0):4d}")

        # Step 4 / F4: parse-rate re-derived from transcripts
        if HAVE_GRADER:
            tot = par = 0
            for r in rows:
                for t in r.get("rollout_texts", []):
                    tot += 1
                    p, _ = extract_predicted_answer(t)
                    par += (p is not None)
            if tot:
                print(f"\nParse rate: {par}/{tot} = {100*par/tot:.1f}% "
                      f"(low => bad scores are FORMAT failures, not math)")

        summary[tag] = mean_reward

        # Step 8: dump 50 stratified transcripts to read by hand
        random.seed(0); picks = []
        for z in ["goldilocks", "too_easy", "too_hard", "borderline"]:
            zr = [r for r in rows if r["zone"] == z]
            picks += random.sample(zr, min(len(zr), 4))
        picks = picks[:50]
        outname = f"transcripts_{tag}.txt"
        with open(outname, "w") as f:
            for r in picks:
                f.write("=" * 72 + "\n")
                f.write(f"[{r['zone']}] {r['correct']}/{N}  concept={r.get('skeleton_type')}  gold={r['gold']}\n")
                f.write("PROBLEM: " + r["problem"][:400] + "\n")
                for j, t in enumerate(r.get("rollout_texts", [])[:2]):
                    f.write(f"--- rollout {j} ---\n" + t[:1200] + "\n")
        print(f"\nWrote {len(picks)} transcripts to {outname} — OPEN IT AND READ THEM (Step 8)")

        # §2b machine-readable report (additive; terminal output above unchanged)
        if args.json_out:
            pool_rows, pool_meta = _load_pool(args.pool) if args.pool else (None, None)
            report = build_report(rows, path, pool_rows, pool_meta)
            with open(args.json_out, "w") as f:
                json.dump(report, f, indent=2)
                f.write("\n")
            print(f"\nWrote machine-readable report to {args.json_out}")

    if len(summary) > 1:
        print("\n" + "=" * 72)
        print("CAPABILITY ORDERING (Step 7):")
        for tag, mr in sorted(summary.items(), key=lambda kv: kv[1]):
            print(f"  {tag:24} mean_reward={mr:.3f}")
        print("PASS iff the bigger model has the higher mean_reward.")


if __name__ == "__main__":
    main()
