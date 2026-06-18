"""End-of-run metric: how is the model doing on the HARD portion of the (fixed) held-out set?

The held-out (data/v12_holdout.json) is unchanged from v12 so runs stay comparable, but it contains
already-easy problems that saturate. This re-scores each held-out eval restricted to the problems in
the same hard band as training (base 8-rollout calib_correct <= band-max), filtering out the easy ones,
so you can see whether the hard band actually moved.

Reads the per-step held-out transcripts a run already wrote (holdout_step*.jsonl). Works on a local
dir or an s3:// prefix (synced to a temp dir).

Usage:
  python tools/eval_hard_subset.py --transcripts s3://calibrate-rl-agent/runs/v12_hardband_run1/holdout_transcripts/
  python tools/eval_hard_subset.py --transcripts /tmp/holdout_run --band-max 5
"""
import os, sys, json, glob, re, argparse, subprocess, tempfile

ap = argparse.ArgumentParser()
ap.add_argument("--transcripts", required=True, help="local dir OR s3:// prefix of holdout_step*.jsonl")
ap.add_argument("--holdout", default="data/v12_holdout.json")
ap.add_argument("--band-max", type=int, default=5, help="hard = base calib_correct <= this (out of 8)")
a = ap.parse_args()

d = a.transcripts
if d.startswith("s3://"):
    tmp = tempfile.mkdtemp(prefix="holdout_")
    subprocess.run(["aws","s3","cp",d,tmp,"--recursive","--exclude","*","--include","holdout_step*"],
                   check=True)
    d = tmp

# hard mask from the fixed held-out's base calibration
ho = json.load(open(a.holdout))
hard = {r["problem"] for r in ho if r["calib_correct"] <= a.band_max}
print(f"held-out: {len(ho)} total | hard (calib_correct<={a.band_max}): {len(hard)} | easy: {len(ho)-len(hard)}")

def mpr(recs):
    if not recs: return None
    tot = 0.0
    for r in recs:
        k = r.get("k") or len(r.get("samples", [])) or 1
        nc = r.get("n_correct_rollouts")
        if nc is None:
            nc = sum(1 for s in r.get("samples", []) if s.get("correct"))
        tot += nc / k
    return tot / len(recs)

rows = []
unmatched = 0
for f in glob.glob(os.path.join(d, "holdout_step*.jsonl")):
    m = re.search(r"step(\d+)", os.path.basename(f))
    when = "end" if "_end" in f else ("begin" if "_begin" in f else "periodic")
    recs = [json.loads(l) for l in open(f) if l.strip()]
    for r in recs:
        if r["problem"] not in {x["problem"] for x in ho}: unmatched += 1
    hard_recs = [r for r in recs if r["problem"] in hard]
    rows.append((int(m.group(1)), when, mpr(recs), mpr(hard_recs), len(hard_recs)))

rows.sort()
print(f"\n{'step':>5} {'when':>9} {'mpr_FULL':>9} {'mpr_HARD':>9} {'n_hard':>6}")
for s, when, full, h, n in rows:
    print(f"{s:>5} {when:>9} {full:>9.4f} {h:>9.4f} {n:>6}")
if rows:
    base = rows[0]
    bestf = max(rows, key=lambda r: r[2]); besth = max(rows, key=lambda r: r[3])
    print(f"\nFULL : base={base[2]:.4f} -> best={bestf[2]:.4f} @step{bestf[0]}  (Δ{bestf[2]-base[2]:+.4f})")
    print(f"HARD : base={base[3]:.4f} -> best={besth[3]:.4f} @step{besth[0]}  (Δ{besth[3]-base[3]:+.4f})")
if unmatched: print(f"\n[warn] {unmatched} transcript records did not match a held-out problem (text mismatch)")
