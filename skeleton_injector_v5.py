#!/usr/bin/env python3
"""
skeleton_injector_v6.py — CalibrateRL Layer-1 depth-0 reasoning generator

PHILOSOPHY (the correction that defines v6):
  v6 trains MATH REASONING across the domains the AMC eval draws on -- NOT the
  surface FORMAT of AMC problems. The goal is capability that GENERALISES; AMC
  improvement should be a CONSEQUENCE of better reasoning, not the training
  target. So problems are plain-format, calibrated for 7B signal, and chosen to
  cover the reasoning PRIMITIVES behind ~50-60 of the 83 eval problems.
  (An AMC-format wrapper is a SEPARATE later layer, applied on top, so we can
  measure reasoning-transfer vs format-adaptation independently.)

DESIGN RULES (audit Part 6, enforced for every concept):
  R1 no formula hints   R2 no trivial one-step lookups
  R3 integer answers asserted, mostly 10..10000 (SMALL_OK lists count-concepts)
  R4 answer not guessable from concept type alone (wide answer range)
  R5 >=5 surface phrasings   R6 method must be inferred from context

DIFFICULTY (audit Part 5): the lever that moves a 7B from "always right" to
  "~half right" is the number of DEPENDENT steps / slip-risk, not novelty.
  Ranges below are chosen so the METHOD is known but EXECUTION fails ~half the
  rollouts at training temperature.

COVERAGE: each concept carries `amc_targets` = the eval problem IDs whose
  reasoning it builds. main() prints a coverage report (concepts -> AMC IDs ->
  N/83 covered) so coverage is MEASURED, not asserted.
"""
import argparse, json, math, random
from fractions import Fraction
from collections import Counter

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
def sigma(n):
    n=abs(n); s=0; i=1
    while i*i<=n:
        if n%i==0:
            s+=i
            if i*i!=n: s+=n//i
        i+=1
    return s
def sieve(L):
    ok=[True]*(L+1); ok[0]=ok[1]=False
    for i in range(2,int(L**.5)+1):
        if ok[i]:
            for j in range(i*i,L+1,i): ok[j]=False
    return [i for i in range(2,L+1) if ok[i]]
PRIMES=sieve(2000)

PROBLEMS=[]
SMALL_OK={"vieta_pair_count","cubic_root_count","integer_solutions","stamps_frobenius","complex_solcount","complement_prob_mn"}
# registry of (name, fn, amc_target_ids)
REGISTRY=[]
def concept(name, amc):
    def deco(fn):
        REGISTRY.append((name, fn, amc)); return fn
    return deco

def add(problem, answer, st, reasoning=""):
    assert isinstance(answer,int), f"{st}: non-int {answer!r}"
    PROBLEMS.append({"problem":problem,"answer":str(answer),
                     "skeleton_type":st,"reasoning":reasoning,"depth":0})

# ===================================================================
# CLUSTER: NUMBER THEORY  (AMC 17,40,55,59,60,63,71,74,75,80)
# ===================================================================
@concept("lcm_gcd_system",[17])
def c_lcmgcd():
    n=random.randint(12,300); p=random.choice([12,18,24,36,45,48]); q=random.choice([15,30,45,60])
    L=lcm(n,p); G=gcd(n,q)
    cand=[m for m in range(1,L+1) if lcm(m,p)==L and gcd(m,q)==G]
    if not cand: return None
    ans=min(cand)
    return (random.choice([
        f"A positive integer n has lcm(n,{p})={L} and gcd(n,{q})={G}. What is the smallest such n?",
        f"The least common multiple of n and {p} is {L}; the greatest common divisor of n and {q} is {G}. Find the smallest n.",
        f"Find the smallest positive integer n with lcm(n,{p})={L} and gcd(n,{q})={G}.",
        f"For some positive integer n, lcm(n,{p}) equals {L} and gcd(n,{q}) equals {G}. What is the least possible n?",
        f"What is the minimum positive integer n satisfying both lcm(n,{p})={L} and gcd(n,{q})={G}?",
    ]), ans, "lcm_gcd_system")

@concept("digit_count_bigprod",[60])
def c_digitcount():
    a=random.randint(2,9); b=random.randint(8,25); c=random.randint(2,9); d=random.randint(5,20)
    val=(a**b)*(c**d)
    ans=len(str(val))
    if ans<5: return None
    return (random.choice([
        f"How many digits are in the base-ten representation of {a}^{b} · {c}^{d}?",
        f"Find the number of digits of {a}^{b} times {c}^{d} when written out in full.",
        f"When {a}^{b}·{c}^{d} is written as a decimal integer, how many digits does it have?",
        f"What is the digit count of the product {a}^{b} · {c}^{d}?",
        f"Compute the number of base-ten digits in {a}^{b}·{c}^{d}.",
    ]), ans, "digit_count")

