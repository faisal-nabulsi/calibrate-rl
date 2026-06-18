#!/usr/bin/env python3
"""
Chain-target diversity scan (no GPU).

Goal: stop every chain ending in modular_exponent. A chain A->B stays answer-diverse
(passes the top-3 <= 0.30 gate) iff B is MULTI-INPUT -- we feed A's intermediate into ONE
of B's inputs and let B's OTHER inputs supply independent entropy. Single-input targets
(cdc-count, otc, ppd, count_pythagorean, ...) collapse: the answer becomes a deterministic
function of the one fed value.

This scans, for all 47 concepts as FEEDER x a menu of multi-input TARGET adapters:
  - feed-legality: does the feeder's output distribution land in the target input's envelope?
  - diversity:     top-3 answer share + #distinct of the COMPOSITE answer.
Then it greedily assigns each feeder a viable target, spreading targets to maximize variety,
and reports coverage (all 47 feeders used) + the target histogram. modexp is the fallback
ONLY when a feeder has no other viable target.

  INJECTOR=generate/skeleton_injector_v12.py python3 tools/scan_chain_targets.py
"""
import os, math, random, importlib.util
from fractions import Fraction
from collections import Counter, defaultdict

random.seed(7)
INJ = os.environ.get("INJECTOR", "generate/skeleton_injector_v12.py")
spec = importlib.util.spec_from_file_location("inj", INJ)
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)

def _lcm(a, b): return a*b//math.gcd(a, b)

# ---------------- target adapters: name -> (fed_lo, fed_hi, oracle(v)->ans|None, klass) ----------------
# oracle draws the target's OTHER inputs each call and returns the composite answer.
def t_modexp_exp(v):
    return pow(random.choice([2,3,5,6,7]), v, random.choice([50,97,221,264,503,997]))
def t_modexp_base(v):
    return pow(v, random.randint(2,6), random.choice([50,97,221,264,503,997]))
def t_algebraic_x(v):
    return v + random.randint(5,25) + random.randint(5,25)
def t_telescoping_N(v):
    gap = random.choice([2,3]); s = sum(Fraction(1,k*(k+gap)) for k in range(1,v+1))
    return s.numerator + s.denominator
def t_digit_target(v):
    lo = random.choice([1000,2000,3000]); hi = lo + random.choice([1000,2000])
    return sum(1 for x in range(lo,hi) if sum(int(c) for c in str(x)) == v)
