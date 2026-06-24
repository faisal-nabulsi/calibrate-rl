#!/usr/bin/env python3
"""
Prototype + validate the rest of the DEPTH-2 recognition-trap library before integrating:
  - SEAM-TWIN (depth-1.5 seam-presence): a chain-like surface with NO real chain — the computed
    value is a RED HERRING; the target is self-contained. The naive "embedded value -> plug it in"
    reflex (what depth-1/1.5 trains) yields a SPECIFIC wrong number; gold = target-only. Forces the
    DECISION "is there a seam?", the recognition depth-1 never had to make.
  - Family B (lattice/region): count interior lattice points of a triangle. Naive "the count = the
    AREA" (a*b/2) overcounts; gold = exact enumeration (Pick: I = A - B/2 + 1).
  - Family C (finite-state process): count +1/+2 walks 1->n that AVOID a set of trapped squares.
    Naive ignores the traps -> the plain Fibonacci count (a specific wrong number > gold); gold = DP
    over the trapped squares. The "process / first-passage" axis, distinct from A's static count.
  - Family D (adversarial logic): count T/F assignments to n statements satisfying a set of
    implications. Naive = 2^n (ignore the constraints); gold = exact satisfying count.

Each must clear the SAME bar Family A did: exact oracle (independent recompute == gold), naive!=gold
(trap real), answer diversity (top3 <= 0.30). NO LLM judge. Whatever doesn't clear it is REJECTED
(documented), like pid-1 pairing — better found here than in a 6h sample.
"""
import argparse, math, random, re
from collections import Counter
from math import isqrt


def _ndiv(n):
    return sum(1 for d in range(1, isqrt(n) + 1) if n % d == 0) * 2 - (1 if isqrt(n) ** 2 == n else 0)


# ── SEAM-TWIN: red-herring chain (gold = target-only; trap = plug the red herring in) ──────────
def gen_seam_twin(rng):
    for _ in range(60):
        D = rng.randint(12, 200)
        g = _ndiv(D)                                   # the RED HERRING value (small, 2..~12)
        a, e, m = rng.randint(2, 9), rng.randint(6, 16), rng.randint(50, 200)
        gold = pow(a, e, m)                            # self-contained: g is NOT used
        trap = pow(a, g, m)                            # the always-chain reflex: plug g into the exponent
        if gold == trap:
            continue
        prob = (f"Let g be the number of positive divisors of {D}. "
                f"What is the remainder when {a}^{e} is divided by {m}?")
        return prob, gold, trap
    return None


# ── Family B: interior lattice points of a SHEARED triangle (naive = area, shear-invariant) ─────
def _tri_interior(a, b, c):
    return sum(1 for y in range(1, b) for x in range(min(0, c), max(a, c) + 1)
               if x * b - c * y > 0 and a * b - x * b + c * y - a * y > 0)

def gen_family_b(rng):
    for _ in range(60):
        a, b, c = rng.randint(6, 16), rng.randint(6, 16), rng.randint(-8, 16)
        gold = _tri_interior(a, b, c)
        naive = a * b // 2                              # "the count is the area" (= a*b/2 for any shear c)
        if gold < 2 or naive == gold:
            continue
        prob = (f"How many points with integer coordinates lie strictly inside the triangle whose "
                f"vertices are (0,0), ({a},0), and ({c},{b})?")
        return prob, gold, naive
    return None


# ── Family C: +1/+2 walks 1->n avoiding trapped squares (naive = plain Fibonacci) ──────────────
def _walks(n, F):
    ways = [0] * (n + 1)
    ways[1] = 1
    for i in range(2, n + 1):
        if i in F:
            ways[i] = 0
        else:
            ways[i] = ways[i - 1] + (ways[i - 2] if i - 2 >= 1 else 0)
    return ways[n]