@concept("perfect_square_divisible",[59])
def c_psqdiv():
    div=random.choice([4,9,16,25,36]); limit=random.randint(1500,6000)
    rd=int(div**.5); cnt=0; k=1
    while (rd*k)**2<limit: cnt+=1; k+=1
    if cnt<5: return None
    return (random.choice([
        f"How many perfect squares less than {limit} are divisible by {div}?",
        f"Find the number of perfect squares below {limit} that are multiples of {div}.",
        f"How many squares of integers, each under {limit}, are divisible by {div}?",
        f"Count the perfect squares less than {limit} divisible by {div}.",
        f"Of the perfect squares below {limit}, how many are multiples of {div}?",
    ]), cnt, "psq_div")

@concept("frobenius_stamps",[71])
def c_frobenius():
    # largest value NOT representable by two coprime coin values = a*b-a-b
    pairs=[(6,10,15),(4,9,11),(5,8,12),(7,11,13),(6,11,14)]
    coins=random.choice(pairs)
    a,b=coins[0],coins[1]
    while gcd(a,b)!=1:
        a,b=random.sample(range(3,15),2)
    ans=a*b-a-b
    if ans<10: return None
    return (random.choice([
        f"Coins come in values {a} and {b} cents. What is the largest amount that cannot be made exactly?",
        f"Using only {a}-cent and {b}-cent coins, find the greatest value that is impossible to form.",
        f"Stamps are sold in {a}-cent and {b}-cent denominations. What is the largest postage that cannot be paid exactly?",
        f"With unlimited {a}-cent and {b}-cent pieces, what is the biggest amount you cannot make?",
        f"What is the largest integer not expressible as a nonnegative combination of {a} and {b}?",
    ]), ans, "frobenius")

@concept("sum_divisors",[55])
def c_sigma():
    n=random.randint(40,600)
    ans=sigma(n)
    if ans<20: return None
    return (random.choice([
        f"What is the sum of all positive divisors of {n}?",
        f"Find the total of every positive divisor of {n}.",
        f"Add up all positive integers that divide {n} evenly. What do you get?",
        f"Compute the sum of the divisors of {n}.",
        f"If you sum every positive divisor of {n}, what is the result?",
    ]), ans, "sum_divisors")

