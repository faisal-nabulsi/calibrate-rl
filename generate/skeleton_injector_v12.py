#!/usr/bin/env python3
"""
skeleton_injector_v11.py — CalibrateRL v11 (derived from validated v10)

v11 CHANGES APPLIED (safe, verified):
  - custom_binary_op: 3 -> 4 operands, range 8-40 -> 3-12 (one extra
    composition step, smaller range to avoid overflow). Answers re-verified.
  - box_diagonal_sq: prompt clarity only ("smallest by value") to reduce
    selection noise. Math/answers unchanged.
  - arith_term_filter -> DEPTH1_PARTNERS. v10 calib: mean_pass 0.958,
    6/9 too_easy -> saturated standalone, promote to composition-only. CONFIRMED.

STAGED (commented, gated on 2048 re-sample):
  - algebraic_system_2eq range bump (x,y,z 2-15->5-25; coeffs 1-4->1-7).
    v10 calib mean_pass 0.831 EVEN WHILE truncation-suppressed (worst-hit
    concept). Bump likely justified; confirm un-truncated >=0.80 at 2048,
    then uncomment the staged lines in c_system().

DROPPED (data says leave it):
  - continued_fraction depth 5 -> 4: v10 calib mean_pass 0.411, 5/7 goldilocks
    -> already IN BAND. Cutting depth would push it too easy. The lone 0.00 is
    a truncation casualty that 2048 should fix. No edit.

NOT CHANGED (plan items already done or mismatched v10 code):
  - trapezoid_area, frobenius_stamps: already in DEPTH1_PARTNERS in v10.
  - divisor_sum_filter "widen pool": v10 uses randint(60,900), not a fixed
    pool; the v11 edit referenced a different concept. Left untouched.

--- original v7 header below ---
skeleton_injector_v7.py — CalibrateRL v7: BROAD COVERAGE via CONSTRAINTS

THESIS: v6 proved single-method concepts saturate for the 7B. v7 keeps broad
coverage (~60/83) but makes saturated concepts hard by ADDING CONSTRAINTS:
"compute X" -> "count/find X satisfying conditions". This is AMC-shaped
reasoning-difficulty (the 7B's best v6 concept, lcm_gcd_system, was already a
2-constraint problem), computed by ENUMERATION (correct by construction).

Structure:
  - SURVIVORS: v6 concepts already calibrated for 7B (kept as-is)
  - CONSTRAINT-RESCUED: saturated v5 concepts + a constraint (the core of v7)
  - RECOVERED: concepts for AMC problems first thought uncoverable (37,44,63,65,74,77,79)
  - GEOMETRY-COUNTING: constraint-counting geometry (Option 3)

Audit rules enforced: R1 no formula hints, R2 no trivial lookups, R3 integer
answers asserted, R4 answer not guessable from type, R5 >=5 phrasings,
R6 method inferred. Difficulty = constraint interaction + execution slip-risk.

NOTE: difficulty here is PREDICTED. The 7B calibration run is what confirms each
concept lands in band; nothing is claimed calibrated until measured.
"""
import argparse, json, math, os, random, sys
from fractions import Fraction
from collections import Counter
from itertools import combinations as Ccomb

# Phase 0 (auto-calibrator design §2a): difficulty knobs for the loop concepts
# (triangular_filter_count, log_laws, ordered_triple_constraint,
# constrained_subset_count + the abl3 set) are externalized to
# automation/calibrator/knobs/<concept>.json. K.randint/K.choice draw through
# the SAME random.* calls the inline literals used, so identical seeds yield
# identical problems (automation/calibrator/tests/test_knob_equivalence.py).
# Generator math is untouched; the calibrator edits JSON only, never this file.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from automation.calibrator.knob_loader import KnobBank
K = KnobBank()

def gcd(a,b):
    while b: a,b=b,a%b
    return abs(a)
def lcm(a,b): return a*b//gcd(a,b)
def ndiv(n):
    n=abs(n); c=0; i=1
    while i*i<=n:
        if n%i==0: c+=1 if i*i==n else 2
        i+=1
    return c
def sigma_full(n):
    n=abs(n); s=0; i=1
    while i*i<=n:
        if n%i==0:
            s+=i
            if i*i!=n: s+=n//i
        i+=1
    return s
