#!/usr/bin/env python3
"""
skeleton_injector_v6_focused.py — CalibrateRL FOCUSED depth-0 generator for the 7B

WHY THIS EXISTS:
  The v5 broad-coverage run (40 concepts) on Qwen2.5-7B-Instruct showed 65%
  too-easy: single-method concepts saturate regardless of topic. Only ~9
  concepts produced 7B signal, all sharing one property -- SUSTAINED MULTI-STEP
  COMPUTATION where errors accumulate. This generator keeps ONLY those, with the
  too-hard ones EASED into the goldilocks band using exact parameter cliffs read
  from the calib_v5_7B run.

  This is the depth-0 "engine" set: narrow AMC coverage (~15 problems) but every
  concept produces real gradient for the 7B. Broad coverage returns at depth-1+
  via composition, where these engines anchor chains that pull in the saturated
  concepts as components.

PER-CONCEPT CALIBRATION (from calib_v5_7B.json, 300 problems x 16 rollouts):
  KEEP as-is (already in-band):
    lcm_gcd_system        mean 0.38  (5/6 goldilocks)  -- BEST
    alternating_cubes     mean 0.51  (6/7 goldilocks)  -- BEST
    complex_eq_solcount   mean 0.62  (3/4 goldilocks)
    custom_binary_op      mean 0.78  (2/4 goldilocks)
    perfect_square_div    mean 0.83  (3/8 goldilocks)
  EASED into band (were too HARD -- exact cliffs from the run):
    telescoping_mn   N 8..40 -> 6..16   (N>=26 was 0-1/16; N=14 was 3/16)
    taxicab_count    n 8..40 -> 6..16   (n>=20 was 0/16)
    modular_exponent exp 10..40 -> 6..16, mod 100..999 -> 50..300  (5^12 mod310 was 7/16; exp>=22 dead)
    vieta_pair_count search R 40 -> 22, c in {6,8,12,24}  (was 0.05; the search length is the difficulty)

  LENGTH KNOB: concepts whose difficulty scales with computation length take a
  `length`-style parameter as the PRIMARY difficulty axis (sets up the depth
  curriculum: longer = harder, same concept).

  Dropped: the 31 single-method concepts (geo_seq, combinations, box_diagonal,
  vieta_sumcubes, divisors, inclusion_exclusion, rate, etc.) -- 16/16 for 7B,
  no depth-0 fix. They return as depth-1 chain components, not standalone.
"""
import argparse, json, math, random
from fractions import Fraction
from collections import Counter

def gcd(a,b):
    while b: a,b=b,a%b
    return abs(a)
def lcm(a,b): return a*b//gcd(a,b)

PROBLEMS=[]
SMALL_OK={"vieta_pair_count","complex_eq_solcount"}  # count-type: small answers inherent
REGISTRY=[]
def concept(name, amc):
    def deco(fn): REGISTRY.append((name,fn,amc)); return fn
    return deco
def add(problem, answer, st):
    assert isinstance(answer,int), f"{st}: non-int {answer!r}"
    PROBLEMS.append({"problem":problem,"answer":str(answer),"skeleton_type":st,"depth":0})

# ============================ KEEP (in-band, unchanged) ============================
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

@concept("alternating_cubes",[46])
def c_altcubes():
    # LENGTH KNOB: top controls number of terms. Run showed in-band across 12..50.
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
    n=random.randint(3,12); ans=n+2
    return (random.choice([
        f"How many complex numbers z satisfy z^{n} = conjugate(z)?",
        f"Find the number of complex solutions to z^{n} = z̄ (z-bar is the conjugate).",
        f"How many complex z solve the equation z^{n} = conjugate of z?",
        f"Count the complex numbers z with z^{n} equal to its own conjugate.",
        f"The equation z^{n}=z̄ has how many complex solutions?",
    ]), ans, "complex_eq_solcount")