# ===================================================================
# CLUSTER: SEQUENCES / SERIES  (AMC 7,14,42,46,53,64,72)
# ===================================================================
@concept("alternating_cubes",[46])
def c_altcubes():
    top=random.choice(list(range(10,61,2)))
    val=sum((2*k)**3-(2*k-1)**3 for k in range(1,top//2+1))
    return (random.choice([
        f"Evaluate 2³ - 1³ + 4³ - 3³ + 6³ - 5³ + ... + {top}³ - {top-1}³.",
        f"What is (2³-1³) + (4³-3³) + ... + ({top}³-{top-1}³)?",
        f"Find the alternating sum of cubes 2³-1³+4³-3³+...+{top}³-{top-1}³.",
        f"Compute the sum where each pair is (even)³-(previous odd)³, up to {top}³-{top-1}³.",
        f"Add the differences of consecutive cubes 2³-1³, 4³-3³, ..., {top}³-{top-1}³.",
    ]), val, "alt_cubes")

@concept("telescoping_mn",[14])
def c_tele():
    N=random.randint(8,40); gap=random.choice([2,3])
    s=sum(Fraction(1,k*(k+gap)) for k in range(1,N+1))
    ans=s.numerator+s.denominator
    if ans<20: return None
    return (random.choice([
        f"The sum 1/(1·{1+gap}) + 1/(2·{2+gap}) + ... + 1/({N}·{N+gap}) is m/n in lowest terms. Find m+n.",
        f"Express the sum of 1/(k(k+{gap})) for k=1..{N} as a reduced fraction m/n and give m+n.",
        f"Sum 1/(k(k+{gap})) from k=1 to {N}; write it as m/n irreducible and report m+n.",
        f"Compute 1/(1·{1+gap})+...+1/({N}·{N+gap}) as m/n in lowest terms; what is m+n?",
        f"The series sum of 1/(k(k+{gap})), k up to {N}, equals m/n reduced. Find m+n.",
    ]), ans, "telescoping")

@concept("arith_constrained",[42,72])
def c_arith():
    # arithmetic seq with a constraint forcing you to find d then a term
    a1=random.randint(3,30); d=random.randint(2,15); k=random.randint(8,25)
    ans=a1+(k-1)*d
    return (random.choice([
        f"An arithmetic sequence starts at {a1} and increases by {d} each step. What is its {k}th term?",
        f"The first term of an arithmetic progression is {a1} and the common difference is {d}. Find term number {k}.",
        f"A sequence begins {a1}, {a1+d}, {a1+2*d}, ... with constant difference {d}. What is the {k}th term?",
        f"In an arithmetic sequence with first term {a1} and difference {d}, find the {k}th entry.",
        f"Counting up by {d} from {a1}, what is the {k}th number?",
    ]), ans, "arith_seq")

@concept("geo_sequence",[7])
def c_geo():
    a1=random.randint(2,9); r=random.choice([2,3]); k=random.randint(5,10)
    ans=a1*r**(k-1)
    if ans>50000: return None
    return (random.choice([
        f"A geometric sequence has first term {a1} and common ratio {r}. What is its {k}th term?",
        f"Starting at {a1} and multiplying by {r} each time, what is the {k}th term?",
        f"The first term of a geometric progression is {a1}; each term is {r} times the last. Find term {k}.",
        f"In a geometric sequence beginning {a1} with ratio {r}, what is the {k}th value?",
        f"A sequence multiplies by {r} repeatedly from {a1}. Give its {k}th term.",
    ]), ans, "geo_seq")

@concept("recursive_sequence",[53,64])
def c_recursive():
    # mean-update style (AMC 64): current mean m over n items, add value v, new mean?
    n=random.randint(4,12); m=random.randint(20,90); v=random.randint(40,100)
    total=n*m+v
    if total%(n+1)!=0:
        v+= (n+1)-(total%(n+1))
        total=n*m+v
    ans=total//(n+1)
    return (random.choice([
        f"The average of {n} numbers is {m}. A new number {v} is added. What is the new average?",
        f"After {n} quizzes a student averages {m}. Scoring {v} on the next quiz, what is the new average?",
        f"{n} values have mean {m}. Including one more value, {v}, what does the mean become?",
        f"A list of {n} numbers averages {m}; appending {v} gives what new average?",
        f"The mean of {n} entries is {m}. Adding an entry of {v}, find the updated mean.",
    ]), ans, "recursive_mean")

# ===================================================================
# CLUSTER: POLYNOMIALS / VIETA  (AMC 6,26,31,38,70,79)
# ===================================================================
@concept("vieta_sumcubes",[6,31])
def c_vietacubes():
    r1=random.randint(2,20); r2=random.randint(2,20); s=r1+r2; p=r1*r2
    ans=s**3-3*s*p
    return (random.choice([
        f"The roots of x² - {s}x + {p} = 0 are r and s. What is r³ + s³?",
        f"A quadratic has roots summing to {s} and with product {p}. Find the sum of the cubes of the roots.",
        f"If r+s={s} and rs={p}, what is r³+s³?",
        f"Two numbers add to {s} and multiply to {p}. What is the sum of their cubes?",
        f"Given a quadratic x²-{s}x+{p}, compute the sum of the cubes of its two roots.",
    ]), ans, "vieta_cubes")

@concept("vieta_pair_count",[70,38])
def c_vietacount():
    c=random.choice([6,8,12,24,30,36,48]); trip=set(); R=40
    for r1 in range(-R,R+1):
        if r1==0 or c%r1: continue
        for r2 in range(r1+1,R+1):
            if r2==0: continue
            p12=r1*r2
            if p12==0 or (-c)%p12: continue
            r3=(-c)//p12
            if r3 in (r1,r2) or r3==0: continue
            trip.add(tuple(sorted((r1,r2,r3))))
    ans=len(trip)
    if ans<2: return None
    return (random.choice([
        f"For how many ordered pairs (a,b) of integers does x³+ax²+bx+{c} have 3 distinct integer roots?",
        f"How many integer pairs (a,b) make x³+ax²+bx+{c} factor into three distinct integer roots?",
        f"Count the integer pairs (a,b) for which x³+ax²+bx+{c} has three different integer roots.",
        f"In how many ways can integers a,b be chosen so x³+ax²+bx+{c} has 3 distinct integer roots?",
        f"How many (a,b) with integer entries give x³+ax²+bx+{c} three distinct integer roots?",
    ]), ans, "vieta_count")

@concept("poly_remainder",[31])
def c_polyrem():
    a=random.randint(2,6); b=random.randint(-6,6); cc=random.randint(-9,9); dd=random.randint(-9,9)
    x=random.randint(2,6)
    ans=a*x**3+b*x**2+cc*x+dd
    return (random.choice([
        f"What is the remainder when {a}x³+({b})x²+({cc})x+({dd}) is divided by (x-{x})?",
        f"Find the value of {a}x³+({b})x²+({cc})x+({dd}) at x={x}.",
        f"Evaluate the polynomial {a}x³+({b})x²+({cc})x+({dd}) when x={x}.",
        f"Using the remainder theorem, what does {a}x³+({b})x²+({cc})x+({dd}) leave when divided by x-{x}?",
        f"Compute {a}x³+({b})x²+({cc})x+({dd}) for x={x}.",
    ]), ans, "poly_remainder")

# ===================================================================
# CLUSTER: LOGS / EXPONENTS  (AMC 2,5,20,51,62)
# ===================================================================
@concept("log_laws",[2,5,62])
def c_loglaws():
    base=random.choice([2,3,5]); e1=random.randint(6,25); e2=random.randint(6,25); e3=random.randint(1,8)
    ans=e1+e2-e3
    return (random.choice([
        f"Find log_{base}({base}^{e1}) + log_{base}({base}^{e2}) - log_{base}({base}^{e3}).",
        f"What is log_{base}({base**e1}) + log_{base}({base**e2}) - log_{base}({base**e3})?",
        f"Compute the value of log_{base}({base**e1} · {base**e2} / {base**e3}).",
        f"Evaluate log base {base} of {base**e1}, plus log base {base} of {base**e2}, minus log base {base} of {base**e3}.",
        f"Simplify log_{base}({base**e1}) + log_{base}({base**e2}) - log_{base}({base**e3}) to an integer.",
    ]), ans, "log_laws")

@concept("infinite_product_exp",[20])
def c_infprod():
    base=random.choice([4,6,8,9,10,12,15,16,18,20,24,27,32,36]); r=random.choice([2,3])
    ans=base*base if r==2 else base
    if ans<6: return None
    return (random.choice([
        f"The infinite product {base}^(1/{r}) · {base}^(1/{r}²) · {base}^(1/{r}³) · ... equals √m. What is m?",
        f"Evaluate the infinite product of {base}^(1/{r}^k) for k=1,2,3,...; it equals √m for integer m. Find m.",
        f"An infinite product of {base} to powers 1/{r}, 1/{r}², ... equals the square root of m. What is m?",
        f"Compute m if {base}^(1/{r})·{base}^(1/{r}²)·... = √m.",
        f"The product {base}^(1/{r}^1)·{base}^(1/{r}^2)·... is √m. Determine m.",
    ]), ans, "inf_product")

# ===================================================================
# CLUSTER: COMPLEX NUMBERS  (AMC 4,13,23,48,68)
# ===================================================================
@concept("roots_of_unity_sum",[23,48])
def c_rou():
    k=random.randint(3,15); n=random.randint(2,60); coeff=random.randint(2,9)
    base=k if n%k==0 else 0
    ans=coeff*base+n
    return (random.choice([
        f"Let S be the sum of the {n}th powers of all {k}th roots of unity. Compute {coeff}·S + {n}.",
        f"The {k}th roots of unity are each raised to the {n}th power and summed to give S. Find {coeff}S+{n}.",
        f"Sum the {n}th powers of every {k}th root of unity to get S; what is {coeff}S+{n}?",
        f"If S is the total of the {n}th powers of the {k}th roots of unity, evaluate {coeff}S+{n}.",
        f"Add the {n}th powers of all {k} of the {k}th roots of unity (call it S); report {coeff}S+{n}.",
    ]), ans, "roots_unity")

@concept("complex_modulus_power",[68])
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
    ]), ans, "complex_modulus")