def divisors(n):
    n=abs(n); ds=[]
    i=1
    while i*i<=n:
        if n%i==0:
            ds.append(i)
            if i*i!=n: ds.append(n//i)
        i+=1
    return sorted(ds)
def sieve(L):
    ok=[True]*(L+1); ok[0]=ok[1]=False
    for i in range(2,int(L**.5)+1):
        if ok[i]:
            for j in range(i*i,L+1,i): ok[j]=False
    return ok
ISPRIME=sieve(2_000_000)

# ── depth-1 oracle helpers ───────────────────────────────────────────────────
# Single source of truth for each concept's gold, so composites compose the SAME
# oracle (Addendum A.1: oracles compose -> composite gold exact by construction,
# no math re-derived). The parent generators below call these too; output stays
# byte-identical so test_knob_equivalence still passes.
def _loglaws_gold(e1, e2, e3):
    return e1 + e2 - e3
def _triples_gold(N):
    return sum(1 for a in range(N+1) for b in range(a+1, N+1) if (N-a-b) > b)
def _cdc_count(N, cond, t):
    """constrained_divisor_count oracle: # divisors of N that are odd / >t / <t.
    Same logic as c_divfilter; shared so composites with cdc as the target compose
    the exact gold (Addendum A.1). New helper — does NOT touch c_divfilter, so
    test_knob_equivalence still holds."""
    ds = divisors(N)
    if cond == "odd": return sum(1 for x in ds if x % 2 == 1)
    if cond == "gt":  return sum(1 for x in ds if x > t)
    return sum(1 for x in ds if x < t)            # lt
def _cdc_desc(cond, t):
    return "odd" if cond == "odd" else (f"greater than {t}" if cond == "gt" else f"less than {t}")
def _smallest_with_ndiv(D, cap=10**6):
    """Smallest positive integer with exactly D divisors, or None if it exceeds cap.
    The cap BOUNDS the search: prime / awkward D (envelope is [4,200]) have an
    enormous smallest-N (D=97 -> 2^96) and the bare `while ndiv(n)!=D: n+=1` loop
    would hang the generator — and autocalib edits the D knob unattended
    (charizard #42 flag 1). Consumes no RNG; for every in-use D the answer is well
    under cap, so output is byte-identical to the old loop (test_knob_equivalence)."""
    n = 1
    while ndiv(n) != D:
        n += 1
        if n > cap:
            return None
    return n

PROBLEMS=[]
REGISTRY=[]
# concepts that are irreducibly one-step at depth-0; reserved as depth-1 ride-along partners
DEPTH1_PARTNERS={'infinite_product_exp','unit_conversion_area','count_obtuse_triangles','primality_in_sequence','frobenius_stamps','vieta_pair_count','sum_of_squares','trapezoid_area','vieta_sumcubes','rate_closing','percent_compound','three_number_system','point_rotation','digit_count_bigprod','arith_series_sum','geo_first_exceed','mean_removal','distinct_product_count','arith_term_filter'}
# concepts whose answers are naturally small (count concepts) — exempt from the >=10 rule
SMALL_OK={"complex_eq_solcount","constrained_divisor_count","count_pythagorean",
          "ordered_triple_constraint","geo_first_exceed","primality_in_sequence",
          "distinct_product_count","polynomial_sign_intervals","triangular_filter_count"}
def concept(name, amc):
    def deco(fn): REGISTRY.append((name,fn,amc)); return fn
    return deco
def add(problem, answer, st):
    assert isinstance(answer,int), f"{st}: non-int {answer!r}"
    PROBLEMS.append({"problem":problem,"answer":str(answer),"skeleton_type":st,"depth":0})

# ===================================================================
# SURVIVORS — already calibrated for 7B in v6 (keep as-is)
# ===================================================================
@concept("lcm_gcd_system",[17])
def c_lcmgcd():
    n=random.randint(12,300); p=random.choice([12,18,24,36,45,48]); q=random.choice([15,30,45,60])
    L=lcm(n,p); G=gcd(n,q)
    cand=[m for m in range(1,L+1) if lcm(m,p)==L and gcd(m,q)==G]
    if not cand: return None
    return (random.choice([
        f"A positive integer n has lcm(n,{p})={L} and gcd(n,{q})={G}. What is the smallest such n?",
        f"The least common multiple of n and {p} is {L}; the greatest common divisor of n and {q} is {G}. Find the smallest n.",
        f"Find the smallest positive integer n with lcm(n,{p})={L} and gcd(n,{q})={G}.",
        f"For some positive integer n, lcm(n,{p}) equals {L} and gcd(n,{q}) equals {G}. What is the least possible n?",
        f"What is the minimum positive integer n satisfying both lcm(n,{p})={L} and gcd(n,{q})={G}?",
    ]), min(cand), "lcm_gcd_system")

@concept("alternating_cubes",[46])
def c_altcubes():
    top=random.choice(list(range(10,46,2)))
    val=sum((2*k)**3-(2*k-1)**3 for k in range(1,top//2+1))
    return (random.choice([
        f"Evaluate 2³ - 1³ + 4³ - 3³ + 6³ - 5³ + ... + {top}³ - {top-1}³.",
        f"What is (2³-1³) + (4³-3³) + ... + ({top}³-{top-1}³)?",
        f"Find the alternating sum of cubes 2³-1³+4³-3³+...+{top}³-{top-1}³.",
        f"Compute the sum where each pair is (even)³-(previous odd)³, up to {top}³-{top-1}³.",
        f"Add the differences of consecutive cubes 2³-1³, 4³-3³, ..., {top}³-{top-1}³.",
    ]), val, "alternating_cubes")

@concept("complex_eq_solcount",[48])
def c_complexsol():
    n=random.randint(3,12)
    return (random.choice([
        f"How many complex numbers z satisfy z^{n} = conjugate(z)?",
        f"Find the number of complex solutions to z^{n} = z̄ (z-bar is the conjugate).",
        f"How many complex z solve the equation z^{n} = conjugate of z?",
        f"Count the complex numbers z with z^{n} equal to its own conjugate.",
        f"The equation z^{n}=z̄ has how many complex solutions?",
    ]), n+2, "complex_eq_solcount")

@concept("custom_binary_op",[22,34,68])
def c_customop():
    # v11: 4 operands (one extra composition step), smaller range 3-12 to avoid overflow
    a=random.randint(3,12); b=random.randint(3,12); c=random.randint(3,12); d=random.randint(3,12)
    op=lambda x,y:x+y+x*y
    ans=op(op(op(a,b),c),d)
    if ans>200000: return None
    return (random.choice([
        f"Define x⊕y = x+y+xy for all integers. What is (({a}⊕{b})⊕{c})⊕{d}?",
        f"Let the operation x⊕y mean x+y+xy. Compute (({a}⊕{b})⊕{c})⊕{d}.",
        f"Using x⊕y = x+y+xy, evaluate {a}⊕{b}, then ⊕ that result with {c}, then ⊕ with {d}.",
        f"If a⊕b is defined as a+b+ab, what is (({a}⊕{b})⊕{c})⊕{d}?",
        f"With the rule x⊕y=x+y+xy, find the value of (({a}⊕{b})⊕{c})⊕{d}.",
    ]), ans, "custom_binary_op")

@concept("modular_exponent",[55])
def c_modexp():
    kn=K["modular_exponent"]
    a=kn.randint("a"); e=kn.randint("e"); m=kn.randint("m")
    ans=pow(a,e,m)
    if ans<5: return None
    return (random.choice([
        f"What is the remainder when {a}^{e} is divided by {m}?",
        f"Find {a}^{e} mod {m}.",
        f"Compute the remainder of {a} raised to the {e} upon division by {m}.",
        f"{a}^{e} is divided by {m}. What is the remainder?",
        f"Evaluate {a}^{e} modulo {m}.",
    ]), ans, "modular_exponent")

@concept("telescoping_mn",[14])
def c_tele():
    N=random.randint(6,16); gap=random.choice([2,3])
    s=sum(Fraction(1,k*(k+gap)) for k in range(1,N+1))
    ans=s.numerator+s.denominator
    if ans<20: return None
    return (random.choice([
        f"The sum 1/(1·{1+gap}) + 1/(2·{2+gap}) + ... + 1/({N}·{N+gap}) is m/n in lowest terms. Find m+n.",
        f"Express the sum of 1/(k(k+{gap})) for k=1..{N} as a reduced fraction m/n and give m+n.",
        f"Sum 1/(k(k+{gap})) from k=1 to {N}; write it as m/n irreducible and report m+n.",
        f"Compute 1/(1·{1+gap})+...+1/({N}·{N+gap}) as m/n in lowest terms; what is m+n?",
        f"The series sum of 1/(k(k+{gap})), k up to {N}, equals m/n reduced. Find m+n.",
    ]), ans, "telescoping_mn")

@concept("perfect_square_divisible",[59])
def c_psqdiv():
    div=random.choice([4,9,16,25,36,49]); limit=random.randint(1500,12000)
    rd=int(div**.5); cnt=0; k=1
    while (rd*k)**2<limit: cnt+=1; k+=1
    if cnt<5: return None
    return (random.choice([
        f"How many perfect squares less than {limit} are divisible by {div}?",
        f"Find the number of perfect squares below {limit} that are multiples of {div}.",
        f"How many squares of integers, each under {limit}, are divisible by {div}?",
        f"Count the perfect squares less than {limit} divisible by {div}.",
        f"Of the perfect squares below {limit}, how many are multiples of {div}?",
    ]), cnt, "perfect_square_divisible")

# ===================================================================
# CONSTRAINT-RESCUED — saturated v5 concepts + constraint (CORE OF v7)
# ===================================================================
@concept("constrained_subset_count",[1,15,27,57,81])
def c_subsets():
    # v12 SCAFFOLD (kept at depth-0): shrink to small n + fixed mod 3 (size kept at 3 to
    # preserve the skill shape) so the modular-subset-counting ATOM lands in-band and is
    # learnable (v11: 0.10 mean / 44% too-hard -> a depth-0 ghost factory). The hard
    # compositional AMC versions (#1,15,27,57,81) are reserved for Phase-3 chaining, which
    # composes this learned atom with others -- depth-0 alone can't crack them anyway.
    kn=K["constrained_subset_count"]
    n=kn.randint("n"); mod=kn.choice("mod"); mv=random.randint(0,mod-1)
    nocons=False
    def ok(c):
        if sum(c)%mod!=mv: return False
        if nocons and any(c[i+1]-c[i]==1 for i in range(2)): return False
        return True
    cnt=sum(1 for c in Ccomb(range(1,n+1),3) if ok(c))
    if cnt<5: return None
    consphrase=" and contain no two consecutive integers" if nocons else ""
    consphrase2=", no two consecutive," if nocons else ""
    return (random.choice([
        f"How many 3-element subsets of {{1,2,...,{n}}} have a sum that leaves remainder {mv} when divided by {mod}{consphrase}?",
        f"From {{1,...,{n}}}, how many ways to choose 3 numbers{consphrase2} whose sum is congruent to {mv} modulo {mod}?",
        f"Count the 3-element subsets of the first {n} positive integers{consphrase} with sum ≡ {mv} (mod {mod}).",
        f"How many size-3 subsets of {{1..{n}}} have sum ≡ {mv} mod {mod}{consphrase}?",
        f"How many 3-element subsets of {{1..{n}}} sum to {mv} more than a multiple of {mod}{consphrase}?",
    ]), cnt, "constrained_subset_count")

@concept("ordered_triple_constraint",[21,47])
def c_triples():
    N=K["ordered_triple_constraint"].randint("N")  # v12: narrowed to [10,20] from [12,25] (v11 0.13 mean, 54% too-hard); range now in knobs/
    cnt=_triples_gold(N)
    if cnt<5: return None
    # v12 representation fix: every phrasing now states 0<=a<b<c EXPLICITLY. The v11
    # natural-language variants ("nonnegative integers" without the 0<= bound) made the
    # model drop the a=0 case -> a consistent count-1 error -> pr~0 ghost. Gold unchanged
    # (rc counts 0<=a<b<c, check_dataset agrees).
    return (random.choice([
        f"How many triples of integers (a,b,c) with 0≤a<b<c satisfy a+b+c={N}?",
        f"How many triples (a,b,c) of integers with 0≤a<b<c have a+b+c={N}?",
        f"In how many ways can {N} be written as a+b+c with 0≤a<b<c (integers)?",
        f"How many ordered triples (a,b,c) of integers, 0≤a<b<c, sum to {N}?",
        f"Count the integer triples (a,b,c) with 0≤a<b<c and a+b+c={N}.",
    ]), cnt, "ordered_triple_constraint")

# ===================================================================
# DEPTH-1 CHAINING (Addendum A) — composites compose parent oracles
# ===================================================================
@concept("chain_log_laws__ordered_triple_constraint",[21,47])
def c_chain_loglaws_triples():
    # Pilot composite (Addendum A), Option-A draw: sample the TARGET N FIRST (uniform,
    # in-band) so composite answers stay FLAT, then DERIVE a log expression whose value
    # e1+e2-e3 == N. Review fix (PR #41): the old draw set N = e1+e2-e3, a bell-shaped
    # sum clipped at 25 -> top3 0.388 (answer-hack shape) AND mass in ordered_triple's
    # too-hard 21-25 band. Inverting the draw flattens answers and centers N in-band; the
    # num-no-widening rule means this initial spread is the only shot at it.
    # Oracles still compose: gold := _triples_gold(N), exact by construction. Surface EMBEDS
    # the log (model must evaluate it to recover N), never a "first/then" recipe.
    kn=K["chain_log_laws__ordered_triple_constraint"]
    N=kn.randint("N")                                  # flat target -> flat composite answers
    gold=_triples_gold(N)                              # B's oracle on the (embedded) value
    if gold<5: return None                             # B's own validity guard
    base=kn.choice("base"); e3=kn.randint("e3")
    s=N+e3                                              # need e1+e2 = N+e3  ->  e1+e2-e3 = N
    lo=max(4, s-20); hi=min(20, s-4)                   # keep e1,e2 inside log_laws's [4,20] envelope
    if lo>hi: return None
    e1=random.randint(lo,hi); e2=s-e1
    expr=f"log_{base}({base}^{e1} · {base}^{e2} / {base}^{e3})"   # evaluates to N; embedded
    prob=random.choice([
        f"How many triples of integers (a,b,c) with 0≤a<b<c satisfy a+b+c = {expr}?",
        f"How many ordered triples (a,b,c) of integers, 0≤a<b<c, sum to {expr}?",
        f"In how many ways can {expr} be written as a+b+c with 0≤a<b<c (integers)?",
        f"Count the integer triples (a,b,c) with 0≤a<b<c whose sum equals {expr}.",
    ])
    meta={"depth":1,"chain":{"components":["log_laws","ordered_triple_constraint"],
                              "fed_param":"N","intermediate_gold":N}}
    return (prob, gold, "chain_log_laws__ordered_triple_constraint", meta)

@concept("chain_prime_power_divisors__constrained_divisor_count",[75])
def c_chain_ppd_cdc():
    # Depth-1 composite (Addendum A) — AMC #75 = prime_power_divisors x constrained_divisor_count.
    # A = ppd: N := smallest int with exactly D divisors. N is divisor-RICH by construction, so
    # it auto-satisfies the num_pool "must have rich divisor structure" caveat (chain_compat
    # semantic_caveats[0]) — the one risk of cdc-as-target is eliminated for free. B = cdc on N.
    # Oracles compose -> gold exact. Surface EMBEDS A's quantity (model must compute N), no recipe.
    kn=K["chain_prime_power_divisors__constrained_divisor_count"]
    D=kn.choice("D")
    N=_smallest_with_ndiv(D)                           # bounded search (charizard #42 flag 1)
    if N is None: return None
    nlo,nhi=K["constrained_divisor_count"].params["num_pool"]["envelope"]  # feed-legal: READ B's
    if not (nlo<=N<=nhi): return None                  # envelope, never hard-code (kathryne #42 fix2)
    cond=kn.choice("cond")                             # knob locks cond to {gt,lt}: "odd" count
    t=kn.choice("gt_thresholds") if cond=="gt" else kn.choice("lt_thresholds") if cond=="lt" else None
    cnt=_cdc_count(N,cond,t); desc=_cdc_desc(cond,t)
    if cnt<3: return None                              # cdc's own validity guard
    expr=f"the smallest positive integer with exactly {D} positive divisors"
    prob=random.choice([
        f"Let N be {expr}. How many positive divisors of N are {desc}?",
        f"Suppose N is {expr}. Of the positive divisors of N, how many are {desc}?",
        f"Let N denote {expr}. Count the positive divisors of N that are {desc}.",
        f"If N is {expr}, find the number of positive divisors of N that are {desc}.",
    ])
    meta={"depth":1,"chain":{"components":["prime_power_divisors","constrained_divisor_count"],
                              "fed_param":"num_pool","intermediate_gold":N}}
    return (prob, cnt, "chain_prime_power_divisors__constrained_divisor_count", meta)

@concept("chain_constrained_divisor_count__modular_exponent",[55])
def c_chain_cdc_modexp():
    # Depth-1 composite (Addendum A) — AMC #55 ingredients constrained_divisor_count x
    # modular_exponent (pairs-only v1; divisor_sum_filter is the 3rd ingredient, deferred to
    # the 3-way wave). Direction cdc->modexp.e (compat-map VALID edge, frac 0.84): A=cdc count
    # becomes B=modexp's EXPONENT. modexp is the high-entropy TARGET, so composite answers stay
    # diverse (cdc-as-target collapses to small divisor counts: top3 0.59 -> rejected). Oracles
    # compose -> gold exact. Surface EMBEDS the divisor count as e (model must compute it).
    kn=K["chain_constrained_divisor_count__modular_exponent"]
    num=kn.choice("num_pool"); cond=kn.choice("cond")
    t=kn.choice("gt_thresholds") if cond=="gt" else kn.choice("lt_thresholds") if cond=="lt" else None
    e=_cdc_count(num,cond,t)                            # A's oracle (cdc) -> B's exponent
    elo,ehi=K["modular_exponent"].params["e"]["envelope"]   # feed-legal: READ B's e envelope,
    if not (elo<=e<=ehi): return None                   # never hard-code (kathryne #42 fix2)
    a=kn.randint("a"); m=kn.randint("m")
    ans=pow(a,e,m)                                      # B's oracle (modexp)
    if ans<5: return None                               # modexp's own validity guard
    desc=_cdc_desc(cond,t)
    prob=random.choice([
        f"Let e be the number of positive divisors of {num} that are {desc}. What is the remainder when {a}^e is divided by {m}?",
        f"Suppose e is the number of positive divisors of {num} that are {desc}. Find {a}^e mod {m}.",
        f"Let e denote how many positive divisors of {num} are {desc}. Compute the remainder when {a}^e is divided by {m}.",
        f"If e is the number of positive divisors of {num} that are {desc}, what is the remainder when {a}^e is divided by {m}?",
    ])
    meta={"depth":1,"chain":{"components":["constrained_divisor_count","modular_exponent"],
                              "fed_param":"e","intermediate_gold":e}}
    return (prob, ans, "chain_constrained_divisor_count__modular_exponent", meta)

@concept("arith_term_filter",[72])
def c_arithfilter():
    a=random.randint(3,15); d=random.randint(2,9); n=random.randint(30,60); dv=random.choice([3,4,5,6])
    cnt=sum(1 for k in range(n) if (a+k*d)%dv==0)
    if cnt<3: return None
    return (random.choice([
        f"An arithmetic sequence starts at {a} with common difference {d}. Among its first {n} terms, how many are divisible by {dv}?",
        f"Of the first {n} terms of the sequence {a}, {a+d}, {a+2*d}, ..., how many are multiples of {dv}?",
        f"How many of the first {n} terms of an arithmetic progression (first term {a}, difference {d}) are divisible by {dv}?",
        f"Counting the first {n} terms beginning {a} and increasing by {d}, how many are divisible by {dv}?",
        f"In the arithmetic sequence with first term {a} and common difference {d}, how many of the first {n} terms are multiples of {dv}?",
    ]), cnt, "arith_term_filter")

@concept("constrained_divisor_count",[55,75])
def c_divfilter():
    # v12 cardinality fix: widened num list + thresholds to flatten answer
    # concentration (v11 audit: 19 distinct, top-3 38%). Divisor counts are
    # structurally small ints, so distinct-count stays ~20, but the distribution is
    # more uniform -> less answer-hackable. Math unchanged; rc_constrained_divisor_count
    # parses num + threshold generically, so gold verification still holds.
    kn=K["constrained_divisor_count"]
    num=kn.choice("num_pool")
    cond=kn.choice("cond")
    ds=divisors(num)
    if cond=="odd": cnt=sum(1 for x in ds if x%2==1); desc="odd"
    elif cond=="gt": t=kn.choice("gt_thresholds"); cnt=sum(1 for x in ds if x>t); desc=f"greater than {t}"
    else: t=kn.choice("lt_thresholds"); cnt=sum(1 for x in ds if x<t); desc=f"less than {t}"
    if cnt<3: return None
    return (random.choice([
        f"How many positive divisors of {num} are {desc}?",
        f"Of the divisors of {num}, how many are {desc}?",
        f"Count the divisors of {num} that are {desc}.",
        f"{num} has how many positive divisors that are {desc}?",
        f"Find the number of {desc} divisors of {num}.",
    ]), cnt, "constrained_divisor_count")

@concept("divisor_sum_filter",[55])
def c_divsumfilter():
    # v12: require n to have >=3 distinct ODD prime factors (Doc4 lever) so the divisor-sum
    # needs real factorization, not a prime-power geometric-series shortcut (v11: 0.86 mean,
    # 38% too_easy). Sample randomly (keeps answer diversity high) and reject the rest.
    kn=K["divisor_sum_filter"]
    def _n_odd_pf(x):
        return sum(1 for pr in (3,5,7,11,13,17,19,23) if x%pr==0)
    n=None
    for _ in range(200):
        cand=kn.randint("n")
        if _n_odd_pf(cand)>=3: n=cand; break
    if n is None: return None
    cond=kn.choice("cond")
    ds=divisors(n)
    if cond=="odd": v=sum(d for d in ds if d%2==1)
    else: v=sum(d for d in ds if d%2==0)
    if v<15: return None
    return (random.choice([
        f"What is the sum of the {cond} positive divisors of {n}?",
        f"Add up all {cond} divisors of {n}.",
        f"Find the total of the {cond} positive divisors of {n}.",
        f"Sum every {cond} divisor of {n}.",
        f"Of the divisors of {n}, what do the {cond} ones add up to?",
    ]), v, "divisor_sum_filter")

@concept("triangular_filter_count",[7])
def c_trifilter():
    kn=K["triangular_filter_count"]
    lim=kn.randint("lim"); k=kn.choice("k")
    cnt=0; n=1
    while n*(n+1)//2 < lim:
        if (n*(n+1)//2)%k==0: cnt+=1
        n+=1
    if cnt<3: return None
    return (random.choice([
        f"How many triangular numbers less than {lim} are divisible by {k}? (A triangular number is 1+2+...+n.)",
        f"Among triangular numbers below {lim}, how many are multiples of {k}?",
        f"Count the triangular numbers under {lim} that are divisible by {k}.",
        f"The triangular numbers are 1, 3, 6, 10, .... How many below {lim} are multiples of {k}?",
        f"How many of the triangular numbers less than {lim} are divisible by {k}?",
    ]), cnt, "triangular_filter_count")

@concept("geo_first_exceed",[7])
def c_geoexceed():
    a=random.randint(2,9); r=random.choice([2,3]); bound=random.randint(800,60000)
    k=1; term=a
    while term<=bound: k+=1; term=a*r**(k-1)
    if k<4: return None
    return (random.choice([
        f"A geometric sequence starts at {a} and multiplies by {r} each step. Which term is the first to exceed {bound}?",
        f"Starting at {a} and tripling" + (f"" if r==3 else f" (well, ×{r})") + f" each time, what is the index of the first term greater than {bound}?",
        f"In the sequence {a}, {a*r}, {a*r*r}, ... (ratio {r}), what is the position of the first term above {bound}?",
        f"A sequence begins at {a} and each term is {r} times the previous. Find the number of the first term exceeding {bound}.",
        f"How many terms of the geometric sequence (first term {a}, ratio {r}) are needed before a term exceeds {bound}?",
    ]), k, "geo_first_exceed")

@concept("inclusion_exclusion_3set",[40])
def c_incexc3():
    kn=K["inclusion_exclusion_3set"]
    U=kn.randint("U")
    a,b,c=kn.choice("divisor_triples")
    v=(U//a+U//b+U//c-U//lcm(a,b)-U//lcm(a,c)-U//lcm(b,c)+U//lcm(a,lcm(b,c)))
    if v<10: return None
    return (random.choice([
        f"How many integers from 1 to {U} are divisible by {a}, {b}, or {c}?",
        f"Count the integers in [1,{U}] divisible by at least one of {a}, {b}, {c}.",
        f"Of the numbers 1 through {U}, how many are multiples of {a}, {b}, or {c}?",
        f"How many positive integers up to {U} are divisible by {a}, {b}, or {c}?",
        f"In the range 1 to {U}, how many integers are divisible by {a}, {b}, or {c}?",
    ]), v, "inclusion_exclusion_3set")

@concept("multi_constraint_square",[59])
def c_msquare():
    limit=random.randint(2000,4000); d=random.choice([4,9]); last=random.choice([1,4,5,6,9])  # v9: smaller search
    cnt=0; k=1
    while k*k<limit:
        if (k*k)%d==0 and (k*k)%10==last: cnt+=1
        k+=1
    if cnt<3: return None
    return (random.choice([
        f"How many perfect squares less than {limit} are divisible by {d} and end in the digit {last}?",
        f"Count perfect squares below {limit} that are multiples of {d} and whose last digit is {last}.",
        f"Of perfect squares under {limit}, how many are divisible by {d} and end in {last}?",
        f"How many squares less than {limit} are both divisible by {d} and ending in {last}?",
        f"Find the count of perfect squares < {limit} that are divisible by {d} and have units digit {last}.",
    ]), cnt, "multi_constraint_square")

@concept("vieta_sumcubes",[6,31])
def c_vietacubes():
    r1=random.randint(2,20); r2=random.randint(2,20); s=r1+r2; p=r1*r2
    return (random.choice([
        f"The roots of x² - {s}x + {p} = 0 are r and s. What is r³ + s³?",
        f"A quadratic has roots summing to {s} and with product {p}. Find the sum of the cubes of the roots.",
        f"If r+s={s} and rs={p}, what is r³+s³?",
        f"Two numbers add to {s} and multiply to {p}. What is the sum of their cubes?",
        f"Given a quadratic x²-{s}x+{p}, compute the sum of the cubes of its two roots.",
    ]), s**3-3*s*p, "vieta_sumcubes")

@concept("poly_remainder",[31])
def c_polyrem():
    # INVERSION: given P(x) value, find x. P(x)=a x^3+b x^2+c x+d, ask which integer input gives V.
    a=random.randint(2,5); b=random.randint(-5,5); cc=random.randint(-9,9); dd=random.randint(-9,9)
    x=random.randint(3,16)  # v12: widened from [3,9] (v11: only 7 distinct answers, top-3 49%)
    V=a*x**3+b*x**2+cc*x+dd
    # uniqueness over a wide range so rc_poly_remainder (which scans x in [1,3000)) agrees:
    # the gold x must be the ONLY positive-integer solution (poly>V for t>80 given a>=2).
    hits=[t for t in range(1,80) if a*t**3+b*t**2+cc*t+dd==V]
    if hits!=[x]: return None
    def fmt(co,term):
        return f"{'+' if co>=0 else '-'}{abs(co)}{term}"
    poly=f"{a}x³ {fmt(b,'x²')} {fmt(cc,'x')} {fmt(dd,'')}"
    return (random.choice([
        f"For which positive integer x does {poly} equal {V}?",
        f"The polynomial {poly} takes the value {V} at a positive integer x. Find x.",
        f"Solve {poly} = {V} for the positive integer x.",
        f"At what positive integer x is {poly} equal to {V}?",
        f"A positive integer x satisfies {poly} = {V}. What is x?",
    ]), x, "poly_remainder")

@concept("log_laws",[2,5,51,80])
def c_loglaws():
    kn=K["log_laws"]
    base=kn.choice("base"); e1=kn.randint("e1"); e2=kn.randint("e2"); e3=kn.randint("e3")
    # v12 representation fix: every argument shown as base^e (never the computed power
    # like log_3(1594323)), killing v11's 'free vs impossible' bimodal (17% gold:
    # 41% too_easy + 21% too_hard). The task is now consistently applying the product/
    # quotient log-laws. Answer e1+e2-e3 unchanged; rc_log_laws parses base^e -> verified.
    return (random.choice([
        f"Find log_{base}({base}^{e1}) + log_{base}({base}^{e2}) - log_{base}({base}^{e3}).",
        f"Compute log_{base}({base}^{e1} · {base}^{e2} / {base}^{e3}).",
        f"Evaluate log_{base}({base}^{e1} · {base}^{e2}) - log_{base}({base}^{e3}).",
        f"What is log_{base}({base}^{e1}) + log_{base}({base}^{e2}) - log_{base}({base}^{e3})?",
        f"Simplify log_{base}({base}^{e1}) + log_{base}({base}^{e2}) - log_{base}({base}^{e3}) to an integer.",
    ]), _loglaws_gold(e1,e2,e3), "log_laws")

@concept("infinite_product_exp",[20])
def c_infprod():
    base=random.choice([4,6,8,9,10,12,15,16,18,20,24,27]); r=random.choice([2,3])
    ans=base*base if r==2 else base
    if ans<6: return None
    return (random.choice([
        f"The infinite product {base}^(1/{r}) · {base}^(1/{r}²) · {base}^(1/{r}³) · ... equals √m. What is m?",
        f"Evaluate the infinite product of {base}^(1/{r}^k) for k=1,2,3,...; it equals √m for integer m. Find m.",
        f"An infinite product of {base} to powers 1/{r}, 1/{r}², ... equals the square root of m. What is m?",
        f"Compute m if {base}^(1/{r})·{base}^(1/{r}²)·... = √m.",
        f"The product {base}^(1/{r}^1)·{base}^(1/{r}^2)·... is √m. Determine m.",
    ]), ans, "infinite_product_exp")

@concept("roots_of_unity_sum",[23,48])
def c_rou():
    # COUNTING: # complex numbers that are BOTH n-th and m-th roots of unity = gcd(n,m).
    # v12: construct n,m with a CONTROLLED gcd so the answer spreads uniformly (a plain
    # wider pool BACKFIRED -- coprime pairs make gcd=1 dominate). Pick g and coprime
    # multipliers i!=j -> n=g*i, m=g*j, gcd(n,m)=g. rc recomputes gcd(n,m) from the text.
    g=random.randint(2,12)
    i,j=random.sample(range(2,7),2)
    while gcd(i,j)!=1:
        i,j=random.sample(range(2,7),2)
    n=g*i; m=g*j
    if n==m: return None
    ans=gcd(n,m)
    return (random.choice([
        f"How many complex numbers are simultaneously {n}th roots of unity and {m}th roots of unity?",
        f"A complex number is both an {n}th and an {m}th root of unity. How many such numbers exist?",
        f"Count the complex numbers z with z^{n}=1 and z^{m}=1.",
        f"How many values of z satisfy both z^{n}=1 and z^{m}=1?",
        f"The {n}th roots of unity and the {m}th roots of unity share how many common values?",
    ]), ans, "roots_of_unity_sum")

@concept("complex_modulus_power",[68,13])
def c_cmod(_cands=[]):
    # v12 cardinality fix: N is drawn from a programmatically-built list of
    # sum-of-two-squares values (1-3 representations) instead of v11's hardcoded
    # 19-value list. Math & answer are identical, so the gold recomputer / kathryne
    # verification is unchanged -- just far more distinct problems/answers (v11 audit:
    # only 14 distinct answers, top-3 = 43% -> answer-hackable, the multi_constraint_square
    # failure mode). Difficulty held constant via the 1-3 representation cap.
    if not _cands:
        kn=K["complex_modulus_power"]
        clo,chi=kn.const("cand_range")   # candidate M scanned in range(clo,chi) — hi exclusive
        rlo,rhi=kn.const("rep_cap")      # keep M with rlo..rhi representations (difficulty cap)
        for M in range(clo, chi):
            r=[(a,b) for a in range(1,int(M**0.5)+1) for b in range(a,int(M**0.5)+1) if a*a+b*b==M]
            if rlo <= len(r) <= rhi: _cands.append(M)
    N=random.choice(_cands)
    reps=[(a,b) for a in range(1,int(N**0.5)+1) for b in range(a,int(N**0.5)+1) if a*a+b*b==N]
    if not reps: return None
    ans=sum(a+b for a,b in reps)
    return (random.choice([
        f"For all pairs of positive integers a≤b with a²+b²={N}, what is the sum of (a+b) over every such pair?",
        f"Find every pair of positive integers a≤b satisfying a²+b²={N}; add up a+b across all of them.",
        f"Over all representations of {N} as a²+b² with 0<a≤b, what is the total of (a+b)?",
        f"Sum a+b over all positive-integer pairs (a≤b) with a²+b²={N}.",
        f"How much is the combined total of a+b across all pairs of positive integers a≤b where a²+b²={N}?",
    ]), ans, "complex_modulus_power")

@concept("complement_prob_mn",[24,61])
def c_compprob():
    # INVERSION: fewest rolls r so P(at least one specific face) first exceeds a threshold
    # v12: higher thresholds + bigger dice (v11: 0.90 mean / 64% too_easy / top-3 44%) ->
    # larger r, harder AND more distinct. rc parses {faces}-sided + the threshold fraction.
    faces=random.choice([4,6,8,10,12,16,20]); thr=random.choice([Fraction(2,3),Fraction(3,4),Fraction(4,5),Fraction(9,10)])
    r=1
    while 1-Fraction((faces-1)**r,faces**r)<=thr:
        r+=1
        if r>50: return None
    return (random.choice([
        f"A {faces}-sided die is rolled repeatedly. What is the fewest rolls so the probability of seeing a specific face at least once first exceeds {thr.numerator}/{thr.denominator}?",
        f"How many times must a {faces}-sided die be rolled for the chance of a given face appearing to first exceed {thr.numerator}/{thr.denominator}?",
        f"Rolling a {faces}-sided die, find the minimum number of rolls so P(a chosen face appears) > {thr.numerator}/{thr.denominator}.",
        f"For a {faces}-sided die, what is the least roll count making the probability of at least one specified face exceed {thr.numerator}/{thr.denominator}?",
        f"How many rolls of a {faces}-sided die are needed before the probability of a specific face first surpasses {thr.numerator}/{thr.denominator}?",
    ]), r, "complement_prob_mn")


@concept("box_diagonal_sq",[69])
def c_boxdiag():
    # PARAM: dimensions are the 3 smallest integers each having exactly k divisors
    # v12: widened k set (v11: only 4 distinct answers, top-3 75% -- each k gives one
    # deterministic answer). Unbuildable k just return None below. rc parses "exactly k".
    k=random.choice([4,6,8,9,10,12,14,15,16,18,20,24])
    dims=[]
    nn=2
    while len(dims)<3 and nn<500:
        if ndiv(nn)==k: dims.append(nn)
        nn+=1
    if len(dims)<3: return None
    a,b,c=dims
    return (random.choice([
        f"A box's three edge lengths are the three smallest positive integers (smallest by value) that each have exactly {k} divisors. What is the square of its space diagonal?",
        f"The dimensions of a rectangular box are the 3 smallest integers with exactly {k} divisors each (ordered by value, smallest first). Find d² for its space diagonal d.",
        f"Let the edges of a box be the three smallest numbers (by value) having exactly {k} positive divisors. Compute the square of the space diagonal.",
        f"A rectangular box has edges equal to the smallest three integers (smallest by value) each with exactly {k} divisors. What is the squared length of its diagonal?",
        f"Take the three smallest integers (by value) with exactly {k} divisors as a box's dimensions. What is the square of its space diagonal?",
    ]), a*a+b*b+c*c, "box_diagonal_sq")

@concept("trapezoid_area",[67,30])
def c_trap():
    # COUNTING: how many (bases,height) give area in [lo,hi]? OR inversion: find bases.
    # Use inversion: area A, height h given, bases are consecutive integers k,k+1 -> find k.
    h=random.choice([4,6,8,10,12]); k=random.randint(6,40)
    A=(k+(k+1))*h//2 if ((k+(k+1))*h)%2==0 else None
    if A is None:
        k+=1; A=(k+(k+1))*h//2
    # answer is the smaller base k (model must solve (2k+1)*h/2 = A)
    return (random.choice([
        f"A trapezoid has area {A} and height {h}. Its two parallel bases are consecutive integers. What is the smaller base?",
        f"The area of a trapezoid is {A} with height {h}; the bases are consecutive integers k and k+1. Find k.",
        f"A trapezoid of height {h} and area {A} has bases that differ by 1. What is the shorter base?",
        f"Given a trapezoid with area {A}, height {h}, and consecutive-integer bases, determine the smaller base.",
        f"A trapezoid's bases are consecutive integers; its height is {h} and area {A}. Find the smaller base.",
    ]), k, "trapezoid_area")

@concept("rate_closing",[43])
def c_rate():
    # INVERSION: two riders close a gap; given gap, first speed, and meeting distance, find second speed
    v1=random.randint(10,40); v2=random.randint(10,40)
    mult=random.randint(3,12); d=(v1+v2)*mult
    metfirst=d*v1//(v1+v2)
    if (d*v1)%(v1+v2)!=0: return None
    # give them d, v1, and the distance the FIRST traveled; ask for v2
    return (random.choice([
        f"Two towns are {d} miles apart. Two cyclists ride toward each other; the first goes {v1} mph and has covered {metfirst} miles when they meet. What is the second cyclist's speed?",
        f"Riders start {d} miles apart heading toward each other. The {v1}-mph rider has gone {metfirst} miles at the meeting point. How fast is the other rider?",
        f"A {d}-mile gap; two move toward each other. One travels at {v1} mph and meets the other after {metfirst} miles. Find the other's speed in mph.",
        f"Two trains {d} miles apart approach each other. The first ({v1} mph) covers {metfirst} miles before meeting. What is the second train's speed?",
        f"Starting {d} miles apart, two cyclists approach; the {v1}-mph one rides {metfirst} miles to the meeting. What is the other's mph?",
    ]), v2, "rate_closing")

@concept("three_number_system",[11])
def c_3num():
    # 3-var system, ask for product or specific combo (needs all three solved, not just one)
    third=random.randint(4,20); mult=random.randint(3,7); off=random.randint(15,50)
    first=mult*third; second=third+off
    total=first+second+third
    ans=first*third - second
    if ans<5: return None
    return (random.choice([
        f"Three numbers sum to {total}. The first is {mult} times the third, and the third is {off} less than the second. Find (first × third) − second.",
        f"Numbers a,b,c sum to {total} with a={mult}c and c=b−{off}. Compute a·c − b.",
        f"The sum of three numbers is {total}; the first equals {mult} times the third, the third is {off} below the second. What is (first·third) − second?",
        f"If a+b+c={total}, a={mult}c, and c=b−{off}, find the value of a·c−b.",
        f"Three numbers total {total}: first={mult}×third, third=second−{off}. Evaluate first×third−second.",
    ]), ans, "three_number_system")

@concept("mean_removal",[19,41,64])
def c_meanrem():
    # exact construction: x2 = n*m - x1 - (n-2)*m2 is always an integer; pick params so x2 in range
    for _ in range(20):
        n=random.randint(6,12); m=random.randint(30,70); m2=random.randint(30,70)
        x1=random.randint(15,80)
        x2=n*m-x1-(n-2)*m2
        if 10<=x2<=95:
            return (random.choice([
                f"The mean of {n} numbers is {m}. Two numbers are removed and the mean of the remaining becomes {m2}. If one removed number is {x1}, what is the other?",
                f"A list of {n} numbers averages {m}. After deleting two, the average is {m2}. One deleted value is {x1}; find the other.",
                f"{n} numbers have mean {m}. Removing two changes the mean to {m2}. Given one removed number is {x1}, what was the second?",
                f"The average of {n} numbers is {m}. Two are taken away, leaving an average of {m2}. One was {x1}; what was the other removed number?",
                f"Mean of {n} numbers is {m}; remove two and the mean is {m2}. One removed is {x1}. Find the other.",
            ]), x2, "mean_removal")
    return None

@concept("point_rotation",[9,39])
def c_rotation():
    x=random.randint(-20,20); y=random.randint(-20,20)
    cx=random.randint(-10,10); cy=random.randint(-10,10)
    deg=random.choice([90,180,270]); dx,dy=x-cx,y-cy
    if deg==90: nx,ny=-dy,dx
    elif deg==180: nx,ny=-dx,-dy
    else: nx,ny=dy,-dx
    return (random.choice([
        f"The point ({x},{y}) is rotated {deg}° counterclockwise about ({cx},{cy}). What is the sum of the new coordinates?",
        f"After rotating ({x},{y}) by {deg}° counterclockwise around ({cx},{cy}), add the resulting x and y coordinates.",
        f"Rotate ({x},{y}) {deg} degrees counterclockwise about the point ({cx},{cy}); what is x'+y' of the image?",
        f"A point ({x},{y}) turns {deg}° counterclockwise around ({cx},{cy}). Find the sum of coordinates of its new position.",
        f"What is the sum of coordinates after ({x},{y}) is rotated {deg}° CCW about ({cx},{cy})?",
    ]), (nx+cx)+(ny+cy), "point_rotation")

@concept("percent_compound",[52,73])
def c_pctcompound():
    # INVERSION, construct to guarantee integer final: choose base divisible by 100
    base=random.choice([400,500,600,800,1000,1200,1500,2000]); up=random.choice([10,20,25,50])
    down=random.choice([10,20,25,40,50])
    after_up=base*(100+up)//100
    final=after_up*(100-down)//100
    return (random.choice([
        f"A quantity of {base} is increased by {up}%, then decreased by some percent, ending at {final}. By what percent was it decreased?",
        f"Starting at {base}, a {up}% increase is followed by a percent decrease, giving {final}. Find the decrease percentage.",
        f"{base} grows by {up}% and then drops by p%, landing at {final}. What is p?",
        f"After a {up}% raise and then a cut of p%, the value {base} becomes {final}. Determine p.",
        f"A value {base} is raised {up}% then lowered by an unknown percent to reach {final}. What percent was the reduction?",
    ]), down, "percent_compound")

@concept("prime_power_divisors",[75])
def c_ppdiv():
    # INVERSION: find the smallest positive integer with exactly D divisors
    # v12: widened D set (v11: 8 distinct answers, top-3 38%, 75% too_easy). Larger D ->
    # larger smallest-n -> harder AND more distinct. rc finds smallest n with D divisors.
    D=K["prime_power_divisors"].choice("D")
    n=_smallest_with_ndiv(D)                          # bounded search (charizard #42 flag 1)
    if n is None: return None                         # awkward D (huge smallest-N) -> resample
    return (random.choice([
        f"What is the smallest positive integer with exactly {D} divisors?",
        f"Find the least positive integer having exactly {D} positive divisors.",
        f"The smallest number whose divisor count is exactly {D} — what is it?",
        f"Determine the minimum positive integer that has precisely {D} divisors.",
        f"What is the smallest integer n such that n has exactly {D} positive divisors?",
    ]), n, "prime_power_divisors")

@concept("arith_series_sum",[72])
def c_arithsum():
    # INVERSION: smallest number of terms n so the arithmetic-series sum first exceeds T
    a=random.randint(2,15); d=random.randint(2,9); T=random.randint(300,3000)
    n=0; tot=0
    while tot<=T:
        n+=1; tot+=a+(n-1)*d
    return (random.choice([
        f"An arithmetic sequence starts at {a} with common difference {d}. How many terms are needed for the running sum to first exceed {T}?",
        f"Starting at {a} and increasing by {d}, what is the fewest terms whose sum is greater than {T}?",
        f"For the series {a}, {a+d}, {a+2*d}, ..., how many terms until the total first passes {T}?",
        f"The arithmetic series with first term {a}, difference {d}: smallest term-count with sum > {T}?",
        f"How many terms of the arithmetic progression (first {a}, difference {d}) are needed for the sum to exceed {T}?",
    ]), n, "arith_series_sum")

@concept("sum_of_squares",[7,53])
def c_sumsq():
    # COUNTING: among partial sums S_k = 1^2+..+k^2 for k=1..n, how many are divisible by m?
    n=random.randint(20,60); m=random.choice([3,4,5,6,7])
    cnt=0; run=0
    for k in range(1,n+1):
        run+=k*k
        if run%m==0: cnt+=1
    if cnt<2: return None
    return (random.choice([
        f"For k from 1 to {n}, let S_k = 1²+2²+...+k². How many S_k are divisible by {m}?",
        f"How many of the partial sums 1², 1²+2², ..., up to {n} terms are multiples of {m}?",
        f"Counting k=1..{n}, for how many is the sum of the first k squares divisible by {m}?",
        f"Among the running totals of squares 1²+...+k² (k≤{n}), how many are divisible by {m}?",
        f"How many k in [1,{n}] make 1²+2²+...+k² a multiple of {m}?",
    ]), cnt, "sum_of_squares")

@concept("digit_count_bigprod",[60])
def c_digitcount():
    a=random.randint(2,9); b=random.randint(8,25); c=random.randint(2,9); d=random.randint(5,20)
    val=(a**b)*(c**d); ans=len(str(val))
    if ans<5: return None
    return (random.choice([
        f"How many digits are in the base-ten representation of {a}^{b} · {c}^{d}?",
        f"Find the number of digits of {a}^{b} times {c}^{d} when written out in full.",
        f"When {a}^{b}·{c}^{d} is written as a decimal integer, how many digits does it have?",
        f"What is the digit count of the product {a}^{b} · {c}^{d}?",
        f"Compute the number of base-ten digits in {a}^{b}·{c}^{d}.",
    ]), ans, "digit_count_bigprod")

@concept("frobenius_stamps",[71])
def c_frobenius():
    # COUNTING: how many positive integers are NOT representable as ax+by (x,y>=0)?
    # = (a-1)(b-1)/2 for coprime a,b -- but make them COMPUTE by reasoning, larger pairs
    pairs=[(4,9),(5,8),(6,11),(7,11),(5,12),(7,13),(8,11),(9,13),(7,17),(8,15)]
    a,b=random.choice(pairs)
    if gcd(a,b)!=1: return None
    ans=(a-1)*(b-1)//2
    return (random.choice([
        f"Using only {a}-cent and {b}-cent stamps, how many positive integer amounts CANNOT be made exactly?",
        f"With coins of {a} and {b} cents, how many positive values are impossible to form?",
        f"How many positive integers cannot be expressed as a nonnegative combination of {a} and {b}?",
        f"Stamps worth {a} and {b} cents: count the postage amounts that cannot be paid exactly.",
        f"How many positive integers are NOT representable as {a}x+{b}y for nonnegative integers x,y?",
    ]), ans, "frobenius_stamps")

@concept("vieta_pair_count",[70,38])
def c_vietacount():
    c=random.choice([16,24,32,36,48,60,72,80,90,96,120])
    trip=set(); R=15
    for r1 in range(-R,R+1):
        if r1==0 or c%r1: continue
        for r2 in range(r1+1,R+1):
            if r2==0: continue
            p12=r1*r2
            if p12==0 or (-c)%p12: continue
            r3=(-c)//p12
            if r3 in (r1,r2) or r3==0: continue
            trip.add(tuple(sorted((r1,r2,r3))))
    if len(trip)<2: return None
    return (random.choice([
        f"For how many ordered pairs (a,b) of integers does x³+ax²+bx+{c} have 3 distinct integer roots?",
        f"How many integer pairs (a,b) make x³+ax²+bx+{c} factor into three distinct integer roots?",
        f"Count the integer pairs (a,b) for which x³+ax²+bx+{c} has three different integer roots.",
        f"In how many ways can integers a,b be chosen so x³+ax²+bx+{c} has 3 distinct integer roots?",
        f"How many (a,b) with integer entries give x³+ax²+bx+{c} three distinct integer roots?",
    ]), len(trip), "vieta_pair_count")

@concept("continued_fraction",[0])
def c_contfrac():
    depth=random.choice([3,4,5]); a=random.choice([2,3,4,5,6,7])
    f=Fraction(a)
    for _ in range(depth-1):
        f=a+1/f
    ans=f.numerator+f.denominator
    return (random.choice([
        f"The value of {a}+1/({a}+1/({a}+1/{a})) is m/n in lowest terms. What is m+n?" if depth==4 else f"The value of {a}+1/({a}+1/{a}) is m/n in lowest terms. What is m+n?",
        f"Write the continued fraction with {depth} levels of {a} (i.e. {a}+1/({a}+1/(...))) as a reduced fraction m/n; find m+n.",
        f"A continued fraction repeats {a} for {depth} levels. Expressed as m/n in lowest terms, what is m+n?",
        f"Evaluate the nested fraction {a}+1/({a}+1/(...)) with {depth} total {a}'s as m/n irreducible; report m+n.",
        f"The {depth}-level continued fraction built from {a} equals m/n reduced. What is m+n?",
    ]), ans, "continued_fraction")

# ===================================================================
# RECOVERED — concepts for AMC problems first thought uncoverable
# ===================================================================
@concept("primality_in_sequence",[37])
def c_primeseq():
    # count primes among first K terms of a simple generated sequence
    # v9: avoid clustering -- pick d coprime-ish to small primes so terms aren't all composite
    d=random.choice([2,4,6,10,14]); a=random.choice([1,3,7,9,11,13]); K=random.randint(10,18)
    cnt=sum(1 for k in range(K) if (a+k*d)<2_000_000 and ISPRIME[a+k*d])
    return (random.choice([
        f"Consider the sequence {a}, {a+d}, {a+2*d}, ... How many of its first {K} terms are prime?",
        f"How many primes are among the first {K} terms of the arithmetic sequence starting at {a} with step {d}?",
        f"Of the first {K} terms of the sequence beginning {a} and increasing by {d}, how many are prime numbers?",
        f"Count the prime numbers in the first {K} terms of the sequence {a}, {a+d}, {a+2*d}, ....",
        f"In the sequence with first term {a} and common difference {d}, how many of the first {K} terms are prime?",
    ]), cnt, "primality_in_sequence")

@concept("distinct_product_count",[74])
def c_distprod():
    # spread: vary number of dice (3) AND number of faces -> different counts
    n=3; faces=random.choice([4,5,6,8])
    from itertools import product
    prods=set()
    for combo in product(range(1,faces+1),repeat=n):
        p=1
        for x in combo: p*=x
        prods.add(p)
    return (random.choice([
        f"When {n} standard {faces}-sided dice are rolled, how many distinct values can the product take?",
        f"Rolling {n} {faces}-sided dice, how many different products are possible?",
        f"How many distinct products result from multiplying the faces of {n} rolled {faces}-sided dice?",
        f"{n} {faces}-sided dice are rolled and multiplied. How many different products can occur?",
        f"Count the distinct possible products when {n} {faces}-sided dice are rolled.",
    ]), len(prods), "distinct_product_count")

@concept("polynomial_sign_intervals",[79])
def c_polysign():
    # P(x) = prod (x-i)^{m_i}; removing roots leaves intervals; count where P>0
    # v12: widened K (v11: only 7 distinct answers, top-3 79%) -> more intervals -> the
    # positive-count spans a wider range. rc handles any K and any multiplicity list.
    K=random.randint(4,10)
    mults=[random.randint(1,4) for _ in range(K)]
    # rightmost interval is always positive (leading coeff positive, even/odd handled by sign walk)
    # walk from +inf leftward: sign flips when crossing a root of ODD multiplicity
    pos=0; sign=1  # +inf region positive
    # intervals from right to left: K+1 intervals
    if sign>0: pos+=1
    for m in reversed(mults):
        if m%2==1: sign=-sign
        if sign>0: pos+=1
    return (random.choice([
        f"The polynomial P(x)=(x-1)^{mults[0]}·(x-2)^{mults[1]}" + "".join(f"·(x-{i+1})^{mults[i]}" for i in range(2,K)) + f" has its roots removed from the number line, leaving {K+1} open intervals. On how many is P(x) positive?",
        f"Given P(x) with roots at 1..{K} of multiplicities {mults} respectively, on how many of the {K+1} resulting intervals is P(x)>0?",
        f"A polynomial has roots 1,2,...,{K} with multiplicities {mults}. After removing the roots, on how many of the {K+1} intervals is the polynomial positive?",
        f"Roots at x=1..{K} (multiplicities {mults}) split the line into {K+1} intervals. Count those where the polynomial is positive.",
        f"P(x)=∏(x-i)^(m_i) for i=1..{K} with m={mults}. On how many of the {K+1} open intervals is P positive?",
    ]), pos, "polynomial_sign_intervals")

@concept("constrained_digit_count",[63])
def c_digitconstraint():
    # count d-digit numbers (in a range) where digit sum equals a target, or all digits distinct
    lo=random.choice([1000,2000,3000]); hi=lo+random.choice([1000,2000])
    target=random.randint(10,20)
    cnt=sum(1 for x in range(lo,hi) if sum(int(c) for c in str(x))==target)
    if cnt<5: return None
    return (random.choice([
        f"How many integers from {lo} to {hi-1} have digits summing to exactly {target}?",
        f"Count the integers in [{lo}, {hi-1}] whose digit sum is {target}.",
        f"Among the numbers {lo} through {hi-1}, how many have digits that add up to {target}?",
        f"How many integers between {lo} and {hi-1} (inclusive of {lo}) have a digit sum of {target}?",
        f"Find the count of integers in the range {lo} to {hi-1} with digit sum equal to {target}.",
    ]), cnt, "constrained_digit_count")

@concept("equalization_fraction",[65])
def c_equalize():
    # g glasses, last is fraction f full, rest full; equalize -> pour x from each of (g-1).
    # total = (g-1) + f ; each ends at total/g ; pour from each full one = 1 - total/g
    g=random.choice([3,4,5,6,8]); fn=random.choice([Fraction(1,3),Fraction(1,2),Fraction(1,4),Fraction(2,3),Fraction(1,5),Fraction(3,4),Fraction(2,5),Fraction(3,5)])
    total=(g-1)+fn; each=total/g; pour=1-each
    ans=pour.numerator+pour.denominator
    return (random.choice([
        f"There are {g} identical glasses. The first {g-1} are full; the last is {fn} full. To make all equal, what fraction must be poured from each full glass into the last? Express as m/n in lowest terms and give m+n.",
        f"{g} glasses: {g-1} completely full, one {fn} full. Equalizing by pouring equally from each full glass, the poured fraction is m/n reduced. Find m+n.",
        f"You have {g} equal glasses, {g-1} full and one {fn} full. The fraction poured from each full glass to equalize is m/n in lowest terms; report m+n.",
        f"To equalize {g} glasses ({g-1} full, one {fn} full), you pour m/n of a glass from each full one. Find m+n in lowest terms.",
        f"With {g} glasses, {g-1} full and one at {fn}, the equalizing pour from each full glass is m/n irreducible. What is m+n?",
    ]), ans, "equalization_fraction")

@concept("algebraic_system_2eq",[44])
def c_system():
    # 3x3 integer system, ask x+y+z -> genuine multi-step elimination
    # v12: ENABLED the v11 staged range bump (v11 calib: 0.90 mean, 59% too_easy -> raise).
    # 2048 removed the truncation that argued for caution. rc_algebraic_system_2eq solves
    # the system generically, so larger coeffs/values stay verified.
    x=random.randint(5,25); y=random.randint(5,25); z=random.randint(5,25)
    def row():
        return random.randint(1,7),random.randint(1,7),random.randint(1,7)
    a1,b1,c1=row(); a2,b2,c2=row(); a3,b3,c3=row()
    det=a1*(b2*c3-b3*c2)-b1*(a2*c3-a3*c2)+c1*(a2*b3-a3*b2)
    if det==0: return None
    d1=a1*x+b1*y+c1*z; d2=a2*x+b2*y+c2*z; d3=a3*x+b3*y+c3*z
    return (random.choice([
        f"Positive integers x,y,z satisfy {a1}x+{b1}y+{c1}z={d1}, {a2}x+{b2}y+{c2}z={d2}, and {a3}x+{b3}y+{c3}z={d3}. Find x+y+z.",
        f"Solve {a1}x+{b1}y+{c1}z={d1}, {a2}x+{b2}y+{c2}z={d2}, {a3}x+{b3}y+{c3}z={d3} for positive integers; give x+y+z.",
        f"Three equations: {a1}x+{b1}y+{c1}z={d1}, {a2}x+{b2}y+{c2}z={d2}, {a3}x+{b3}y+{c3}z={d3}. What is x+y+z?",
        f"Given the system {a1}x+{b1}y+{c1}z={d1}, {a2}x+{b2}y+{c2}z={d2}, {a3}x+{b3}y+{c3}z={d3}, compute x+y+z.",
        f"Find x+y+z if {a1}x+{b1}y+{c1}z={d1}, {a2}x+{b2}y+{c2}z={d2}, and {a3}x+{b3}y+{c3}z={d3}.",
    ]), x+y+z, "algebraic_system_2eq")

@concept("unit_conversion_area",[77])
def c_unitarea():
    width_mm=random.choice([5,6,8,10,13,15]); length_m=random.randint(10,40)
    # area in cm^2: width in cm = width_mm/10, length in cm = length_m*100
    # area = (width_mm/10) * (length_m*100) = width_mm*length_m*10
    ans=width_mm*length_m*10
    return (random.choice([
        f"A paint strip is {width_mm} millimeters wide and {length_m} meters long. How many square centimeters does it cover?",
        f"A brush makes a strip {width_mm} mm wide; there is enough paint for {length_m} meters of length. Find the area in square centimeters.",
        f"How many square centimeters are covered by a strip {width_mm} mm wide and {length_m} m long?",
        f"A {width_mm}-millimeter-wide strip runs {length_m} meters. What is its area in square centimeters?",
        f"Compute the area in cm² of a painted strip {width_mm} mm wide and {length_m} m long.",
    ]), ans, "unit_conversion_area")

# ===================================================================
# GEOMETRY-COUNTING (Option 3) — constraint-counting geometry
# ===================================================================
@concept("count_obtuse_triangles",[18])
def c_obtuse():
    P=random.randint(11,16)  # v9: small enough to enumerate by hand (~15-25 triangles)
    cnt=0
    for a in range(1,P):
        for b in range(a,P):
            for c in range(b,P):
                if a+b+c>P: break
                if a+b<=c: continue
                if c*c>a*a+b*b: cnt+=1
    if cnt<2: return None
    return (random.choice([
        f"How many triangles with integer side lengths and perimeter at most {P} are obtuse?",
        f"Count the obtuse triangles with integer sides and perimeter ≤ {P}.",
        f"How many integer-sided triangles of perimeter at most {P} have an obtuse angle?",
        f"Find the number of obtuse integer-sided triangles with perimeter no greater than {P}.",
        f"Among triangles with integer sides and perimeter ≤ {P}, how many are obtuse?",
    ]), cnt, "count_obtuse_triangles")

@concept("lattice_points_circle",[82])
def c_lattice():
    R=random.randint(3,16)  # v12: widened from [3,7] (v11: 5 distinct answers, top-3 60%); answer deterministic per R, rc squares the bound
    cnt=sum(1 for x in range(-R,R+1) for y in range(-R,R+1) if x*x+y*y<=R*R)
    return (random.choice([
        f"How many integer-coordinate points (x,y) satisfy x²+y² ≤ {R}²?",
        f"Count the lattice points inside or on the circle of radius {R} centered at the origin.",
        f"How many points with integer coordinates lie within distance {R} of the origin?",
        f"Find the number of integer points (x,y) with x²+y² ≤ {R*R}.",
        f"How many lattice points are inside or on a circle of radius {R} about the origin?",
    ]), cnt, "lattice_points_circle")

@concept("count_pythagorean",[66,76])
def c_countpythag():
    H=random.choice([15,18,20,25,30])
    cnt=0
    for a in range(1,H+1):
        for b in range(a,H+1):
            c2=a*a+b*b; c=math.isqrt(c2)
            if c*c==c2 and c<=H: cnt+=1
    if cnt<3: return None
    return (random.choice([
        f"How many right triangles with integer side lengths have a hypotenuse of at most {H}?",
        f"Count the integer right triangles (Pythagorean triples) with hypotenuse ≤ {H}.",
        f"How many Pythagorean triples (a,b,c) with a≤b have c ≤ {H}?",
        f"Find the number of integer-sided right triangles whose hypotenuse is at most {H}.",
        f"How many right triangles with whole-number sides have hypotenuse no more than {H}?",
    ]), cnt, "count_pythagorean")

def build(per):
    for name,fn,_ in REGISTRY:
        if name in DEPTH1_PARTNERS: continue   # reserved for depth-1 chaining
        made=0; guard=0
        while made<per and guard<per*200:
            guard+=1
            r=fn()
            if r is None: continue
            add(r[0],r[1],name)
            made+=1

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--per",type=int,default=150)
    ap.add_argument("--sample",type=int,default=0)
    ap.add_argument("--out",default="/home/faisalnab25/data/skeleton_dataset_v7.json")
    ap.add_argument("--seed",type=int,default=42)
    args=ap.parse_args()
    random.seed(args.seed); build(args.per)
    print(f"Generated {len(PROBLEMS)} v7 problems across {len(REGISTRY)} concepts")
    cov=set()
    for name,_,amc in REGISTRY:
        if name in DEPTH1_PARTNERS: continue
        cov.update(amc)
    print(f"AMC coverage (depth-0): {len(cov)}/83 -> {sorted(cov)}")
    print(f"Depth-1 partners (reserved for chaining): {sorted(DEPTH1_PARTNERS)}")
    if args.sample:
        for p in random.sample(PROBLEMS,min(args.sample,len(PROBLEMS))):
            print("\n["+p['skeleton_type']+"] ans="+p['answer']); print("  "+p['problem'][:170])
        return
    with open(args.out,"w") as f: json.dump(PROBLEMS,f,indent=2)
    print(f"Saved to {args.out}")

if __name__=="__main__": main()
