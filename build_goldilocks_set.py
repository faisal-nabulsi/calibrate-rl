"""
Build the goldilocks training + held-out sets for the depth-0 hillclimb.

Source: data/calib_v10_7B.json (300 calibrated problems, each with the 8 stored
rollout_texts). We RE-GRADE those stored rollouts with the CURRENT hardened
grader and CORRECTED golds (continued_fraction depth fix), then keep the ones
that land 2-6/8 = goldilocks. Re-grading (vs trusting the stored zone) matters
because the grader was hardened and continued_fraction golds were fixed after
calibration ran — so this re-derives goldilocks consistently with what training
will actually reward.

Split: hold out 1 unseen goldilocks from each of the top-N concepts by count
(N=12 -> ~12 held-out, rest train). Can't stratify across all concepts: most
have too few goldilocks to spare one. Deterministic (seed 42).

Outputs:
  data/goldilocks_train_v10.json    (~108)  -> train_grpo.py
  data/goldilocks_holdout_v10.json  (~12)   -> per-step pass@8 monitor
"""
import json, random
from collections import defaultdict, Counter
from reward_func import extract_predicted_answer, extract_gold_answer, _numbers_match
from clean_dataset import parse_cf, cf_value

CALIB = "data/calib_v10_7B.json"
TRAIN_OUT = "data/goldilocks_train_v10.json"
HOLD_OUT = "data/goldilocks_holdout_v10.json"
N_HOLD_CONCEPTS = 12
SEED = 42


def corrected_gold(r):
    if r.get("skeleton_type") == "continued_fraction":
        x, d = parse_cf(r["problem"])
        if x is not None:
            return str(cf_value(x, d))
    return str(r["gold"])


def regrade(rollout_texts, gold):
    g = extract_gold_answer(str(gold))
    n = 0
    for t in rollout_texts:
        p, _ = extract_predicted_answer(t)
        if g is not None and p is not None and _numbers_match(p, g):
            n += 1
    return n


def main():
    d = json.load(open(CALIB))
    rows, cf_fixed, zone_moved = [], 0, 0
    for r in d:
        gold = corrected_gold(r)
        if r.get("skeleton_type") == "continued_fraction" and gold != str(r["gold"]):
            cf_fixed += 1
        n = regrade(r.get("rollout_texts", []), gold)
        if n != r.get("correct"):
            zone_moved += 1
        if 2 <= n <= 6:                                  # goldilocks under current grader
            rows.append({"problem": r["problem"], "answer": gold,
                         "skeleton_type": r["skeleton_type"], "depth": "0",
                         "calib_correct": n})
    print(f"re-graded 300 calib problems | continued_fraction golds fixed: {cf_fixed} "
          f"| problems whose correct-count moved vs stored: {zone_moved}")
    print(f"goldilocks (2-6/8 after re-grade): {len(rows)} across "
          f"{len(set(r['skeleton_type'] for r in rows))} concepts")

    by = defaultdict(list)
    for r in rows:
        by[r["skeleton_type"]].append(r)
    rng = random.Random(SEED)
    top = sorted(by, key=lambda k: (-len(by[k]), k))[:N_HOLD_CONCEPTS]
    hold = []
    for c in top:
        insts = by[c][:]
        rng.shuffle(insts)
        hold.append(insts[0])
    holdset = {id(r) for r in hold}
    train = [r for r in rows if id(r) not in holdset]

    json.dump(train, open(TRAIN_OUT, "w"), indent=1)
    json.dump(hold, open(HOLD_OUT, "w"), indent=1)
    print(f"\ntrain:    {len(train):3d} -> {TRAIN_OUT}")
    print(f"held-out: {len(hold):3d} -> {HOLD_OUT}  (1 each from {len(top)} concepts)")
    print("held-out concepts:", ", ".join(r["skeleton_type"] for r in hold))
    print("train per-concept:", dict(Counter(r["skeleton_type"] for r in train)))


if __name__ == "__main__":
    main()
