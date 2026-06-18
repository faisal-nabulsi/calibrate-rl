"""Build the v12 "hard-band" training sets: same v12 pool, pass-rate pre-filtered to the
harder band (base 8-rollout correct count <= 5/8), filtering out the already-easy problems.

Two variants:
  v12_hardband_1to5_train.json  (calib_correct in [1,5])  -- RECOMMENDED. v12_train minus the
        easy 6/8+7/8. Every problem has nonzero reward variance (real gradient).
  v12_hardband_0to5_train.json  (calib_correct in [0,5])  -- also re-injects the 90 reserved
        too_hard (0/8) problems. 0/8 are ghost batches (all rollouts fail -> zero gradient).

Held-out (data/v12_holdout.json) is UNCHANGED (kept comparable to v12). The end-of-run signal on
the hard portion of the held-out is computed separately by tools/eval_hard_subset.py.
"""
import json
from collections import Counter

train   = json.load(open("data/v12_train.json"))     # 449  calib_correct 1..7 (goldilocks+borderline)
reserve = json.load(open("data/v12_reserve.json"))   # 90   calib_correct 0   (too_hard)
holdout = json.load(open("data/v12_holdout.json"))   # 79   FIXED, never trained on

pool = train + reserve  # all labeled non-holdout problems (too_easy 8/8 already excluded upstream)

def hist(rows):
    h = Counter(r["calib_correct"] for r in rows)
    return " ".join(f"{k}/8:{h.get(k,0)}" for k in range(9) if h.get(k,0))

band_1to5 = [r for r in pool if 1 <= r["calib_correct"] <= 5]
band_0to5 = [r for r in pool if 0 <= r["calib_correct"] <= 5]

json.dump(band_1to5, open("data/v12_hardband_1to5_train.json","w"), indent=0)
json.dump(band_0to5, open("data/v12_hardband_0to5_train.json","w"), indent=0)

print("source pool (v12_train+reserve, holdout excluded):", len(pool), "|", hist(pool))
print(f"WROTE v12_hardband_1to5_train.json  n={len(band_1to5)}  ({hist(band_1to5)})  "
      f"-> 112 steps @4 prompts/step = {112*4/len(band_1to5):.2f} epochs   [RECOMMENDED]")
print(f"WROTE v12_hardband_0to5_train.json  n={len(band_0to5)}  ({hist(band_0to5)})  "
      f"-> {112*4/len(band_0to5):.2f} epochs   (incl. {sum(1 for r in band_0to5 if r['calib_correct']==0)} ghost-batch 0/8)")
hard_ho = [r for r in holdout if r["calib_correct"] <= 5]
print(f"held-out hard subset (calib_correct<=5): {len(hard_ho)}/{len(holdout)}  ({hist(holdout)})")
