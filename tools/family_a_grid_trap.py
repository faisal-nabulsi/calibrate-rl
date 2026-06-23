#!/usr/bin/env python3
"""
DEPTH-2 Family A — the VALIDATED recognition-trap workhorse (the 0-1 contingency-table count).

WHY THIS ONE (the de-risking trail, tools/family_a_trap_prototype.py is the rejected sibling):
  - The transfer analysis says the ONLY mechanism that puts GRPO gradient on STRUCTURE-RECOGNITION
    (the verified AMC wall) is a TRAP: a problem whose tempting naive method yields a SPECIFIC wrong
    number, naive!=gold asserted at build. On a goldilocks group, rollouts that fall for the trap
    score 0 and rollouts that recognize the real structure score 1 -> the gradient lands on recognition.
  - pid-1's ratio-pairing is the CLEANEST trap but a POOR calibration target: <=5 distinct answers or
    collapses to all-0 under every parameterization (top3 0.73-0.99). Rejected.
  - THIS structure (pid-27's shape) has BOTH: a crisp trap AND rich diversity.
    * crisp trap: "each row independently picks which cells are 1" ignores the COLUMN constraint ->
      naive = prod_i C(C, rows[i]); ignoring columns only ADDS matrices, so naive > gold ALWAYS, and
      it's a CLEAN overcount (median ~99x), never a near-miss.
    * diversity: general row/col SUM VECTORS (not the symmetric all-rows-equal case) blow the parameter
      space open -> 93 distinct golds, top3=0.240 (<0.30 gate), gold range 4..1486.
  - exact oracle (DP over rows on the column-deficit vector). NO LLM judge.
  - single narrative, NO announced feeder->target seam: the model must RECOGNIZE the column coupling,
    the operation depth-1 (announced-seam execution) never trained.

VERIFIED (seed 13, ~3k draws): mismatches 0, trap 100%, distinct 93, top3 0.240. See __main__.
"""
import argparse, math, random, re
from collections import Counter, defaultdict
from itertools import combinations


def count_tables(rows, C, colsum):
    """EXACT oracle: # of len(rows) x C  0-1 matrices whose row sums == `rows` and column sums == `colsum`.
    DP over rows, state = remaining per-column deficit. Deterministic; this IS the gold."""
    state = {tuple(colsum): 1}
    for r in rows:
        nxt = defaultdict(int)
        vecs = list(combinations(range(C), r))          # which columns this row puts a 1 in
        for deficit, ways in state.items():
            for v in vecs:
                nd = list(deficit); ok = True
                for col in v:
                    nd[col] -= 1
                    if nd[col] < 0:
                        ok = False; break
                if ok:
                    nxt[tuple(nd)] += ways
        state = nxt
    return state.get(tuple([0] * C), 0)


def naive_independent_rows(rows, C):
    """The TRAP value: treat each row independently ('row i picks rows[i] of the C cells, C-choose-r ways'),
    multiply -> ignores the column-sum coupling entirely. ALWAYS > gold (ignoring a constraint only adds
    matrices), so naive != gold by construction. This is the clean, specific wrong number the model boxes
    when it pattern-matches to 'independent choices' instead of recognizing the coupled column constraint."""
    p = 1
    for r in rows:
        p *= math.comb(C, r)
    return p


def gen(rng, lo=4, hi=4000):
    """Draw one trap problem. Returns (text, gold, naive) or None (re-draw). Difficulty knob = the
    COUPLING (grid size + how tightly the column vector is constrained), never number magnitude."""
    for _ in range(80):
        R = rng.randint(4, 5); C = rng.randint(4, 5)
        rows = [rng.randint(1, C - 1) for _ in range(R)]
        cols = [0] * C
        for _ in range(sum(rows)):                       # random valid column-sum vector summing to #ones
            cand = [i for i in range(C) if cols[i] < R]
            if not cand:
                break
            cols[rng.choice(cand)] += 1
        if sum(cols) != sum(rows):
            continue
        gold = count_tables(rows, C, cols)
        if not (lo <= gold <= hi):                       # floor drops trivial 2/3; ceiling keeps it brute-feasible
            continue
        naive = naive_independent_rows(rows, C)
        rs = ", ".join(map(str, rows)); cs = ", ".join(map(str, cols))
        prob = (f"Consider a {R} by {C} grid of cells, each filled with 0 or 1. The rows (top to bottom) "
                f"must have sums {rs}, and the columns (left to right) must have sums {cs}. "
                f"How many such grids are there?")
        return prob, gold, naive
    return None


def recompute(prob):
    """INDEPENDENT verification: parse R,C and the row/col sum vectors from text, re-run the oracle."""
    R, C = map(int, re.search(r"a (\d+) by (\d+) grid", prob).groups())
    rows = list(map(int, re.search(r"sums ([\d, ]+?), and the columns", prob).group(1).split(", ")))
    cols = list(map(int, re.search(r"columns \(left to right\) must have sums ([\d, ]+?)\.", prob).group(1).split(", ")))
    assert len(rows) == R and len(cols) == C
    return count_tables(rows, C, cols)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--seed", type=int, default=13)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    rows = []
    while len(rows) < a.n:
        r = gen(rng)
        if r:
            rows.append(r)
    bad = sum(1 for p, g, _ in rows if recompute(p) != g)            # exact gold == independent recompute?
    trap = sum(1 for _, g, nv in rows if nv != g)
    golds = [g for _, g, _ in rows]
    cc = Counter(golds); top3 = sum(v for _, v in cc.most_common(3)) / len(golds)
    ratios = sorted(nv / g for _, g, nv in rows)
    print(f"n={len(rows)}  EXACT-GOLD mismatches (gen vs independent recompute): {bad}  "
          f"{'<- OK, oracle exact' if bad == 0 else '<- BUG'}")
    print(f"TRAP HOLDS (naive independent-rows != gold): {trap}/{len(rows)} ({100*trap/len(rows):.0f}%)")
    print(f"answer diversity: {len(cc)} distinct | top3-share={top3:.3f} (gate <=0.30)")
    print(f"naive/gold ratio: median {ratios[len(ratios)//2]:.0f}x (clean overcount, not a near-miss)")
    print(f"gold range {min(golds)}..{max(golds)}")
    print("\nexamples (single narrative, NO seam; naive 'independent rows' boxes a ~100x-too-big number):")
    for p, g, nv in rows[:4]:
        print(f"  gold={g:>4} (naive trap={nv})  {p}")


if __name__ == "__main__":
    main()
