"""
analyze_calibration.py — turn calibration output into the protocol's Step 7-9 info.
Usage:  python3 analyze_calibration.py ~/data/calib_7B.json [~/data/calib_1.5B.json ...]
"""
import json, sys, glob, os, random
import numpy as np
from collections import defaultdict, Counter

try:                       # re-derive parse-rate from saved transcripts (F4 / Step 4)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from reward_func import extract_predicted_answer
    HAVE_GRADER = True
except Exception:
    HAVE_GRADER = False

files = sys.argv[1:] or sorted(glob.glob("/home/faisalnab25/data/calib_*.json"))
if not files:
    print("usage: python3 analyze_calibration.py file1.json [file2.json ...]"); sys.exit(1)

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

if len(summary) > 1:
    print("\n" + "=" * 72)
    print("CAPABILITY ORDERING (Step 7):")
    for tag, mr in sorted(summary.items(), key=lambda kv: kv[1]):
        print(f"  {tag:24} mean_reward={mr:.3f}")
    print("PASS iff the bigger model has the higher mean_reward.")
