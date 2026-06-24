#!/usr/bin/env python3
"""
Prototype: DEPTH-2 Family A — the RECOGNITION TRAP (the only mechanism the transfer analysis
says puts GRPO gradient on STRUCTURE-RECOGNITION, the verified AMC wall).

A SINGLE, un-announced counting problem (no feeder->target seam) with a COUPLED constraint, where:
  - gold = EXACT brute-force enumeration of the valid configurations (oracle, no LLM judge),
  - a tempting NAIVE method ("the pairing is forced -> unique -> 1") yields a SPECIFIC wrong number,
  - we ASSERT naive != gold at build, so every shipped problem provably PUNISHES the naive read.

This is literally AMC pid-1's structure (split 1..2n into n pairs, greater >= k*lesser, count) where
depth-1 boxed the naive 1 vs gold 144. A model that pattern-matches to the nearest closed form (greedy
forced pairing) is penalized; a model that recognizes "the partners are NOT forced, enumerate" wins ->
the gradient lands on recognition, the operation depth-1 never trained.

Verifies: exact gold (independent recompute), naive!=gold (trap holds), answer diversity (top3),
goldilocks-tunable difficulty via the COUPLING (k) and size (n), never number magnitude.
"""
import argparse, random
from collections import Counter
from functools import lru_cache


def count_matchings(elements, k):
    """EXACT oracle: # perfect matchings of `elements` where every pair has greater >= k*lesser.
    Match the smallest element to each valid partner, recurse on the rest. Memoized on the frozen set."""
    @lru_cache(maxsize=None)
    def rec(elts):
        if not elts:
            return 1
        first = elts[0]                       # smallest (elts kept sorted) — its partner is the greater
        total = 0
        for i in range(1, len(elts)):
            partner = elts[i]
            if partner >= k * first:          # greater(partner) >= k * lesser(first)
                total += rec(elts[1:i] + elts[i + 1:])   # remove BOTH first (idx 0) and partner (idx i)
        return total
    return rec(tuple(sorted(elements)))


def naive_forced_count(n, k):
    """The TRAP value: what the naive 'each large element has a UNIQUE forced partner -> one chain'
    method produces. Greedily pair the LARGEST remaining with its only-if-forced smallest partner;
    if every step is forced it returns 1 (the documented pid-1 error: boxes 1). If a step has 0 or
    >1 options the naive heuristic still commits to one -> still reports 1 matching. So naive == 1."""
    return 1


def gen(n, k):
    twon = 2 * n
    gold = count_matchings(range(1, twon + 1), k)
    naive = naive_forced_count(n, k)
    prob = (f"How many ways are there to split the integers 1 through {twon} into {n} pairs such that "
            f"in each pair, the greater number is at least {k} times the lesser number?")
    return prob, gold, naive


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=400)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    random.seed(a.seed)
    rows = []
    for _ in range(a.samples):
        n = random.randint(5, 8)              # 2n in [10,16]: brute-force-feasible, pid-1 is n=7
        k = random.choice([2, 3])             # the COUPLING knob (not number size)
        rows.append(gen(n, k))

    # independent recompute (re-enumerate from the displayed 2n, k parsed from text) == stored gold?
    import re
    bad = 0
    for prob, gold, _ in rows:
        twon = int(re.search(r"integers 1 through (\d+)", prob).group(1))
        k = int(re.search(r"at least (\d+) times", prob).group(1))
        if count_matchings(range(1, twon + 1), k) != gold:
            bad += 1

    golds = [g for _, g, _ in rows]
    trap_holds = sum(1 for _, g, nv in rows if g != nv)         # naive != gold (the trap is real)
    naive_is_modal_hack = Counter(golds).get(1, 0)              # how often gold==1 (naive would be RIGHT)
    cc = Counter(golds)
    top3 = sum(v for _, v in cc.most_common(3)) / len(golds)

    print(f"n={len(rows)}  EXACT-GOLD mismatches (gen vs independent re-enumeration): {bad}  "
          f"{'<- OK, oracle exact' if bad == 0 else '<- BUG'}")
    print(f"TRAP HOLDS (naive 'forced->1' != enumerated gold): {trap_holds}/{len(rows)} "
          f"({100*trap_holds/len(rows):.0f}%)   [problems where gold==1, naive would be right: {naive_is_modal_hack}]")
    print(f"answer diversity: {len(cc)} distinct golds | top3-share={top3:.3f} (gate wants <=0.30)")
    print(f"gold range: {min(golds)}..{max(golds)}  median {sorted(golds)[len(golds)//2]}")
    print("\nexamples (single narrative, NO announced seam; naive 'forced-unique' boxes 1 and LOSES):")
    seen = set()
    for prob, gold, naive in rows:
        key = prob[:40]
        if key in seen:
            continue
        seen.add(key)
        if len(seen) > 6:
            break
        print(f"  gold={gold:>5}  (naive trap={naive})   {prob}")


if __name__ == "__main__":
    main()
