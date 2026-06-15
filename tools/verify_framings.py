#!/usr/bin/env python3
"""
Gold-invariance verifier for multi-framing depth-0 concepts.

Each depth-0 generator picks one of N surface framings via random.choice([...]) but
computes the gold from the PARAMS, so the gold is phrasing-invariant *by construction*.
The real risk when we expand 5 -> 10 framings is authoring a framing whose ENGLISH asks
a DIFFERENT quantity than `ans` computes -> we'd silently train on wrong golds (the #1
project risk). This tool catches that: for each concept it samples many problems (hitting
every framing), independently RE-SOLVES each one straight from the text, and asserts the
recompute equals the stored gold. A framing that asks the wrong thing shows up as a
mismatch concentrated on that one framing.

It also reports how many distinct framings were seen (should equal the authored count) and
flags any framing the recomputer could not parse (a robustness gap, not necessarily a gold
bug). Add a concept by registering a recomputer in RECOMPUTERS; nothing else changes.

  INJECTOR=generate/skeleton_injector_v12.py python3 tools/verify_framings.py [--n 4000] [--concept X]
"""
import os, re, sys, math, argparse, importlib.util
from collections import defaultdict, Counter
from fractions import Fraction
from functools import reduce

INJ = os.environ.get("INJECTOR", "generate/skeleton_injector_v13.py")

def _ints(s):
    return [int(x) for x in re.findall(r"-?\d+", s)]

def _lcm(a, b): return a * b // math.gcd(a, b)

# ---- per-concept recomputers: text -> recomputed answer (or None if unparseable) ----

def rc_modular_exponent(t):
    m_pow = (re.search(r"(\d+)\s*\^\s*(\d+)", t)
             or re.search(r"(\d+)\s+raised to the\s+(\d+)", t)
             or re.search(r"(\d+)\s+to the power\s+(\d+)", t))
    if not m_pow: return None
    a, e = int(m_pow.group(1)), int(m_pow.group(2))
    # the modulus is the integer NOT inside the a^e span
    s, en = m_pow.span()
    outside = [int(x.group()) for x in re.finditer(r"\d+", t) if x.start() >= en or x.end() <= s]
    if len(outside) != 1: return None
    return pow(a, e, outside[0])