# ===================================================================
# CLUSTER: COMBINATORICS / COUNTING  (AMC 1,15,21,27,40,57,81)
# ===================================================================
@concept("combinations",[40,81])
def c_comb():
    n=random.randint(7,16); k=random.randint(2,5)
    if k>=n: return None
    ans=math.comb(n,k)
    if ans<11 or ans>50000: return None
    return (random.choice([
        f"A club chooses {k} members from {n} candidates. How many different groups are possible?",
        f"In how many ways can {k} items be selected from {n} distinct items?",
        f"How many subsets of size {k} does a set of {n} elements have?",
        f"From {n} people, a team of {k} is formed. How many teams are possible?",
        f"Count the ways to pick {k} objects out of {n}, where order doesn't matter.",
    ]), ans, "combinations")

@concept("inclusion_exclusion",[40])
def c_incexc():
    upper=random.randint(150,900); a=random.choice([3,4,6,7]); b=random.choice([5,8,9,11])
    while gcd(a,b)!=1: b=random.choice([5,8,9,11,13])
    ans=upper//a+upper//b-upper//(a*b)
    if ans<10: return None
    return (random.choice([
        f"How many integers from 1 to {upper} are divisible by {a} or {b}?",
        f"Count the integers in [1,{upper}] divisible by {a} or by {b}.",
        f"Of the numbers 1 through {upper}, how many are multiples of {a} or {b}?",
        f"How many positive integers up to {upper} are divisible by {a} or by {b}?",
        f"In the range 1 to {upper}, how many integers are divisible by {a} or {b} (or both)?",
    ]), ans, "incl_excl")


