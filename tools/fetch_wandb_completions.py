#!/usr/bin/env python3
"""
Download a W&B run's logged completion tables + scalar history into local files,
so we can analyze reward curves and read training rollouts offline.

Run where wandb is authed and has access to the rl-intro entity:
    pip install wandb pandas
    wandb login                      # team WANDB_API_KEY
    python3 tools/fetch_wandb_completions.py rl-intro/tiny-math-solver/<run_id>

Writes:
    results/wandb_completions_<run_id>.json   (all rollouts: prompt/completion/reward rows)
    results/wandb_history_<run_id>.csv        (per-step reward/kl/loss/etc — the reward curve)
"""
import sys, os, json, glob
import wandb

RUN = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("WANDB_RUN")
if not RUN:
    sys.exit("usage: fetch_wandb_completions.py <entity>/<project>/<run_id>")
run_id = RUN.rstrip("/").split("/")[-1]
RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(RESULTS, exist_ok=True)
OUT = os.path.join(RESULTS, f"wandb_completions_{run_id}.json")
HIST = os.path.join(RESULTS, f"wandb_history_{run_id}.csv")

api = wandb.Api()
run = api.run(RUN)
print(f"run: {run.name}  state={run.state}  ({RUN})", flush=True)

# 1) scalar history (the reward curve) — full, unsampled
try:
    import pandas as pd
    rows_h = list(run.scan_history())
    pd.DataFrame(rows_h).to_csv(HIST, index=False)
    print(f"wrote {len(rows_h)} history steps -> {HIST}", flush=True)
except Exception as e:
    print("history dump failed (non-fatal):", e, flush=True)

# 2) completion tables (the training rollouts)
rows = []
arts = [a for a in run.logged_artifacts() if a.type == "run_table" and "completions" in a.name]
arts.sort(key=lambda a: int(a.version.lstrip("v")) if a.version.lstrip("v").isdigit() else 0)
print(f"{len(arts)} completion tables", flush=True)
for i, a in enumerate(arts):
    d = a.download()
    for f in glob.glob(os.path.join(d, "**", "*.json"), recursive=True):
        try:
            t = json.load(open(f))
        except Exception:
            continue
        if isinstance(t, dict) and "columns" in t and "data" in t:
            cols = t["columns"]
            for r in t["data"]:
                row = dict(zip(cols, r)); row["_table_version"] = a.version
                rows.append(row)
    print(f"  {i+1}/{len(arts)} {a.name}: {len(rows)} rows", flush=True)

json.dump(rows, open(OUT, "w"))
print(f"wrote {len(rows)} rollouts -> {OUT}")
if rows:
    print("columns:", list(rows[0].keys()))