def rc_inclusion_exclusion_3set(t):
    nums = _ints(t)
    if not nums: return None
    U = max(nums)
    divs = sorted(set(n for n in nums if n != U and n != 1))
    if len(divs) != 3: return None
    a, b, c = divs
    return (U//a + U//b + U//c - U//_lcm(a,b) - U//_lcm(a,c) - U//_lcm(b,c)
            + U//_lcm(a, _lcm(b, c)))

def _two_ints_after(t, *keys):
    lo = min((t.find(k) for k in keys if t.find(k) >= 0), default=-1)
    if lo < 0: return None
    got = re.findall(r"\d+", t[lo:])
    return (int(got[0]), int(got[1])) if len(got) >= 2 else None

def rc_lcm_gcd_system(t):
    tl = t.lower()
    pL = _two_ints_after(tl, "lcm", "least common multiple")
    qG = _two_ints_after(tl, "gcd", "greatest common divisor")
    if not pL or not qG: return None
    p, L = pL; q, G = qG
    for n in range(1, L + 1):
        if _lcm(n, p) == L and math.gcd(n, q) == G:
            return n
    return None

def rc_alternating_cubes(t):
    nums = _ints(t)            # cube exponents are unicode superscripts, not ASCII digits
    if not nums: return None
    top = max(nums)
    return sum((2*k)**3 - (2*k-1)**3 for k in range(1, top//2 + 1))

def rc_complex_eq_solcount(t):
    nums = _ints(t)            # the only integer is the exponent n
    if len(nums) != 1: return None
    return nums[0] + 2

def rc_custom_binary_op(t):
    nums = _ints(t)            # the operator def uses letters -> the only ints are a,b,c,d
    if len(nums) != 4: return None
    op = lambda x, y: x + y + x*y
    a, b, c, d = nums
    return op(op(op(a, b), c), d)

def rc_perfect_square_divisible(t):
    nums = _ints(t)
    if len(nums) != 2: return None
    limit, div = max(nums), min(nums)
    rd = math.isqrt(div); cnt = 0; k = 1
    while (rd*k)**2 < limit: cnt += 1; k += 1
    return cnt

def rc_triangular_filter_count(t):
    # anchor on the phrases (example sequences like "1, 3, 6, 10" must not be parsed as params)
    lim = re.search(r"(?:less than|below|under)\s+(\d+)", t)
    k = re.search(r"(?:divisible by|multiples? of)\s+(\d+)", t)
    if not lim or not k: return None
    lim, k = int(lim.group(1)), int(k.group(1))
    cnt = 0; n = 1
    while n*(n+1)//2 < lim:
        if (n*(n+1)//2) % k == 0: cnt += 1
        n += 1
    return cnt

def rc_count_pythagorean(t):
    nums = _ints(t)
    if not nums: return None
    H = max(nums); cnt = 0
    for a in range(1, H+1):
        for b in range(a, H+1):
            c2 = a*a + b*b; c = math.isqrt(c2)
            if c*c == c2 and c <= H: cnt += 1
    return cnt

def _ndiv(n):
    c = 0; i = 1
    while i*i <= n:
        if n % i == 0: c += 1 if i*i == n else 2
        i += 1
    return c

def rc_box_diagonal_sq(t):
    m = re.search(r"exactly\s+(\d+)\s+(?:positive\s+)?divisors", t)
    if not m: return None
    k = int(m.group(1)); dims = []; nn = 2
    while len(dims) < 3 and nn < 500:
        if _ndiv(nn) == k: dims.append(nn)
        nn += 1
    if len(dims) < 3: return None
    a, b, c = dims
    return a*a + b*b + c*c

def rc_lattice_points_circle(t):
    R = None
    m = re.search(r"radius\s+(\d+)", t) or re.search(r"distance\s+(\d+)", t)
    if m: R = int(m.group(1))
    if R is None:
        m = re.search(r"(\d+)²", t)       # a literal "{R}²" (x²/y² have letters, not digits)
        if m: R = int(m.group(1))
    if R is None:
        m = re.search(r"[≤<]=?\s*(\d+)", t)  # "x²+y² <= R*R"  -> the bound is R²
        if m: R = math.isqrt(int(m.group(1)))
    if R is None: return None
    return sum(1 for x in range(-R, R+1) for y in range(-R, R+1) if x*x + y*y <= R*R)

def rc_ordered_triple_constraint(t):
    nums = _ints(t)
    if not nums: return None
    N = max(nums)
    return sum(1 for a in range(0, N) for b in range(a+1, N) for c in range(b+1, N+1)
               if a + b + c == N)

def _smallest_with_ndiv(D, cap=10**6):
    n = 1
    while n <= cap:
        if _ndiv(n) == D: return n
        n += 1
    return None

def rc_algebraic_system_2eq(t):
    rows = re.findall(r"(\d+)x\+(\d+)y\+(\d+)z=(\d+)", t)
    if len(rows) != 3: return None
    A = [[int(rows[i][j]) for j in range(3)] for i in range(3)]
    Dv = [int(rows[i][3]) for i in range(3)]
    def det3(M):
        return (M[0][0]*(M[1][1]*M[2][2]-M[1][2]*M[2][1])
                - M[0][1]*(M[1][0]*M[2][2]-M[1][2]*M[2][0])
                + M[0][2]*(M[1][0]*M[2][1]-M[1][1]*M[2][0]))
    det = det3(A)
    if det == 0: return None
    tot = Fraction(0)
    for col in range(3):
        M = [r[:] for r in A]
        for i in range(3): M[i][col] = Dv[i]
        tot += Fraction(det3(M), det)
    return int(tot) if tot.denominator == 1 else None

def rc_log_laws(t):
    bm = re.search(r"log_(\d+)", t)
    if not bm: return None
    exps = [int(e) for e in re.findall(rf"{bm.group(1)}\^(\d+)", t)]
    if len(exps) != 3: return None
    return exps[0] + exps[1] - exps[2]

def rc_prime_power_divisors(t):
    m = re.search(r"(?:exactly|precisely)\s+(\d+)", t)   # ignore the '0' in "n>0"
    if not m: return None
    return _smallest_with_ndiv(int(m.group(1)))

def rc_complex_modulus_power(t):
    nums = _ints(t)
    if not nums: return None
    N = max(nums); rt = math.isqrt(N)
    return sum(a+b for a in range(1, rt+1) for b in range(a, rt+1) if a*a+b*b == N)

def rc_roots_of_unity_sum(t):
    vals = [n for n in _ints(t) if n != 1]
    if len(set(vals)) < 2: return None
    return reduce(math.gcd, vals)

def rc_complement_prob_mn(t):
    fm = re.search(r"(\d+)-sided", t); tm = re.search(r"(\d+)\s*/\s*(\d+)", t)
    if not (fm and tm): return None
    faces = int(fm.group(1)); thr = Fraction(int(tm.group(1)), int(tm.group(2)))
    r = 1
    while 1 - Fraction((faces-1)**r, faces**r) <= thr:
        r += 1
        if r > 50: return None
    return r

def rc_multi_constraint_square(t):
    lim = re.search(r"(?:less than|smaller than|below|under|<)\s*(\d+)", t)
    dm = re.search(r"(?:divisible by|multiples? of)\s*(\d+)", t)
    lastm = re.search(r"(?:end(?:s|ing)?(?:\s+(?:with|in))?\s+(?:the\s+)?(?:digit\s+)?"
                      r"|last digit(?:\s+is)?\s+|units digit\s+)(\d+)", t)
    if not (lim and dm and lastm): return None
    limit, d, last = int(lim.group(1)), int(dm.group(1)), int(lastm.group(1))
    cnt = 0; k = 1
    while k*k < limit:
        if (k*k) % d == 0 and (k*k) % 10 == last: cnt += 1
        k += 1
    return cnt

def rc_constrained_digit_count(t):
    vals = sorted(set(_ints(t)))
    if len(vals) < 3: return None
    target, lo, hi = vals[0], vals[1], vals[-1]
    return sum(1 for x in range(lo, hi+1) if sum(int(c) for c in str(x)) == target)

def rc_equalization_fraction(t):
    gm = re.search(r"(\d+)\s+(?:identical\s+|equal\s+)?glasses", t)
    fm = re.search(r"(\d+)\s*/\s*(\d+)", t)   # only digit-fraction is fn; "m/n" uses letters
    if not (gm and fm): return None
    g = int(gm.group(1)); fn = Fraction(int(fm.group(1)), int(fm.group(2)))
    pour = 1 - ((g-1) + fn) / g
    return pour.numerator + pour.denominator

RECOMPUTERS = {
    "modular_exponent": rc_modular_exponent,
    "algebraic_system_2eq": rc_algebraic_system_2eq,
    "log_laws": rc_log_laws,
    "prime_power_divisors": rc_prime_power_divisors,
    "complex_modulus_power": rc_complex_modulus_power,
    "roots_of_unity_sum": rc_roots_of_unity_sum,
    "complement_prob_mn": rc_complement_prob_mn,
    "multi_constraint_square": rc_multi_constraint_square,
    "constrained_digit_count": rc_constrained_digit_count,
    "equalization_fraction": rc_equalization_fraction,
    "inclusion_exclusion_3set": rc_inclusion_exclusion_3set,
    "lcm_gcd_system": rc_lcm_gcd_system,
    "alternating_cubes": rc_alternating_cubes,
    "complex_eq_solcount": rc_complex_eq_solcount,
    "custom_binary_op": rc_custom_binary_op,
    "perfect_square_divisible": rc_perfect_square_divisible,
    "triangular_filter_count": rc_triangular_filter_count,
    "count_pythagorean": rc_count_pythagorean,
    "box_diagonal_sq": rc_box_diagonal_sq,
    "lattice_points_circle": rc_lattice_points_circle,
    "ordered_triple_constraint": rc_ordered_triple_constraint,
}

def _norm(s):  # framing fingerprint: digits -> #
    return re.sub(r"\s+", " ", re.sub(r"-?\d+", "#", s)).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4000)
    ap.add_argument("--concept", default=None)
    args = ap.parse_args()

    spec = importlib.util.spec_from_file_location("inj", INJ)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    import random; random.seed(12345)
    gen = {nm: fn for nm, fn, _ in mod.REGISTRY}

    targets = [args.concept] if args.concept else list(RECOMPUTERS)
    overall_ok = True
    for concept in targets:
        if concept not in RECOMPUTERS:
            print(f"  {concept}: no recomputer registered -> SKIP"); continue
        rc = RECOMPUTERS[concept]; fn = gen[concept]
        per = defaultdict(lambda: {"n": 0, "bad": 0, "unparsed": 0})
        total = mism = unp = 0
        for _ in range(args.n):
            r = fn()
            if r is None: continue
            text, gold = r[0], int(r[1])
            key = _norm(text); per[key]["n"] += 1; total += 1
            got = rc(text)
            if got is None:
                per[key]["unparsed"] += 1; unp += 1
            elif got != gold:
                per[key]["bad"] += 1; mism += 1
        n_fr = len(per)
        status = "PASS" if (mism == 0 and unp == 0) else "FAIL"
        if status != "PASS": overall_ok = False
        print(f"\n{concept}: {status}  | framings seen {n_fr} | samples {total} | "
              f"gold-mismatch {mism} | unparsed {unp}")
        for key in sorted(per, key=lambda k: -per[k]["n"]):
            d = per[key]
            flag = "" if (d["bad"] == 0 and d["unparsed"] == 0) else "  <-- PROBLEM"
            print(f"    n={d['n']:4} bad={d['bad']} unparsed={d['unparsed']}  {key[:88]}{flag}")
    print("\n" + ("ALL PASS" if overall_ok else "FAILURES PRESENT"))
    sys.exit(0 if overall_ok else 1)

if __name__ == "__main__":
    main()