def gen_family_c(rng):
    for _ in range(60):
        n = rng.randint(12, 20)
        F = set(rng.sample(range(2, n), rng.randint(2, 4)))   # trapped interior squares (never 1 or n)
        gold = _walks(n, F)
        naive = _walks(n, set())                              # ignore the traps -> Fibonacci(n)
        if gold < 2 or naive == gold:
            continue
        fl = ", ".join(map(str, sorted(F)))
        prob = (f"A token starts on square 1 of a row of {n} squares and moves forward 1 or 2 squares "
                f"each step, never overshooting square {n}. Squares {fl} are blocked and may not be "
                f"landed on. How many distinct sequences of moves bring the token to exactly square {n}?")
        return prob, gold, naive
    return None


# ── Family D: # T/F assignments satisfying implications a -> b (naive = 2^n) ────────────────────
def _sat_count(n, implications):
    cnt = 0
    for mask in range(1 << n):
        v = [(mask >> i) & 1 for i in range(n)]
        if all((not v[x]) or v[y] for x, y in implications):   # x->y : if x true then y true
            cnt += 1
    return cnt

def gen_family_d(rng):
    for _ in range(60):
        n = rng.randint(4, 6)
        k = rng.randint(2, 4)
        imp = set()
        while len(imp) < k:
            x, y = rng.sample(range(n), 2)
            imp.add((x, y))
        gold = _sat_count(n, imp)
        naive = 1 << n                                          # ignore the constraints
        if gold < 2 or naive == gold:
            continue
        names = [chr(ord('A') + i) for i in range(n)]
        clauses = "; ".join(f"if {names[x]} is true then {names[y]} is true" for x, y in sorted(imp))
        prob = (f"Each of the statements {', '.join(names)} is either true or false, subject to: {clauses}. "
                f"How many of the {1<<n} possible truth-assignments satisfy all of these conditions?")
        return prob, gold, naive
    return None


def report(name, genf, recompute, n=400, seed=1):
    rng = random.Random(seed)
    rows = []
    while len(rows) < n:
        r = genf(rng)
        if r:
            rows.append(r)
    bad = sum(1 for p, g, _ in rows if recompute(p) != g)
    trap = sum(1 for _, g, t in rows if g != t)
    golds = [g for _, g, _ in rows]
    cc = Counter(golds); top3 = sum(v for _, v in cc.most_common(3)) / len(golds)
    verdict = "OK" if (bad == 0 and trap == len(rows) and top3 <= 0.30) else "REJECT"
    print(f"[{name:10}] mismatch={bad}  trap={trap}/{len(rows)}  distinct={len(cc)}  top3={top3:.3f}  -> {verdict}")
    print(f"             e.g. {rows[0][0][:95]}  (gold={rows[0][1]}, trap={rows[0][2]})")


# ── independent recomputers (parse from text, re-solve) ────────────────────────────────────────
def rc_seam(p):
    a, e, m = (int(x) for x in re.search(r"when (\d+)\^(\d+) is divided by (\d+)", p).groups())
    return pow(a, e, m)

def rc_b(p):
    a, c, b = (int(x) for x in re.search(r"\((\d+),0\), and \((-?\d+),(\d+)\)", p).groups())
    return _tri_interior(a, b, c)

def rc_c(p):
    n = int(re.search(r"row of (\d+) squares", p).group(1))
    F = set(int(x) for x in re.search(r"Squares ([\d, ]+?) are blocked", p).group(1).split(", "))
    return _walks(n, F)

def rc_d(p):
    names = re.search(r"statements ([A-Z, ]+?) is either", p).group(1).replace(" ", "").split(",")
    idx = {nm: i for i, nm in enumerate(names)}
    imp = set((idx[x], idx[y]) for x, y in re.findall(r"if ([A-Z]) is true then ([A-Z]) is true", p))
    return _sat_count(len(names), imp)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=400); a = ap.parse_args()
    report("seam-twin", gen_seam_twin, rc_seam, a.n)
    report("family-B", gen_family_b, rc_b, a.n)
    report("family-C", gen_family_c, rc_c, a.n)
    report("family-D", gen_family_d, rc_d, a.n)
