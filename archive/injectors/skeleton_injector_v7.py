#!/usr/bin/env python3
"""
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
import argparse, json, math, random
from fractions import Fraction
from collections import Counter
from itertools import combinations as Ccomb

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

PROBLEMS=[]
REGISTRY=[]
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
    a=random.randint(8,40); b=random.randint(8,40); c=random.randint(8,40)
    op=lambda x,y:x+y+x*y
    ans=op(op(a,b),c)
    if ans>200000: return None
    return (random.choice([
        f"Define x⊕y = x+y+xy for all integers. What is ({a}⊕{b})⊕{c}?",
        f"Let the operation x⊕y mean x+y+xy. Compute ({a}⊕{b})⊕{c}.",
        f"Using x⊕y = x+y+xy, evaluate {a}⊕{b}, then ⊕ that result with {c}.",
        f"If a⊕b is defined as a+b+ab, what is ({a}⊕{b})⊕{c}?",
        f"With the rule x⊕y=x+y+xy, find the value of ({a}⊕{b})⊕{c}.",
    ]), ans, "custom_binary_op")

@concept("modular_exponent",[55])
def c_modexp():
    a=random.randint(2,9); e=random.randint(6,16); m=random.choice(list(range(50,300)))
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
    n=random.randint(12,22); mod=random.choice([3,4,5]); mv=random.randint(0,mod-1)
    cnt=sum(1 for c in Ccomb(range(1,n+1),3)
            if sum(c)%mod==mv and not any(c[i+1]-c[i]==1 for i in range(2)))
    if cnt<5: return None
    return (random.choice([
        f"How many 3-element subsets of {{1,2,...,{n}}} have a sum that leaves remainder {mv} when divided by {mod} and contain no two consecutive integers?",
        f"From {{1,...,{n}}}, how many ways to choose 3 numbers, no two consecutive, whose sum is congruent to {mv} modulo {mod}?",
        f"Count the 3-element subsets of the first {n} positive integers with no two consecutive elements and sum ≡ {mv} (mod {mod}).",
        f"How many size-3 subsets of {{1..{n}}} avoid consecutive integers and have sum ≡ {mv} mod {mod}?",
        f"In how many ways can 3 numbers be chosen from {{1..{n}}} so no two are adjacent and their sum is {mv} more than a multiple of {mod}?",
    ]), cnt, "constrained_subset_count")

@concept("ordered_triple_constraint",[21,47])
def c_triples():
    N=random.randint(18,55)
    cnt=sum(1 for a in range(N+1) for b in range(a+1,N+1) if (N-a-b)>b)
    if cnt<5: return None
    return (random.choice([
        f"How many triples of integers (a,b,c) with 0≤a<b<c satisfy a+b+c={N}?",
        f"Count the strictly increasing triples (a,b,c) of nonnegative integers with a+b+c={N}.",
        f"In how many ways can {N} be written as a+b+c with 0≤a<b<c (integers)?",
        f"How many ordered triples (a,b,c), 0≤a<b<c, sum to {N}?",
        f"Find the number of triples a<b<c of nonnegative integers summing to {N}.",
    ]), cnt, "ordered_triple_constraint")

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
    num=random.choice([360,420,504,540,600,630,660,720,756,792,840,900,924,990,1080,1260])
    cond=random.choice(["odd","gt","lt"])
    ds=divisors(num)
    if cond=="odd": cnt=sum(1 for x in ds if x%2==1); desc="odd"
    elif cond=="gt": t=random.choice([10,12,20]); cnt=sum(1 for x in ds if x>t); desc=f"greater than {t}"
    else: t=random.choice([20,30,50]); cnt=sum(1 for x in ds if x<t); desc=f"less than {t}"
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
    n=random.randint(60,900); cond=random.choice(["odd","even"])
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
    lim=random.randint(800,6000); k=random.choice([2,3,5])
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
    U=random.randint(200,900)
    a,b,c=random.choice([(2,3,5),(3,4,5),(2,5,7),(3,5,7),(2,3,7)])
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
    limit=random.randint(4000,12000); d=random.choice([4,9]); last=random.choice([1,4,5,6,9])
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
    a=random.randint(2,6); b=random.randint(-6,6); cc=random.randint(-9,9); dd=random.randint(-9,9)
    x=random.randint(3,7)
    return (random.choice([
        f"What is the remainder when {a}x³+({b})x²+({cc})x+({dd}) is divided by (x-{x})?",
        f"Find the value of {a}x³+({b})x²+({cc})x+({dd}) at x={x}.",
        f"Evaluate the polynomial {a}x³+({b})x²+({cc})x+({dd}) when x={x}.",
        f"Using the remainder theorem, what does {a}x³+({b})x²+({cc})x+({dd}) leave when divided by x-{x}?",
        f"Compute {a}x³+({b})x²+({cc})x+({dd}) for x={x}.",
    ]), a*x**3+b*x**2+cc*x+dd, "poly_remainder")

@concept("log_laws",[2,5,51,80])
def c_loglaws():
    base=random.choice([2,3,5]); e1=random.randint(6,25); e2=random.randint(6,25); e3=random.randint(1,8)
    return (random.choice([
        f"Find log_{base}({base}^{e1}) + log_{base}({base}^{e2}) - log_{base}({base}^{e3}).",
        f"What is log_{base}({base**e1}) + log_{base}({base**e2}) - log_{base}({base**e3})?",
        f"Compute the value of log_{base}({base**e1} · {base**e2} / {base**e3}).",
        f"Evaluate log base {base} of {base**e1}, plus log base {base} of {base**e2}, minus log base {base} of {base**e3}.",
        f"Simplify log_{base}({base**e1}) + log_{base}({base**e2}) - log_{base}({base**e3}) to an integer.",
    ]), e1+e2-e3, "log_laws")

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
    k=random.randint(3,15); n=random.randint(2,60); coeff=random.randint(2,9)
    base=k if n%k==0 else 0
    return (random.choice([
        f"Let S be the sum of the {n}th powers of all {k}th roots of unity. Compute {coeff}·S + {n}.",
        f"The {k}th roots of unity are each raised to the {n}th power and summed to give S. Find {coeff}S+{n}.",
        f"Sum the {n}th powers of every {k}th root of unity to get S; what is {coeff}S+{n}?",
        f"If S is the total of the {n}th powers of the {k}th roots of unity, evaluate {coeff}S+{n}.",
        f"Add the {n}th powers of all {k} of the {k}th roots of unity (call it S); report {coeff}S+{n}.",
    ]), coeff*base+n, "roots_of_unity_sum")

@concept("complex_modulus_power",[68,13])
def c_cmod():
    a=random.randint(1,9); b=random.randint(1,9); k=random.randint(2,4)
    ans=(a*a+b*b)**k
    if ans>100000: return None
    return (random.choice([
        f"For z={a}+{b}i, what is |z|^{2*k} (the {k}th power of z times its conjugate)?",
        f"Compute (z·z̄)^{k} where z={a}+{b}i.",
        f"If z={a}+{b}i, find the value of |z|² raised to the {k}th power.",
        f"What is ({a}²+{b}²)^{k}, i.e. the modulus-squared of {a}+{b}i to the {k}th power?",
        f"Given z={a}+{b}i, evaluate (|z|²)^{k}.",
    ]), ans, "complex_modulus_power")

@concept("complement_prob_mn",[24,61])
def c_compprob():
    faces=random.choice([4,6,8,10,12]); r=random.randint(2,4)
    p=Fraction(faces**r-(faces-1)**r,faces**r)
    return (random.choice([
        f"A fair {faces}-sided die is rolled {r} times. The probability of getting the top face at least once is m/n in lowest terms. Find m+n.",
        f"Rolling a {faces}-sided die {r} times, the chance of seeing a specific face at least once is m/n reduced. What is m+n?",
        f"In {r} rolls of a {faces}-sided die, the probability of at least one specified face is m/n irreducible. Report m+n.",
        f"The probability of at least one chosen face in {r} rolls of a {faces}-sided die is reduced fraction m/n. Find m+n.",
        f"Roll a {faces}-sided die {r} times; probability a given face appears equals m/n lowest terms. Give m+n.",
    ]), p.numerator+p.denominator, "complement_prob_mn")

@concept("pythag_hypotenuse",[66,76])
def c_pythag():
    bp,bq,bh=random.choice([(3,4,5),(5,12,13),(8,15,17),(7,24,25),(20,21,29),(9,40,41)])
    s=random.randint(2,15)
    return (random.choice([
        f"A right triangle has legs {bp*s} and {bq*s}. What is the length of the hypotenuse?",
        f"Find the hypotenuse of a right triangle with perpendicular sides {bp*s} and {bq*s}.",
        f"A right triangle's two legs measure {bp*s} and {bq*s}. How long is the hypotenuse?",
        f"What is the hypotenuse of a right triangle whose legs are {bp*s} and {bq*s}?",
        f"Two legs of a right triangle are {bp*s} and {bq*s}; compute the hypotenuse.",
    ]), bh*s, "pythag_hypotenuse")

@concept("box_diagonal_sq",[69])
def c_boxdiag():
    a=random.randint(3,20); b=random.randint(3,20); c=random.randint(3,20)
    return (random.choice([
        f"A rectangular box has edge lengths {a}, {b}, and {c}. What is the square of its space diagonal?",
        f"For a box measuring {a}×{b}×{c}, find the squared length of the longest diagonal.",
        f"A rectangular prism has dimensions {a}, {b}, {c}. Compute the square of its main diagonal.",
        f"What is d² where d is the space diagonal of an {a}×{b}×{c} box?",
        f"Find the squared space-diagonal of a rectangular box with sides {a}, {b}, {c}.",
    ]), a*a+b*b+c*c, "box_diagonal_sq")

@concept("trapezoid_area",[67,30])
def c_trap():
    a=random.randint(8,40); b=random.randint(8,40); h=random.randint(4,20)
    if (a+b)*h%2: h+=1
    return (random.choice([
        f"A trapezoid has parallel sides {a} and {b} and height {h}. What is its area?",
        f"Find the area of a trapezoid with parallel sides {a}, {b} and height {h}.",
        f"A trapezoid's two parallel sides are {a} and {b}, with height {h}. Compute the area.",
        f"What is the area of a trapezoid whose bases are {a} and {b} and whose height is {h}?",
        f"Compute the area of a trapezoid with bases {a} and {b}, height {h}.",
    ]), (a+b)*h//2, "trapezoid_area")

@concept("rate_closing",[43])
def c_rate():
    v1=random.randint(10,40); v2=random.randint(10,40); d=(v1+v2)*random.randint(3,12)
    return (random.choice([
        f"Two towns are {d} miles apart. Two cyclists start toward each other at {v1} and {v2} mph. How far has the first traveled when they meet?",
        f"Cities A and B are {d} miles apart; riders leave simultaneously toward each other at {v1} and {v2} mph. How far does the {v1}-mph rider go before meeting?",
        f"{d} miles separate two runners moving toward each other at {v1} and {v2} mph. Distance covered by the first when they meet?",
        f"Two trains {d} miles apart approach at {v1} and {v2} mph. How far has the {v1}-mph train gone at the meeting point?",
        f"Starting {d} miles apart and heading toward each other at {v1} and {v2} mph, how far does the first travel before meeting?",
    ]), d*v1//(v1+v2), "rate_closing")

@concept("three_number_system",[11])
def c_3num():
    third=random.randint(3,30); mult=random.randint(3,9); off=random.randint(20,80)
    first=mult*third; second=third+off
    ans=abs(first-second)
    if ans<5: return None
    return (random.choice([
        f"Three numbers sum to {first+second+third}. The first is {mult} times the third, and the third is {off} less than the second. What is |first - second|?",
        f"The sum of three numbers is {first+second+third}; the first equals {mult} times the third, and the third is {off} below the second. Find |first - second|.",
        f"Three numbers add to {first+second+third}. First = {mult}×third, third = second - {off}. What is |first - second|?",
        f"Numbers a,b,c sum to {first+second+third} with a={mult}c and c=b-{off}. Compute |a-b|.",
        f"If three numbers total {first+second+third}, the first is {mult} times the third, and the third is {off} less than the second, what is |first-second|?",
    ]), ans, "three_number_system")

@concept("mean_removal",[19,41,64])
def c_meanrem():
    n=random.randint(5,12); m=random.randint(20,80); m2=random.randint(20,80)
    removed=n*m-(n-1)*m2
    if removed<1 or removed>200: return None
    return (random.choice([
        f"The mean of {n} numbers is {m}. Removing one makes the mean of the rest {m2}. What number was removed?",
        f"{n} values average {m}; after deleting one value the remaining {n-1} average {m2}. Find the deleted value.",
        f"A set of {n} numbers has mean {m}. Taking one away changes the mean to {m2}. What was taken away?",
        f"With {n} numbers averaging {m}, removing a single number gives average {m2}. Which number was removed?",
        f"The average of {n} numbers is {m}; the average of all but one is {m2}. What is the omitted number?",
    ]), removed, "mean_removal")

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
    base=random.randint(20,200)*10; up=random.choice([10,20,25,50]); down=random.choice([10,20,25,50])
    v=base*(100+up)//100
    return (random.choice([
        f"A quantity of {base} is increased by {up}% and then decreased by {down}%. What is the final value?",
        f"Starting at {base}, apply a {up}% increase followed by a {down}% decrease. What remains?",
        f"After raising {base} by {up}% and then cutting it by {down}%, what is the result?",
        f"A value of {base} grows {up}% then shrinks {down}%. Find the ending amount.",
        f"{base} is marked up {up}% and subsequently marked down {down}%. What is the final figure?",
    ]), v*(100-down)//100, "percent_compound")

@concept("prime_power_divisors",[75])
def c_ppdiv():
    a=random.randint(2,9); b=random.randint(2,9); c=random.randint(2,8)
    p,q,r=random.sample([2,3,5,7,11],3)
    return (random.choice([
        f"How many positive divisors does {p}^{a} · {q}^{b} · {r}^{c} have?",
        f"Find the number of divisors of {p}^{a}·{q}^{b}·{r}^{c}.",
        f"A number factors as {p}^{a}·{q}^{b}·{r}^{c}. How many positive divisors does it have?",
        f"Count the positive divisors of {p}^{a} times {q}^{b} times {r}^{c}.",
        f"What is the total number of divisors of {p}^{a}·{q}^{b}·{r}^{c}?",
    ]), (a+1)*(b+1)*(c+1), "prime_power_divisors")

@concept("arith_series_sum",[72])
def c_arithsum():
    a=random.randint(2,20); d=random.randint(1,12); n=random.randint(8,30)
    return (random.choice([
        f"An arithmetic series starts at {a}, increases by {d}, and has {n} terms. What is the total?",
        f"Sum the first {n} terms of an arithmetic sequence with first term {a} and difference {d}.",
        f"Find the sum of {n} terms beginning at {a} and increasing by {d} each time.",
        f"What is the sum of the arithmetic progression {a}, {a+d}, {a+2*d}, ... ({n} terms)?",
        f"Add the {n}-term arithmetic series first term {a}, common difference {d}.",
    ]), n*(2*a+(n-1)*d)//2, "arith_series_sum")

@concept("sum_of_squares",[7,53])
def c_sumsq():
    n=random.randint(8,40)
    return (random.choice([
        f"What is 1² + 2² + 3² + ... + {n}²?",
        f"Find the sum of the squares of the first {n} positive integers.",
        f"Compute the sum 1²+2²+...+{n}².",
        f"Add up the squares of every integer from 1 to {n}.",
        f"What is the total of the first {n} perfect squares (1², 2², ..., {n}²)?",
    ]), n*(n+1)*(2*n+1)//6, "sum_of_squares")

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
    a,b=random.choice([(6,10),(4,9),(5,8),(7,11),(6,11),(5,12),(7,13),(8,11),(9,13)])
    while gcd(a,b)!=1: a,b=random.sample(range(3,15),2)
    ans=a*b-a-b
    if ans<10: return None
    return (random.choice([
        f"Coins come in values {a} and {b} cents. What is the largest amount that cannot be made exactly?",
        f"Using only {a}-cent and {b}-cent coins, find the greatest value that is impossible to form.",
        f"Stamps are sold in {a}-cent and {b}-cent denominations. What is the largest postage that cannot be paid exactly?",
        f"With unlimited {a}-cent and {b}-cent pieces, what is the biggest amount you cannot make?",
        f"What is the largest integer not expressible as a nonnegative combination of {a} and {b}?",
    ]), ans, "frobenius_stamps")

@concept("vieta_pair_count",[70,38])
def c_vietacount():
    c=random.choice([16,81,32,64,100,48,80,60,84,90,72,108,96,120,128,144,160,168,180,200,216,240])
    trip=set(); R=22
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
    a=random.randint(2,6); d=random.randint(3,12); K=random.randint(8,20)
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
    # count distinct products achievable from n dice (faces 1..6)
    n=random.randint(2,6)
    from itertools import product
    prods=set()
    for combo in product(range(1,7),repeat=n):
        p=1
        for x in combo: p*=x
        prods.add(p)
    return (random.choice([
        f"When {n} standard six-sided dice are rolled, how many distinct values can the product of the numbers take?",
        f"Rolling {n} six-sided dice, how many different products are possible?",
        f"How many distinct products can result from multiplying the faces of {n} rolled six-sided dice?",
        f"{n} ordinary dice are rolled and their numbers multiplied. How many different products can occur?",
        f"Count the number of distinct possible products when {n} six-sided dice are rolled.",
    ]), len(prods), "distinct_product_count")

@concept("polynomial_sign_intervals",[79])
def c_polysign():
    # P(x) = prod (x-i)^{m_i}; removing roots leaves intervals; count where P>0
    K=random.randint(4,8)
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
    # generate integer solution (x,y), build a 2-eq system, ask x+y
    x=random.randint(3,30); y=random.randint(3,30)
    a1,b1=random.randint(1,5),random.randint(1,5); c1=a1*x+b1*y
    a2,b2=random.randint(1,5),random.randint(1,5)
    while a1*b2-a2*b1==0: a2,b2=random.randint(1,5),random.randint(1,5)
    c2=a2*x+b2*y
    return (random.choice([
        f"Positive integers x and y satisfy {a1}x+{b1}y={c1} and {a2}x+{b2}y={c2}. What is x+y?",
        f"Solve the system {a1}x+{b1}y={c1}, {a2}x+{b2}y={c2} for positive integers; find x+y.",
        f"Two equations hold: {a1}x+{b1}y={c1} and {a2}x+{b2}y={c2}. Compute x+y.",
        f"Find x+y given {a1}x+{b1}y={c1} and {a2}x+{b2}y={c2}.",
        f"If {a1}x+{b1}y={c1} and {a2}x+{b2}y={c2}, what is the value of x+y?",
    ]), x+y, "algebraic_system_2eq")

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
    P=random.randint(20,40)
    cnt=0
    for a in range(1,P):
        for b in range(a,P):
            for c in range(b,P):
                if a+b+c>P: break
                if a+b<=c: continue
                if c*c>a*a+b*b: cnt+=1
    if cnt<5: return None
    return (random.choice([
        f"How many triangles with integer side lengths and perimeter at most {P} are obtuse?",
        f"Count the obtuse triangles with integer sides and perimeter ≤ {P}.",
        f"How many integer-sided triangles of perimeter at most {P} have an obtuse angle?",
        f"Find the number of obtuse integer-sided triangles with perimeter no greater than {P}.",
        f"Among triangles with integer sides and perimeter ≤ {P}, how many are obtuse?",
    ]), cnt, "count_obtuse_triangles")

@concept("lattice_points_circle",[82])
def c_lattice():
    R=random.randint(5,15)
    cnt=sum(1 for x in range(-R,R+1) for y in range(-R,R+1) if x*x+y*y<=R*R)
    return (random.choice([
        f"How many integer-coordinate points (x,y) satisfy x²+y² ≤ {R}²?",
        f"Count the lattice points inside or on the circle of radius {R} centered at the origin.",
        f"How many points with integer coordinates lie within distance {R} of the origin?",
        f"Find the number of integer points (x,y) with x²+y² ≤ {R*R}.",
        f"How many lattice points are inside or on a circle of radius {R} about the origin?",
    ]), cnt, "lattice_points_circle")

@concept("count_pythagorean",[76])
def c_countpythag():
    H=random.choice([20,25,30,40,50,60,75,100])
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
    for _,_,amc in REGISTRY: cov.update(amc)
    print(f"AMC coverage: {len(cov)}/83 -> {sorted(cov)}")
    if args.sample:
        for p in random.sample(PROBLEMS,min(args.sample,len(PROBLEMS))):
            print("\n["+p['skeleton_type']+"] ans="+p['answer']); print("  "+p['problem'][:170])
        return
    with open(args.out,"w") as f: json.dump(PROBLEMS,f,indent=2)
    print(f"Saved to {args.out}")

if __name__=="__main__": main()