def t_ie3_U(v):
    a,b,c = sorted(random.sample([2,3,4,5,6,7],3))
    return (v//a+v//b+v//c-v//_lcm(a,b)-v//_lcm(a,c)-v//_lcm(b,c)+v//_lcm(a,_lcm(b,c)))
def t_perfsq_limit(v):
    div = random.choice([4,9,16,25,36,49]); rd = int(div**.5); cnt = 0; k = 1
    while (rd*k)**2 < v: cnt += 1; k += 1
    return cnt
def t_multisquare_limit(v):
    d = random.choice([4,9]); last = random.choice([1,4,5,6,9]); cnt = 0; k = 1
    while k*k < v:
        if (k*k) % d == 0 and (k*k) % 10 == last: cnt += 1
        k += 1
    return cnt
def t_equalize_g(v):
    if v < 3: return None
    fn = random.choice([Fraction(1,3),Fraction(1,2),Fraction(1,4),Fraction(2,3),Fraction(3,4)])
    pour = 1 - ((v-1)+fn)/v
    return pour.numerator + pour.denominator
def t_complement_faces(v):
    if v < 3: return None
    thr = random.choice([Fraction(2,3),Fraction(3,4),Fraction(4,5)]); r = 1
    while 1 - Fraction((v-1)**r, v**r) <= thr:
        r += 1
        if r > 60: return None
    return r
# --- the 4 targets added in the more-targets pass (mirror skeleton_injector_v12 _ADAPT) ---
def _divisors(n):
    n = abs(n); ds = []
    for i in range(1, int(n**.5)+1):
        if n % i == 0: ds += [i, n//i]
    return set(ds)
def t_cmod(v):  # complex_modulus_power: |V+bi|^{2k} = (V^2+b^2)^k  (b,k entropy)
    b = random.choice([2,3,5,7,11,13,17,19,23,29]); k = random.choice([1,2])
    return (v*v + b*b)**k
def t_divsum(v):  # divisor_sum_filter: sum of odd/even divisors of V  (cond entropy; V supplies cardinality)
    cond = random.choice(["odd","even"])
    return sum(d for d in _divisors(v) if (d % 2 == 1) == (cond == "odd"))
def t_customop(v):  # custom_binary_op: ((V (+) b) (+) c), x(+)y = x+y+xy  (b,c entropy; V<=15 cap)
    b = random.choice(range(3,13)); c = random.choice(range(3,13)); op = lambda x,y: x+y+x*y
    return op(op(v,b),c)
def t_boxdiag(v):  # box_diagonal_sq: V^2+b^2+c^2  (b,c entropy; V^2 dominates -> near-unique)
    b = random.choice([2,3,4,5,6,7,8,9,11,13]); c = random.choice([2,3,4,5,6,7,8,9,11,13])
    return v*v + b*b + c*c

TARGETS = {  # target concept -> (fed_lo, fed_hi, oracle, fed input description)
    "modular_exponent@exp":      (2,   20,        t_modexp_exp,        "count -> exponent"),
    "modular_exponent@base":     (2,   5000,      t_modexp_base,       "value -> base"),
    "algebraic_system_2eq@x":    (1,   60,        t_algebraic_x,       "value -> one unknown x"),
    "telescoping_mn@N":          (3,   30,        t_telescoping_N,     "count -> term count N"),
    "constrained_digit_count@t": (5,   20,        t_digit_target,      "count -> digit-sum target"),
    "inclusion_exclusion_3set@U":(60,  9000,      t_ie3_U,             "value -> range bound U"),
    "perfect_square_divisible@L":(300, 200000,    t_perfsq_limit,      "value -> limit"),
    "multi_constraint_square@L": (600, 80000,     t_multisquare_limit, "value -> limit"),
    "equalization_fraction@g":   (3,   14,        t_equalize_g,        "count -> #glasses g"),
    "complement_prob_mn@faces":  (3,   30,        t_complement_faces,  "count -> #die faces"),
    # more-targets pass (now live in the 46-chain set; ranges from _ADAPT in skeleton_injector_v12):
    "complex_modulus_power@re":  (2,   120,       t_cmod,              "value -> real part of z"),
    "divisor_sum_filter@n":      (6,   30000,     t_divsum,            "value -> n (sum its divisors)"),
    "custom_binary_op@operand":  (2,   15,        t_customop,          "count -> one operand"),
    "box_diagonal_sq@edge":      (2,   500,       t_boxdiag,           "value -> one edge length"),
}
MODEXP = {"modular_exponent@exp", "modular_exponent@base"}  # fallbacks

GATE_TOP3, GATE_DISTINCT, LEGAL_FRAC = 0.30, 15, 0.60

# ---------------- feeders: all 47 concepts (28 depth-0 + 19 partners) ----------------
feeders = [nm for nm,_,_ in M.REGISTRY if not nm.startswith("chain_")]
gen = {nm: fn for nm,fn,_ in M.REGISTRY}
assert len(feeders) == 47, f"expected 47 concepts, got {len(feeders)}"

# sample each feeder's intermediate (its answer) distribution
OUT = {}
for nm in feeders:
    vals = []
    for _ in range(400):
        r = gen[nm]()
        if r and isinstance(r[1], int): vals.append(r[1])
    OUT[nm] = vals

def measure(feeder, tname):
    lo, hi, oracle, _ = TARGETS[tname]
    in_range = [o for o in OUT[feeder] if lo <= o <= hi]
    if not OUT[feeder] or len(in_range)/len(OUT[feeder]) < LEGAL_FRAC:
        return None
    ans = []
    for _ in range(700):
        a = oracle(random.choice(in_range))
        if a is not None and a >= 2: ans.append(a)
    if len(ans) < 100: return None
    c = Counter(ans); top3 = sum(v for _,v in c.most_common(3))/len(ans)
    return top3, len(set(ans))

# viable edges
viable = defaultdict(list)  # feeder -> [(tname, top3, distinct)]
for f in feeders:
    for t in TARGETS:
        m = measure(f, t)
        if m and m[0] <= GATE_TOP3 and m[1] >= GATE_DISTINCT:
            viable[f].append((t, m[0], m[1]))

# greedy diverse assignment: prefer a non-modexp target, spread by least-used
use = Counter()
assign = {}
# assign feeders with fewest options first (hardest to place), then by name for determinism
for f in sorted(feeders, key=lambda x: (len([t for t,_,_ in viable[x] if t not in MODEXP]), x)):
    opts = [t for t,_,_ in viable[f] if t not in MODEXP] or [t for t,_,_ in viable[f]]
    if not opts:  # nothing gate-passing -> modexp fallback by feeder magnitude
        med = sorted(OUT[f])[len(OUT[f])//2] if OUT[f] else 0
        opts = ["modular_exponent@base" if med > 40 else "modular_exponent@exp"]
    pick = min(opts, key=lambda t: (use[t], t))
    assign[f] = pick; use[pick] += 1

# ---------------- report ----------------
print(f"=== feeders: {len(feeders)} | viable target menu: {len(TARGETS)} ===\n")
print("TARGET HISTOGRAM (how the final step is distributed):")
for t,_ in use.most_common():
    print(f"  {t:32} {use[t]:2}  ({TARGETS[t][3] if t in TARGETS else ''})")
distinct_targets = len(set(c.split('@')[0] for c in use))
print(f"\n  distinct target CONCEPTS used: {distinct_targets}")
modexp_n = sum(v for k,v in use.items() if k in MODEXP)
print(f"  ending in modexp: {modexp_n}/{len(feeders)}  ({100*modexp_n/len(feeders):.0f}%)  vs 20/22 before")

no_diverse = [f for f in feeders if assign[f] in MODEXP and not [t for t,_,_ in viable[f] if t not in MODEXP]]
print(f"\n  feeders with NO non-modexp option (forced modexp): {len(no_diverse)}")
for f in no_diverse: print(f"     {f}  (out range {min(OUT[f]) if OUT[f] else '-'}..{max(OUT[f]) if OUT[f] else '-'})")

print(f"\n  COVERAGE: all {len(feeders)} concepts appear as a feeder -> {len(assign)==47}")
print("\nFULL ASSIGNMENT (feeder -> target):")
for f in sorted(assign): print(f"  {f:30} -> {assign[f]}")
