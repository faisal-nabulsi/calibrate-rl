#!/usr/bin/env python3
"""
build_depth1_5_pool.py — build a RAW (ungraded) depth-1.5 EMBEDDED chain pool.

Mirrors the campaign's build_pool: one prep/gen_clean.py subprocess per chain with
CHAIN_SURFACE=embedded, merged into one pool JSON. This is the raw pool the static gate
(prep/check_dataset.py golds + automation/calibrator/static_checks.py) runs on, and the
input to sample.py for the eventual depth-1.5 calibration.

Usage: python3 tools/build_depth1_5_pool.py [out.json]   (env: PER_CHAIN=40, INJECTOR=...)
"""
import os, sys, json, subprocess, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); os.chdir(ROOT)
import generate.skeleton_injector_v12 as M

INJ = os.environ.get("INJECTOR", "generate/skeleton_injector_v12.py")
PER = int(os.environ.get("PER_CHAIN", "40"))
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/depth1_5_pool.json"
chains = [n for n, _, _ in M.REGISTRY if n.startswith("chain_")]
env = {**os.environ, "INJECTOR": INJ, "CHAIN_SURFACE": "embedded"}
tmp = tempfile.mkdtemp(prefix="d15_pool_")
rows = []
for ch in chains:
    p = os.path.join(tmp, f"{ch}.json")
    r = subprocess.run([sys.executable, "prep/gen_clean.py", "--concept", ch, "--n", str(PER), "--out", p],
                       env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  !! {ch}: gen_clean rc={r.returncode}  {r.stderr.strip()[-200:]}")
        continue
    if os.path.exists(p):
        rows += json.load(open(p))
json.dump(rows, open(OUT, "w"), indent=2)
emb = sum(1 for r in rows if r.get("chain", {}).get("surface") == "embedded")
print(f"built {len(rows)} rows ({emb} embedded) across {len(chains)} chains -> {OUT}")
