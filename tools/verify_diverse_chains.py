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

def clause_of(prob):
    return prob.split("”")[-1]   # text after the embedded sub-question

def recompute(target, prob, V):
    c = clause_of(prob)
    if target == "modular_exponent":
        m = int(re.search(r"divided by (\d+)", c).group(1))
        mb = re.search(r"V\^(\d+)", c); me = re.search(r"(\d+)\^V", c)
        if mb: return pow(V, int(mb.group(1)), m)
        if me: return pow(int(me.group(1)), V, m)
        return None
    if target == "algebraic_system_2eq":
        rows = re.findall(r"(\d+)x\+(\d+)y\+(\d+)z=(\d+)", c)
        if len(rows) != 2: return None
        (a1,b1,c1,d1),(a2,b2,c2,d2) = [tuple(map(int,r)) for r in rows]
        D1, D2 = d1-a1*V, d2-a2*V
        det = b1*c2-b2*c1
        if det == 0: return None
        y = Fraction(D1*c2-D2*c1, det); z = Fraction(b1*D2-b2*D1, det)
        s = V+y+z
        return int(s) if s.denominator == 1 else None
    if target == "telescoping_mn":
        gap = int(re.search(r"k\+(\d+)", c).group(1))
        s = sum(Fraction(1, k*(k+gap)) for k in range(1, V+1))
        return s.numerator+s.denominator
    if target == "constrained_digit_count":
        lo, hi = (int(x) for x in re.search(r"from (\d+) to (\d+)", c).groups())
        return sum(1 for x in range(lo, hi+1) if sum(int(d) for d in str(x)) == V)
    if target == "inclusion_exclusion_3set":
        a,b,d = (int(x) for x in re.search(r"divisible by (\d+), (\d+), or (\d+)", c).groups())
        return (V//a+V//b+V//d-V//_lcm(a,b)-V//_lcm(a,d)-V//_lcm(b,d)+V//_lcm(a,_lcm(b,d)))
    if target == "perfect_square_divisible":
        div = int(re.search(r"divisible by (\d+)", c).group(1)); rd = int(div**0.5); cnt = 0; k = 1
        while (rd*k)**2 < V: cnt += 1; k += 1
        return cnt
    if target == "multi_constraint_square":
        d = int(re.search(r"divisible by (\d+)", c).group(1))
        last = int(re.search(r"end in the digit (\d+)", c).group(1)); cnt = 0; k = 1
        while k*k < V:
            if (k*k) % d == 0 and (k*k) % 10 == last: cnt += 1
            k += 1
        return cnt
    if target == "equalization_fraction":
        n, dn = (int(x) for x in re.search(r"one is (\d+)/(\d+) full", c).groups())
        pour = 1 - ((V-1)+Fraction(n, dn))/V
        return pour.numerator+pour.denominator
    if target == "complement_prob_mn":
        n, dn = (int(x) for x in re.search(r"exceeds (\d+)/(\d+)", c).groups())
        thr = Fraction(n, dn); r = 1
        while 1 - Fraction((V-1)**r, V**r) <= thr:
            r += 1
            if r > 60: return None
        return r
    return None

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