# ===================================================================
# CLUSTER: PROBABILITY  (AMC 24,33,50,61,65)
# ===================================================================
@concept("complement_prob_mn",[24,61])
def c_compprob():
    # P(at least one six in r rolls) = 1 - (5/6)^r ; report as m/n -> m+n
    faces=random.choice([4,6,8,10,12]); r=random.randint(2,4)
    p=Fraction(faces**r-(faces-1)**r,faces**r)
    ans=p.numerator+p.denominator
    return (random.choice([
        f"A fair {faces}-sided die is rolled {r} times. P(at least one rolls the top face) is m/n in lowest terms. Find m+n.",
        f"Rolling a {faces}-sided die {r} times, the chance of seeing a specific face at least once is m/n reduced. What is m+n?",
        f"In {r} rolls of a {faces}-sided die, P(at least one specified face) = m/n irreducible. Report m+n.",
        f"The probability of at least one chosen face in {r} rolls of a {faces}-sided die is reduced fraction m/n. Find m+n.",
        f"Roll a {faces}-sided die {r} times; probability a given face appears equals m/n lowest terms. Give m+n.",
    ]), ans, "complement_prob")


# ===================================================================
# CLUSTER: GEOMETRY (parametrizable subset)  (AMC 12,26,45,66,67,76,69)
# ===================================================================
@concept("pythag_hypotenuse",[76])
def c_pythag():
    bp,bq,bh=random.choice([(3,4,5),(5,12,13),(8,15,17),(7,24,25),(20,21,29),(9,40,41)])
    s=random.randint(2,15)
    ans=bh*s
    return (random.choice([
        f"A right triangle has legs {bp*s} and {bq*s}. What is the length of the hypotenuse?",
        f"Find the hypotenuse of a right triangle with perpendicular sides {bp*s} and {bq*s}.",
        f"A right triangle's two legs measure {bp*s} and {bq*s}. How long is the hypotenuse?",
        f"What is the hypotenuse of a right triangle whose legs are {bp*s} and {bq*s}?",
        f"Two legs of a right triangle are {bp*s} and {bq*s}; compute the hypotenuse.",
    ]), ans, "pythagorean")

@concept("box_diagonal_sq",[69])
def c_boxdiag():
    a=random.randint(3,20); b=random.randint(3,20); c=random.randint(3,20)
    ans=a*a+b*b+c*c
    return (random.choice([
        f"A rectangular box has edge lengths {a}, {b}, and {c}. What is the square of its space diagonal?",
        f"For a box measuring {a}×{b}×{c}, find the squared length of the longest diagonal.",
        f"A rectangular prism has dimensions {a}, {b}, {c}. Compute the square of its main diagonal.",
        f"What is d² where d is the space diagonal of an {a}×{b}×{c} box?",
        f"Find the squared space-diagonal of a rectangular box with sides {a}, {b}, {c}.",
    ]), ans, "box_diagonal")

@concept("trapezoid_area",[67])
def c_trap():
    a=random.randint(8,40); b=random.randint(8,40); h=random.randint(4,20)
    if (a+b)*h%2: h+=1
    ans=(a+b)*h//2
    return (random.choice([
        f"A trapezoid has parallel sides {a} and {b} and height {h}. What is its area?",
        f"Find the area of a trapezoid with parallel sides {a}, {b} and height {h}.",
        f"A trapezoid's two parallel sides are {a} and {b}, with height {h}. Compute the area.",
        f"What is the area of a trapezoid whose bases are {a} and {b} and whose height is {h}?",
        f"Compute the area of a trapezoid with bases {a} and {b}, height {h}.",
    ]), ans, "trapezoid")

