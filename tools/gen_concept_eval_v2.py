#!/usr/bin/env python3
"""
Concept-transfer eval v2 — a cleaner gate for "does the model learn the CONCEPT or the TEMPLATE?"

Fixes the three confounds found in the v1 eval (data/concept_transfer_eval.json):
  1. v1's C_alternate asked a DIFFERENT question (complement / count), so its delta did not
     measure wording-transfer. -> v2 uses ONLY same-task rewordings (identical gold across framings).
  2. v1 had 3 framings; -> v2 has 5 same-task framings per concept (per the "5 phrasings" intuition).
  3. v1's cdc was ceilinged at BASE (18-24/24), so it could not show transfer. -> v2 raises cdc
     difficulty (bigger M, deeper threshold) to restore headroom.
Also more instances/cell for tighter error bars (default 12 instances x 5 framings x 3 concepts).

DESIGN: each instance draws ONE underlying numeric problem (so the gold is identical) and renders
it in all 5 framings. A_original matches the v1 training template (anchor). The transfer read is
then: Δtrained(B..E) vs Δtrained(A). If B..E rise ~like A -> concept; if only A -> template.

Concepts are the 3 the abl3 / ckpt-108 model was trained on (ie3 / cdc / cmp); cdc is the
ceiling-control made harder. Golds are computed by inline oracles (same as v1).

Run:
  python3 tools/gen_concept_eval_v2.py                      # -> data/concept_transfer_eval_v2.json
  # then sample BASE and ckpt-108 on a GPU box (handoff), e.g.
  bash tools/gen_holdout.sh checkpoint/abl3_v12_200/checkpoint-108 data/concept_transfer_eval_v2.json 2048
Read it: Δtrained on B..E ≈ Δ on A  -> concept learning ; B..E << A -> template memorization.
"""
import os, json, random, math
random.seed(7)
N = int(os.environ.get("N_PER_CELL", "12"))   # underlying instances per concept (shared across framings)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "concept_transfer_eval_v2.json")

def lcm(a, b): return a * b // math.gcd(a, b)
def ie_count(U, a, b, c):
    return (U//a + U//b + U//c - U//lcm(a,b) - U//lcm(a,c) - U//lcm(b,c) + U//lcm(lcm(a,b),c))
def divisors(M):
    ds, i = [], 1
    while i*i <= M:
        if M % i == 0:
            ds.append(i)
            if i != M//i: ds.append(M//i)
        i += 1
    return sorted(ds)
def sos_pairs(U):
    out, a = [], 1
    while 2*a*a <= U:
        r = U - a*a; b = int(round(r**0.5))
        if b >= a and b*b == r: out.append((a, b))
        a += 1
    return out

P = []
def add(concept, framing, text, gold):
    P.append({"problem": text, "answer": str(gold),
              "skeleton_type": f"{concept}__{framing}", "concept": concept, "framing": framing})

FRAMINGS = ["A_original", "B_wordproblem", "C_setbuilder", "D_scenario", "E_paraphrase"]

# ---------- ie3: count integers in [1,U] divisible by a, b, or c  (gold = cnt) ----------
seen, made = set(), 0
while made < N:
    U = random.randint(200, 800); a, b, c = sorted(random.sample([2,3,4,5,6,7], 3))
    if (U,a,b,c) in seen: continue
    seen.add((U,a,b,c)); g = ie_count(U,a,b,c)
    add("ie3","A_original",   f"How many positive integers from 1 to {U} are divisible by {a}, {b}, or {c}?", g)
    add("ie3","B_wordproblem",f"A hallway has {U} lockers numbered 1 through {U}. A locker gets a sticker if its "
                              f"number is divisible by {a}, {b}, or {c}. How many lockers get a sticker?", g)
    add("ie3","C_setbuilder", f"Let S = {{ n : 1 ≤ n ≤ {U}, and n is divisible by {a}, {b}, or {c} }}. "
                              f"What is |S|?", g)
    add("ie3","D_scenario",   f"A counter starts at 0 and steps through the integers 1, 2, …, {U}. It clicks "
                              f"on each integer that is a multiple of {a}, {b}, or {c}. How many clicks total?", g)
    add("ie3","E_paraphrase", f"Count the integers between 1 and {U} inclusive that are a multiple of at least one "
                              f"of {a}, {b}, and {c}.", g)
    made += 1

# ---------- cdc: count divisors of M greater than X  (gold = gt) — harder than v1 for headroom ----------
seen, made = set(), 0
while made < N:
    # bigger, divisor-rich M and a deeper threshold so base must actually enumerate (no ceiling)
    M = (2**random.randint(3,5)) * (3**random.randint(1,3)) * (5**random.randint(1,2)) * random.choice([7,11,13])
    if not (3000 <= M <= 30000): continue
    ds = divisors(M)
    cand = [d for d in ds if 8 <= d <= 60]
    if len(ds) < 12 or not cand: continue
    X = random.choice(cand)
    if (M,X) in seen: continue
    seen.add((M,X)); g = sum(1 for d in ds if d > X)
    add("cdc","A_original",   f"How many positive divisors of {M} are greater than {X}?", g)
    add("cdc","B_wordproblem",f"{M} identical tiles are arranged in a single rectangle; the number of tiles per row "
                              f"must divide {M} exactly. In how many ways can this be done with more than {X} tiles "
                              f"per row?", g)
    add("cdc","C_setbuilder", f"How many positive integers d satisfy both d divides {M} and d > {X}?", g)
    add("cdc","D_scenario",   f"A coach must split {M} players into equal-sized groups, and the group size has to "
                              f"divide {M} evenly. How many allowed group sizes are larger than {X}?", g)
    add("cdc","E_paraphrase", f"Among the positive divisors of {M}, how many exceed {X}?", g)
    made += 1

# ---------- cmp: sum of (a+b) over pairs a<=b with a^2+b^2=U  (gold = s) ----------
seen, made = set(), 0
while made < N:
    a0 = random.randint(2,15); b0 = random.randint(a0,18); U = a0*a0 + b0*b0
    if not (50 <= U <= 650) or U in seen: continue
    pairs = sos_pairs(U)
    if not pairs: continue
    seen.add(U); g = sum(a+b for a,b in pairs)
    add("cmp","A_original",   f"Find every pair of positive integers a ≤ b with a² + b² = {U}; add up "
                              f"(a+b) over all such pairs.", g)
    add("cmp","B_wordproblem",f"An integer-sided right triangle has legs a ≤ b and its hypotenuse squared equals "
                              f"{U}. Over all such triangles, find the total of (a+b).", g)
    add("cmp","C_setbuilder", f"Let T = {{ (a,b) : 1 ≤ a ≤ b and a² + b² = {U} }}. Compute the sum "
                              f"of (a+b) over all (a,b) in T.", g)
    add("cmp","D_scenario",   f"On a grid, mark every point (a,b) with 1 ≤ a ≤ b that lies exactly √{U} "
                              f"from the origin. Add up a+b over all marked points.", g)
    add("cmp","E_paraphrase", f"For each way to write {U} as a² + b² with integers 1 ≤ a ≤ b, take "
                              f"a+b; report the total over all such ways.", g)
    made += 1

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(P, open(OUT, "w"), ensure_ascii=False, indent=1)
from collections import Counter
c = Counter((p["concept"], p["framing"]) for p in P)
print(f"wrote {len(P)} problems -> {OUT}  (framings: {', '.join(FRAMINGS)})")
for k in sorted(c): print(f"  {k[0]:4} {k[1]:14} {c[k]}")
