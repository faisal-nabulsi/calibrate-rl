"""
Build the goldilocks training + held-out sets for the DEPTH-1 (chain) hillclimb.

Depth-1 analogue of build_goldilocks_set.py. SOURCE: a depth-1 calib.json — the
converged merged calib from tools/depth1_calib_campaign.py (rows in the sample.py
schema, each with the 8 stored rollout_texts, calibrated vs ckpt-40). We RE-GRADE
the stored rollouts with the CURRENT grader (so the kept set is consistent with
what training will actually reward, not the stored zone) and keep the ones that
land 2-6/8 = goldilocks (non-saturated => GRPO advantage signal).

Held-out monitor is stratified by CHAIN (one unseen goldilocks per chain that can
spare one), not by atomic concept — depth-1's unit is the chain. Deterministic (seed).

Outputs (paths/band configurable via env):
  data/goldilocks_train_depth1.json    -> train/train_grpo.py (LoRA off ckpt-40)
  data/goldilocks_holdout_depth1.json  -> per-step pass@8 held-out monitor (per chain)

Usage:
  CALIB=data/depth1_calib_iter3.json python3 prep/build_goldilocks_set_depth1.py
"""
import os, sys, json, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root, for `core`
from collections import defaultdict, Counter
from core.reward_func import extract_predicted_answer, extract_gold_answer, _numbers_match

CALIB     = os.environ.get("CALIB", "data/depth1_calib_final.json")
TRAIN_OUT = os.environ.get("TRAIN_OUT", "data/goldilocks_train_depth1.json")
HOLD_OUT  = os.environ.get("HOLD_OUT", "data/goldilocks_holdout_depth1.json")
LO        = int(os.environ.get("GOLD_LO", "2"))   # keep k/8 with LO <= k <= HI
HI        = int(os.environ.get("GOLD_HI", "6"))
SEED      = int(os.environ.get("SEED", "42"))


def chain_key(r):
    c = r.get("chain") or {}
    comp = c.get("components")
    return "chain_" + "__".join(comp) if comp and len(comp) == 2 else r.get("skeleton_type", "?")


def regrade(rollout_texts, gold):
    """Re-derive the pass count with the CURRENT grader (vs the stored 'correct')."""
    g = extract_gold_answer(str(gold))
    n = 0
    for t in rollout_texts:
        p, _ = extract_predicted_answer(t)
        if g is not None and p is not None and _numbers_match(p, g):
            n += 1
    return n


def main():
    d = json.load(open(CALIB))
    rows, moved = [], 0
    for r in d:
        gold = str(r.get("gold", r.get("answer")))
        n = regrade(r.get("rollout_texts", []), gold)
        if n != r.get("correct"):
            moved += 1
        if LO <= n <= HI:                                 # goldilocks under the current grader
            out = {"problem": r["problem"], "answer": gold,
                   "skeleton_type": r.get("skeleton_type"), "depth": 1,
                   "calib_correct": n}
            if r.get("chain"):
                out["chain"] = r["chain"]                 # carry chain meta for the composition-gap diagnostic
            if r.get("knobs"):
                out["knobs"] = r["knobs"]
            rows.append(out)

    nchains = len(set(chain_key(r) for r in rows))
    print(f"re-graded {len(d)} depth-1 calib rows | correct-count moved vs stored: {moved}")
    print(f"goldilocks ({LO}-{HI}/8 after re-grade): {len(rows)} across {nchains} chains")

    by = defaultdict(list)
    for r in rows:
        by[chain_key(r)].append(r)
    rng = random.Random(SEED)
    hold = []
    for ch in sorted(by):                                 # one held-out per chain that can spare one
        insts = by[ch][:]
        if len(insts) >= 2:
            rng.shuffle(insts)
            hold.append(insts[0])
    holdset = {id(r) for r in hold}
    train = [r for r in rows if id(r) not in holdset]

    json.dump(train, open(TRAIN_OUT, "w"), indent=1)
    json.dump(hold, open(HOLD_OUT, "w"), indent=1)
    print(f"\ntrain:    {len(train):3d} -> {TRAIN_OUT}")
    print(f"held-out: {len(hold):3d} -> {HOLD_OUT}  (1 per chain, {len(hold)} chains had a spare)")
    print("train per-chain:", dict(sorted(Counter(chain_key(r) for r in train).items())))


if __name__ == "__main__":
    main()