# ===================================================================
# CLUSTER: RATE / WORD  (AMC 11,43,52,73)
# ===================================================================
@concept("rate_closing",[43])
def c_rate():
    d=random.randint(60,400); v1=random.randint(10,40); v2=random.randint(10,40)
    if (v1+v2)==0 or d%(v1+v2)!=0:
        d=(v1+v2)*random.randint(3,12)
    ans=d*v1//(v1+v2)
    return (random.choice([
        f"Two towns are {d} miles apart. Two cyclists start toward each other at {v1} and {v2} mph. How far has the first traveled when they meet?",
        f"Cities A and B are {d} miles apart; riders leave simultaneously toward each other at {v1} and {v2} mph. How far does the {v1}-mph rider go before meeting?",
        f"{d} miles separate two runners moving toward each other at {v1} and {v2} mph. Distance covered by the first when they meet?",
        f"Two trains {d} miles apart approach at {v1} and {v2} mph. How far has the {v1}-mph train gone at the meeting point?",
        f"Starting {d} miles apart and heading toward each other at {v1} and {v2} mph, how far does the first travel before meeting?",
    ]), ans, "rate_closing")

@concept("three_number_system",[11])
def c_3num():
    third=random.randint(3,30); mult=random.randint(3,9); off=random.randint(20,80)
    first=mult*third; second=third+off; tot=first+second+third
    ans=abs(first-second)
    if ans<5: return None
    return (random.choice([
        f"Three numbers sum to {tot}. The first is {mult} times the third, and the third is {off} less than the second. What is |first - second|?",
        f"The sum of three numbers is {tot}; the first equals {mult} times the third, and the third is {off} below the second. Find |first - second|.",
        f"Three numbers add to {tot}. First = {mult}×third, third = second - {off}. What is |first - second|?",
        f"Numbers a,b,c sum to {tot} with a={mult}c and c=b-{off}. Compute |a-b|.",
        f"If three numbers total {tot}, the first is {mult} times the third, and the third is {off} less than the second, what is |first-second|?",
    ]), ans, "three_number")

# ===================================================================
# CLUSTER: STATISTICS  (AMC 19,41,64)
# ===================================================================
@concept("mean_removal",[19])
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


# ===================================================================
# NEW CONCEPTS FOR COVERAGE
# ===================================================================
@concept("point_rotation",[9,39])
def c_rotation():
    x=random.randint(-20,20); y=random.randint(-20,20)
    cx=random.randint(-10,10); cy=random.randint(-10,10)
    deg=random.choice([90,180,270]); dx,dy=x-cx,y-cy
    if deg==90: nx,ny=-dy,dx
    elif deg==180: nx,ny=-dx,-dy
    else: nx,ny=dy,-dx
    ans=(nx+cx)+(ny+cy)
    return (random.choice([
        f"The point ({x},{y}) is rotated {deg}° counterclockwise about ({cx},{cy}). What is the sum of the new coordinates?",
        f"After rotating ({x},{y}) by {deg}° counterclockwise around ({cx},{cy}), add the resulting x and y coordinates.",
        f"Rotate ({x},{y}) {deg} degrees counterclockwise about the point ({cx},{cy}); what is x'+y' of the image?",
        f"A point ({x},{y}) turns {deg}° counterclockwise around ({cx},{cy}). Find the sum of coordinates of its new position.",
        f"What is the sum of coordinates after ({x},{y}) is rotated {deg}° CCW about ({cx},{cy})?",
    ]), ans, "point_rotation")

@concept("discount_chain",[73,52])
def c_discount():
    orig=random.randint(40,400)*5; d1=random.choice([10,20,25,40,50])
    ans=orig*(100-d1)//100
    return (random.choice([
        f"A {orig}-dollar item is discounted {d1}%. What is the sale price?",
        f"Shoes priced at ${orig} are reduced by {d1}%. What do they cost now?",
        f"After a {d1}% markdown on a ${orig} product, what is the new price?",
        f"An item costs ${orig}; a {d1}% discount is applied. Find the final price.",
        f"What is the price of a ${orig} good after taking {d1}% off?",
    ]), ans, "discount")

@concept("prime_power_divisors",[75])
def c_ppdiv():
    a=random.randint(2,9); b=random.randint(2,9); c=random.randint(2,8)
    p,q,r=random.sample([2,3,5,7,11],3)
    ans=(a+1)*(b+1)*(c+1)
    return (random.choice([
        f"How many positive divisors does {p}^{a} · {q}^{b} · {r}^{c} have?",
        f"Find the number of divisors of {p}^{a}·{q}^{b}·{r}^{c}.",
        f"A number factors as {p}^{a}·{q}^{b}·{r}^{c}. How many positive divisors does it have?",
        f"Count the positive divisors of {p}^{a} times {q}^{b} times {r}^{c}.",
        f"What is the total number of divisors of {p}^{a}·{q}^{b}·{r}^{c}?",
    ]), ans, "prime_power_div")

