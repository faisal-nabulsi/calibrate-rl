#!/usr/bin/env python3
"""
Verify the diverse depth-1 chains: registration, yield, answer-diversity gate, and
construction-correct golds. The gold recomputer re-derives the composite answer from the
TARGET CLAUSE (the text after the embedded sub-question) plus the stored intermediate V
(meta.chain.intermediate_gold) -- catching any adapter oracle / text mismatch. It trusts the
feeder's V (construction-correct, same as the prior value-chains).

  INJECTOR=generate/skeleton_injector_v12.py python3 tools/verify_diverse_chains.py
"""
import os, re, math, random, importlib.util
from fractions import Fraction
from collections import Counter

random.seed(11)
INJ = os.environ.get("INJECTOR", "generate/skeleton_injector_v12.py")
spec = importlib.util.spec_from_file_location("inj", INJ)
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
def _lcm(a, b): return a*b//math.gcd(a, b)

# Gold recompute DELEGATES to the authoritative recomputers in prep/check_dataset.py
# (single source of truth). The old inline copy here silently drifted every time a
# target's phrasing changed (ie3 3-set→2-set, multisquare optional last-digit) — a
# shadow recomputer is a trap, so this script now calls the live gate's functions.
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prep.check_dataset import _recompute_target, _chain_split  # noqa: E402

def recompute(target, prob, V):
    _, c = _chain_split(prob)            # (sub-question, target clause)
    if c is None:
        return None
    return _recompute_target(target, c, V)

chains = [nm for nm,_,_ in M.REGISTRY if nm.startswith("chain_")]
gen = {nm: fn for nm,fn,_ in M.REGISTRY}
print(f"chains registered: {len(chains)}")

tgt_hist = Counter(); bad_total = unp_total = 0; fails = []
for nm in sorted(chains):
    fn = gen[nm]; ans = []; bad = 0; unp = 0
    target = nm.split("__")[-1]
    tgt_hist[target] += 1
    tries = 0
    while len(ans) < 600 and tries < 8000:
        tries += 1
        r = fn()
        if r is None: continue
        prob, gold, _, meta = r
        ans.append(gold)
        V = meta["chain"]["intermediate_gold"]
        got = recompute(target, prob, V)
        if got is None: unp += 1
        elif got != gold: bad += 1
    cc = Counter(ans); top3 = sum(v for _,v in cc.most_common(3))/max(1,len(ans))
    dd = len(set(ans))/max(1,len(ans))
    yld = len(ans)/max(1,tries)
    ok = bad == 0 and unp == 0 and top3 <= 0.30 and len(ans) >= 100
    bad_total += bad; unp_total += unp
    flag = "" if ok else "  <-- CHECK"
    if not ok: fails.append((nm, bad, unp, top3, len(ans)))
    print(f"  {nm:54} yld={yld:.2f} top3={top3:.3f} dd={dd:.2f} bad={bad} unp={unp}{flag}")

print(f"\nTARGET CONCEPTS used: {len(tgt_hist)} -> {dict(tgt_hist)}")
print(f"gold mismatches: {bad_total} | unparsed: {unp_total} | failing chains: {len(fails)}")
print("ALL PASS" if (bad_total==0 and unp_total==0 and not fails) else "FAILURES PRESENT")