@concept("custom_binary_op",[22,34])
def c_customop():
    a=random.randint(8,40); b=random.randint(8,40); c=random.randint(8,40)
    def op(x,y): return x+y+x*y
    ans=op(op(a,b),c)
    if ans>200000: return None
    return (random.choice([
        f"Define x⊕y = x+y+xy for all integers. What is ({a}⊕{b})⊕{c}?",
        f"Let the operation x⊕y mean x+y+xy. Compute ({a}⊕{b})⊕{c}.",
        f"Using x⊕y = x+y+xy, evaluate {a}⊕{b}, then ⊕ that result with {c}.",
        f"If a⊕b is defined as a+b+ab, what is ({a}⊕{b})⊕{c}?",
        f"With the rule x⊕y=x+y+xy, find the value of ({a}⊕{b})⊕{c}.",
    ]), ans, "custom_binary_op")

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

# ============================ EASED (were too hard) ============================
@concept("telescoping_mn",[14])
def c_tele():
    # EASED: N 8..40 -> 6..16 (N>=26 was dead; N~14 borderline). gap 2 or 3.
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


@concept("modular_exponent",[55])
def c_modexp():
    # EASED: exp 10..40 -> 6..16, mod 100..999 -> 50..300 (5^12 mod310 was 7/16).
    a=random.randint(2,9); e=random.randint(6,16); m=random.randint(50,300)
    ans=pow(a,e,m)
    if ans<10: return None
    return (random.choice([
        f"What is the remainder when {a}^{e} is divided by {m}?",
        f"Find {a}^{e} mod {m}.",
        f"Compute the remainder of {a} raised to the {e} upon division by {m}.",
        f"{a}^{e} is divided by {m}. What is the remainder?",
        f"Evaluate {a}^{e} modulo {m}.",
    ]), ans, "modular_exponent")


@concept("digit_power_sum",[60])
def c_digitpow():
    # ADDED BACK as a long-execution concept: digit sum of a power (error-prone)
    base=random.randint(2,9); exp=random.randint(8,18); val=base**exp
    ans=sum(int(d) for d in str(val))
    if ans<10: return None
    return (random.choice([
        f"What is the sum of the digits of {base}^{exp}?",
        f"Find the digit sum of {base} raised to the power {exp}.",
        f"Compute the sum of all digits in the decimal expansion of {base}^{exp}.",
        f"When {base}^{exp} is written out, what do its digits add up to?",
        f"What is the digit sum of {base}^{exp}?",
    ]), ans, "digit_power_sum")

def build(per):
    for name,fn,_ in REGISTRY:
        made=0; guard=0
        while made<per and guard<per*120:
            guard+=1
            r=fn()
            if r is None: continue
            add(r[0],r[1],r[2]); made+=1

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--per",type=int,default=400)
    ap.add_argument("--sample",type=int,default=0)
    ap.add_argument("--out",default="/home/faisalnab25/data/skeleton_dataset_v6.json")
    ap.add_argument("--seed",type=int,default=42)
    args=ap.parse_args()
    random.seed(args.seed); build(args.per)
    print(f"Generated {len(PROBLEMS)} focused depth-0 problems across {len(REGISTRY)} concepts")
    covered=set()
    for _,_,amc in REGISTRY: covered.update(amc)
    print(f"AMC coverage (depth-0 engines): {len(covered)}/83 -> {sorted(covered)}")
    for t,c in sorted(Counter(p['skeleton_type'] for p in PROBLEMS).items()):
        print(f"  {t:24} {c}")
    if args.sample:
        for p in random.sample(PROBLEMS,min(args.sample,len(PROBLEMS))):
            print("\n["+p['skeleton_type']+"] ans="+p['answer']); print("  "+p['problem'][:140])
        return
    with open(args.out,"w") as f: json.dump(PROBLEMS,f,indent=2)
    print(f"Saved to {args.out}")

if __name__=="__main__": main()