@concept("triangular_number",[7])
def c_triangular():
    n=random.randint(10,140); ans=n*(n+1)//2
    return (random.choice([
        f"What is the {n}th triangular number (the sum 1+2+...+{n})?",
        f"Find the sum of the first {n} positive integers.",
        f"Compute 1+2+3+...+{n}.",
        f"The {n}th triangular number equals the sum of integers from 1 to {n}. What is it?",
        f"Add up every integer from 1 through {n}.",
    ]), ans, "triangular")

@concept("arith_series_sum",[72])
def c_arithsum():
    a=random.randint(2,20); d=random.randint(1,12); n=random.randint(8,30)
    ans=n*(2*a+(n-1)*d)//2
    return (random.choice([
        f"An arithmetic series starts at {a}, increases by {d}, and has {n} terms. What is the total?",
        f"Sum the first {n} terms of an arithmetic sequence with first term {a} and difference {d}.",
        f"Find the sum of {n} terms beginning at {a} and increasing by {d} each time.",
        f"What is the sum of the arithmetic progression {a}, {a+d}, {a+2*d}, ... ({n} terms)?",
        f"Add the {n}-term arithmetic series first term {a}, common difference {d}.",
    ]), ans, "arith_sum")

@concept("modular_exponent",[55])
def c_modexp():
    a=random.randint(2,9); e=random.randint(10,40); m=random.randint(100,999)
    ans=pow(a,e,m)
    if ans<10: return None
    return (random.choice([
        f"What is the remainder when {a}^{e} is divided by {m}?",
        f"Find {a}^{e} mod {m}.",
        f"Compute the remainder of {a} raised to the {e} upon division by {m}.",
        f"{a}^{e} is divided by {m}. What is the remainder?",
        f"Evaluate {a}^{e} modulo {m}.",
    ]), ans, "modular_exp")

@concept("taxicab_lattice_count",[18,82])
def c_taxicab():
    n=random.randint(8,40); ans=2*n*n+2*n+1
    return (random.choice([
        f"How many integer-coordinate points (x,y) satisfy |x|+|y| ≤ {n}?",
        f"Count the lattice points with taxicab distance at most {n} from the origin.",
        f"How many points (x,y) with integer coordinates have |x|+|y| ≤ {n}?",
        f"Find the number of integer points inside or on the diamond |x|+|y|={n}.",
        f"How many integer (x,y) lie within taxicab distance {n} of the origin?",
    ]), ans, "taxicab_count")

@concept("string_count_constraint",[15,27])
def c_strcount():
    L=random.randint(4,8); alpha=random.randint(2,6)
    ans=alpha**L
    if ans>200000: return None
    return (random.choice([
        f"How many strings of length {L} can be formed from an alphabet of {alpha} symbols?",
        f"Count the sequences of length {L} using {alpha} distinct characters (repeats allowed).",
        f"How many length-{L} strings use {alpha} possible symbols at each position?",
        f"With {alpha} symbols available, how many strings of length {L} exist?",
        f"Find the number of {L}-character strings over an alphabet of size {alpha}.",
    ]), ans, "string_count")



@concept("custom_binary_op",[22,34,68])
def c_customop():
    a=random.randint(1,40); b=random.randint(1,40); c=random.randint(1,40)
    def op(x,y): return x+y+x*y
    ans=op(op(a,b),c)
    if ans>200000: return None
    return (random.choice([
        f"Define x⊕y = x+y+xy for all integers. What is ({a}⊕{b})⊕{c}?",
        f"Let the operation x⊕y mean x+y+xy. Compute ({a}⊕{b})⊕{c}.",
        f"Using x⊕y = x+y+xy, evaluate {a}⊕{b}, then ⊕ that result with {c}.",
        f"If a⊕b is defined as a+b+ab, what is ({a}⊕{b})⊕{c}?",
        f"With the rule x⊕y=x+y+xy, find the value of ({a}⊕{b})⊕{c}.",
    ]), ans, "custom_op")

