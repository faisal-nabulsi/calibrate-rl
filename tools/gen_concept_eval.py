#!/usr/bin/env python3
"""
Concept-transfer eval — does the 3-concept model learn the CONCEPT or just the TEMPLATE?

Same 3 concepts (ie3 / cdc / cmp), MATCHED difficulty (same number ranges as abl3_holdout),
but three surface framings:
  A_original    = the training template          (ANCHOR — should reproduce the held-out +0.22)
  B_wordproblem = same math, different scenario   (transfer to a richer framing)
  C_alternate   = same concept, asked differently (complement / count — cleanest concept test)

Run:
  python3 tools/gen_concept_eval.py                 # -> data/concept_transfer_eval.json
  bash tools/gen_holdout.sh checkpoint/abl3_v12_200/checkpoint-108 data/concept_transfer_eval.json 1024

Read it: if Δtrained on B/C ≈ Δ on A -> concept learning; if B/C << A -> template memorization.
"""
import os, json, random, math
random.seed(7)
N = int(os.environ.get("N_PER_CELL", "8"))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "concept_transfer_eval.json")

def lcm(a, b): return a * b // math.gcd(a, b)
def ie_count(U, a, b, c):
    return (U//a + U//b + U//c - U//lcm(a,b) - U//lcm(a,c) - U//lcm(b,c) + U//lcm(lcm(a,b),c))
def divisors(M):
    ds = []; i = 1
    while i*i <= M:
        if M % i == 0:
            ds.append(i)
            if i != M//i: ds.append(M//i)
        i += 1
    return sorted(ds)
def sos_pairs(U):
    out = []; a = 1
    while 2*a*a <= U:
        r = U - a*a; b = int(round(r**0.5))
        if b >= a and b*b == r: out.append((a, b))
        a += 1
    return out

P = []
def add(concept, framing, text, gold):
    P.append({"problem": text, "answer": str(gold),
              "skeleton_type": f"{concept}__{framing}", "concept": concept, "framing": framing})

# ---------- ie3: count multiples of a,b,c in [1,U] ----------
seen = set(); made = 0
while made < N:
    U = random.randint(200, 800); a, b, c = sorted(random.sample([2,3,4,5,6,7], 3))
    if (U,a,b,c) in seen: continue
    seen.add((U,a,b,c)); cnt = ie_count(U,a,b,c)
    add("ie3", "A_original",
        f"How many positive integers from 1 to {U} are divisible by {a}, {b}, or {c}?", cnt)
    add("ie3", "B_wordproblem",
        f"A hallway has {U} lockers numbered 1 through {U}. A locker gets a sticker if its number is "
        f"divisible by {a}, {b}, or {c}. How many lockers get a sticker?", cnt)
    add("ie3", "C_alternate",
        f"How many integers from 1 to {U} are divisible by none of {a}, {b}, or {c}?", U - cnt)
    made += 1

# ---------- cdc: count divisors of M past a threshold X ----------
seen = set(); made = 0
while made < N:
    M = (2**random.randint(2,4)) * (3**random.randint(1,2)) * (5**random.randint(1,2)) * (random.choice([1,7,11,13]))
    if not (500 <= M <= 2600): continue
    ds = divisors(M)
    cand = [d for d in ds if 5 <= d <= 40]
    if len(ds) < 8 or not cand: continue
    X = random.choice(cand)
    if (M,X) in seen: continue
    seen.add((M,X))
    gt = sum(1 for d in ds if d > X); le = sum(1 for d in ds if d <= X)
    add("cdc", "A_original", f"How many positive divisors of {M} are greater than {X}?", gt)
    add("cdc", "B_wordproblem",
        f"{M} identical tiles are arranged in a single rectangle; the number of tiles per row must divide "
        f"{M} exactly. In how many ways can this be done with more than {X} tiles per row?", gt)
    add("cdc", "C_alternate", f"How many positive divisors of {M} are {X} or fewer?", le)
    made += 1

# ---------- cmp: integer solutions of a^2 + b^2 = U ----------
seen = set(); made = 0
while made < N:
    a0 = random.randint(2,15); b0 = random.randint(a0,18); U = a0*a0 + b0*b0
    if not (50 <= U <= 650) or U in seen: continue
    pairs = sos_pairs(U)
    if not pairs: continue
    seen.add(U); s = sum(a+b for a,b in pairs); k = len(pairs)
    add("cmp", "A_original",
        f"Find every pair of positive integers a ≤ b with a² + b² = {U}; add up (a+b) over all such pairs.", s)
    add("cmp", "B_wordproblem",
        f"An integer-sided right triangle has legs a ≤ b and its hypotenuse squared equals {U}. "
        f"Over all such triangles, find the total of (a+b).", s)
    add("cmp", "C_alternate",
        f"In how many ways can {U} be written as a² + b² with positive integers a ≤ b?", k)
    made += 1

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(P, open(OUT, "w"), ensure_ascii=False, indent=1)
from collections import Counter
c = Counter((p["concept"], p["framing"]) for p in P)
print(f"wrote {len(P)} problems -> {OUT}")
for k in sorted(c): print(f"  {k[0]:4} {k[1]:14} {c[k]}")
