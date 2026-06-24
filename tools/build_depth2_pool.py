#!/usr/bin/env python3
"""
build_depth2_pool.py — build a RAW (ungraded) DEPTH-2 recognition-trap calibration pool.

Mirrors build_depth1_5_pool.py: one prep/gen_clean.py subprocess per trap concept (with DEPTH2=1 so
the trap library is registered), merged into one pool JSON. This is the raw pool the static gate
(check_dataset golds + static_checks) runs on, and the input to sample.py for the depth-2 calibration
sample vs the DEPTH-1 model — to tune each trap to the goldilocks 2-6/8 band before training.

The 5 traps (all single, un-announced, naive!=gold): trap_grid_count (A), trap_seam_presence (1.5 twin),
trap_lattice_triangle (B), trap_walk_blocked (C), trap_logic_implications (D). gen_clean gold-fixes via
the trap recomputers in check_dataset.py, so every shipped gold is independently re-verified.

Usage: python3 tools/build_depth2_pool.py [out.json]   (env: PER_TRAP=60, INJECTOR=...)
"""
import os, sys, json, subprocess, tempfile
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); os.chdir(ROOT)

INJ = os.environ.get("INJECTOR", "generate/skeleton_injector_v12.py")
PER = int(os.environ.get("PER_TRAP", "60"))
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/depth2_pool.json"

# DEPTH2=1 must be set BEFORE importing the injector so the trap library registers.
env = {**os.environ, "INJECTOR": INJ, "DEPTH2": "1"}
import generate.skeleton_injector_v12 as M   # imported under our process env (DEPTH2 may be unset here)
# Re-derive the trap list the way the subprocess will see it (DEPTH2=1), not this process's REGISTRY.
traps = ["trap_grid_count", "trap_seam_presence", "trap_lattice_triangle",
         "trap_walk_blocked", "trap_logic_implications"]

tmp = tempfile.mkdtemp(prefix="d2_pool_")
rows = []
for ch in traps:
    p = os.path.join(tmp, f"{ch}.json")
    r = subprocess.run([sys.executable, "prep/gen_clean.py", "--concept", ch, "--n", str(PER), "--out", p],
                       env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  !! {ch}: gen_clean rc={r.returncode}  {r.stderr.strip()[-200:]}")
        continue
    if os.path.exists(p):
        got = json.load(open(p))
        rows += got
        print(f"  {ch}: {len(got)} rows")
json.dump(rows, open(OUT, "w"), indent=2)
fams = Counter(r.get("trap", {}).get("family", "?") for r in rows)
d2 = sum(1 for r in rows if r.get("depth") == 2)
print(f"built {len(rows)} rows ({d2} depth-2) across {len(traps)} traps -> {OUT}")
print(f"by family: {dict(fams)}")