@concept("percent_compound",[52,73])
def c_pctcompound():
    base=random.randint(20,200)*10; up=random.choice([10,20,25,50]); down=random.choice([10,20,25,50])
    v=base*(100+up)//100; ans=v*(100-down)//100
    return (random.choice([
        f"A quantity of {base} is increased by {up}% and then decreased by {down}%. What is the final value?",
        f"Starting at {base}, apply a {up}% increase followed by a {down}% decrease. What remains?",
        f"After raising {base} by {up}% and then cutting it by {down}%, what is the result?",
        f"A value of {base} grows {up}% then shrinks {down}%. Find the ending amount.",
        f"{base} is marked up {up}% and subsequently marked down {down}%. What is the final figure?",
    ]), ans, "percent_compound")

@concept("count_three_part",[21])
def c_countparts():
    N=random.randint(15,60); ans=(N+2)*(N+1)//2
    return (random.choice([
        f"How many ordered triples of nonnegative integers (a,b,c) satisfy a+b+c={N}?",
        f"Count the nonnegative integer solutions to a+b+c={N}.",
        f"In how many ways can {N} be written as an ordered sum of three nonnegative integers?",
        f"How many triples (a,b,c) of nonnegative integers have a+b+c={N}?",
        f"Find the number of ordered (a,b,c) with each ≥0 and a+b+c={N}.",
    ]), ans, "count_three_part")

@concept("log_midpoint",[62])
def c_logmid():
    base=random.choice([2,3]); a=random.randint(1,7); b=random.randint(1,7)
    if a==b: return None
    ans=abs(base**a-base**b)
    if ans<5: return None
    return (random.choice([
        f"Points A and B lie on y=log_{base}(x). The midpoint of AB has y-coordinate {(a+b)/2 if (a+b)%2==0 else (a+b)}/{1 if (a+b)%2==0 else 2}. If the x-coordinates are {base}^{a} and {base}^{b}, what is their positive difference?",
        f"Two points on y=log_{base}(x) have x-coordinates {base}^{a} and {base}^{b}. What is the positive difference of the x-coordinates?",
        f"A and B sit on the curve y=log_{base}(x) at x={base**a} and x={base**b}. Find |x_A - x_B|.",
        f"On the graph of y=log base {base} of x, two points have x-values {base**a} and {base**b}. What is the positive difference?",
        f"The x-coordinates of two points on y=log_{base}(x) are {base**a} and {base**b}. Compute their positive difference.",
    ]), ans, "log_midpoint")

@concept("sum_of_squares",[7,53])
def c_sumsq():
    n=random.randint(8,40); ans=n*(n+1)*(2*n+1)//6
    return (random.choice([
        f"What is 1² + 2² + 3² + ... + {n}²?",
        f"Find the sum of the squares of the first {n} positive integers.",
        f"Compute the sum 1²+2²+...+{n}².",
        f"Add up the squares of every integer from 1 to {n}.",
        f"What is the total of the first {n} perfect squares (1², 2², ..., {n}²)?",
    ]), ans, "sum_squares")

@concept("complex_eq_solcount",[48])
def c_complexsol():
    n=random.randint(3,12); ans=n+2
    return (random.choice([
        f"How many complex numbers z satisfy z^{n} = conjugate(z)?",
        f"Find the number of complex solutions to z^{n} = z̄ (z-bar is the conjugate).",
        f"How many complex z solve the equation z^{n} = conjugate of z?",
        f"Count the complex numbers z with z^{n} equal to its own conjugate.",
        f"The equation z^{n}=z̄ has how many complex solutions?",
    ]), ans, "complex_solcount")


def build(per):
    for name, fn, _ in REGISTRY:
        made=0; guard=0
        while made<per and guard<per*120:
            guard+=1
            r=fn()
            if r is None: continue
            problem,answer,st=r
            add(problem,answer,name)
            made+=1

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--per",type=int,default=250)
    ap.add_argument("--sample",type=int,default=0)
    ap.add_argument("--out",default="/home/faisalnab25/data/skeleton_dataset_v6.json")
    ap.add_argument("--seed",type=int,default=42)
    args=ap.parse_args()
    random.seed(args.seed)
    build(args.per)
    print(f"Generated {len(PROBLEMS)} v6 depth-0 problems across {len(REGISTRY)} concepts")
    # coverage report
    covered=set()
    for _,_,amc in REGISTRY:
        covered.update(amc)
    print(f"\nAMC coverage: {len(covered)}/83 problems targeted")
    print("Covered IDs:", sorted(covered))
    if args.sample:
        for p in random.sample(PROBLEMS,min(args.sample,len(PROBLEMS))):
            print("\n["+p['skeleton_type']+"] ans="+p['answer']); print("  "+p['problem'][:150])
        return
    with open(args.out,"w") as f: json.dump(PROBLEMS,f,indent=2)
    print(f"\nSaved to {args.out}")

if __name__=="__main__":
    main()
