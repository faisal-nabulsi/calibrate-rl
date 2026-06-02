#!/usr/bin/env python3
"""
chain_skeletons_v4.py — CalibrateRL depth-1 chains: HARD ANCHOR + SATURATED PARTNER

CURRICULUM DESIGN (the real one):
  depth-0  -> train on the 8 hard survivor concepts (the difficulty engines).
  depth-1  -> train on HARD-ANCHOR + SATURATED-PARTNER chains:
                * the hard survivor (step 1) supplies the difficulty,
                * a SATURATED concept (step 2) rides along -> brings back the broad
                  AMC concept coverage that depth-0 had to drop (combinations,
                  geometry, logs, inclusion-exclusion, etc.).
  This is how coverage returns at depth-1 without sacrificing difficulty: the
  anchor keeps it hard, the partner adds breadth.

  Contrast with the failed v3 chains (saturated o saturated = stayed easy) and
  with a hard o hard design (max difficulty but zero coverage). Hard o saturated
  is the sweet spot: difficulty from the anchor, coverage from the partner.

  embed-not-announce; integer-safe; final answer from the partner op so the
  saturated concept is genuinely exercised.
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

PROBLEMS=[]
def add(problem, answer, ct, amc):
    assert isinstance(answer,int), f"{ct}: non-int {answer!r}"
    PROBLEMS.append({"problem":problem,"answer":str(answer),"skeleton_type":ct,
                     "chain_type":ct,"depth":1,"amc_targets":amc})

# hard anchor: smallest n solving lcm/gcd system (the lcm_gcd_system survivor)
def anchor_lcmgcd():
    p=random.choice([12,18,24,36]); q=random.choice([15,30,45])
    n=random.randint(12,120); L=lcm(n,p); G=gcd(n,q)
    cand=[m for m in range(1,L+1) if lcm(m,p)==L and gcd(m,q)==G]
    if not cand: return None
    return min(cand), f"the smallest positive integer n with lcm(n,{p})={L} and gcd(n,{q})={G}"

# hard anchor: alternating cube sum (alternating_cubes survivor)
def anchor_altcubes():
    top=random.choice([10,12,14,16,18])
    S=sum((2*k)**3-(2*k-1)**3 for k in range(1,top//2+1))
    return S, f"the value of 2³-1³+4³-3³+...+{top}³-{top-1}³"

# hard anchor: modular exponent (modular_exponent survivor)
def anchor_modexp():
    a=random.randint(2,7); e=random.randint(6,12); m=random.randint(50,150)
    return pow(a,e,m), f"the remainder when {a}^{e} is divided by {m}"

# ── CHAINS: anchor -> SATURATED partner (partner = the covered concept) ──

# anchor -> COMBINATIONS (covers AMC combinatorics)
def gen_anchor_into_combinations():
    a=random.choice([anchor_lcmgcd, anchor_altcubes, anchor_modexp])()
    if a is None: return None
    val, desc = a
    k=random.choice([2,3])
    n=val % 15 + 6   # map anchor result into a sensible n for C(n,k)
    if n<=k: return None
    ans=math.comb(n,k)
    if ans<6: return None
    phr=random.choice([
        f"Let v be {desc}. How many ways are there to choose {k} items from (v mod 15)+6 objects?",
        f"v is {desc}. Compute the number of {k}-element subsets of a set of size (v mod 15)+6.",
    ])
    return phr, ans, "anchor_into_combinations", [40,81]

# anchor -> TRAPEZOID AREA (covers geometry)
def gen_anchor_into_trapezoid():
    a=random.choice([anchor_lcmgcd, anchor_modexp])()
    if a is None: return None
    val, desc = a
    b1=val % 20 + 8; b2=random.randint(8,30); h=random.randint(2,10)
    if (b1+b2)*h % 2: h+=1
    ans=(b1+b2)*h//2
    phr=random.choice([
        f"Let v be {desc}. A trapezoid has parallel sides (v mod 20)+8 and {b2}, with height {h}. What is its area?",
        f"v is {desc}. Find the area of a trapezoid with bases (v mod 20)+8 and {b2} and height {h}.",
    ])
    return phr, ans, "anchor_into_trapezoid", [67]

# anchor -> INCLUSION-EXCLUSION count (covers number theory counting)
def gen_anchor_into_inclexcl():
    a=random.choice([anchor_lcmgcd, anchor_altcubes, anchor_modexp])()
    if a is None: return None
    val, desc = a
    upper=val % 400 + 200; x=random.choice([3,4,6]); y=random.choice([5,7,8])
    while gcd(x,y)!=1: y=random.choice([5,7,8,11])
    ans=upper//x+upper//y-upper//(x*y)
    if ans<8: return None
    phr=random.choice([
        f"Let v be {desc}. How many integers from 1 to (v mod 400)+200 are divisible by {x} or {y}?",
        f"v is {desc}. Among 1..(v mod 400)+200, how many are divisible by {x} or by {y}?",
    ])
    return phr, ans, "anchor_into_inclexcl", [40]

# anchor -> DIVISOR COUNT (covers number theory)
def gen_anchor_into_divisors():
    a=random.choice([anchor_altcubes, anchor_modexp])()
    if a is None: return None
    val, desc = a
    base=val % 200 + 12
    ans=ndiv(base)
    if ans<4: return None
    phr=random.choice([
        f"Let v be {desc}. How many positive divisors does (v mod 200)+12 have?",
        f"v is {desc}. Find the number of positive divisors of (v mod 200)+12.",
    ])
    return phr, ans, "anchor_into_divisors", [55,75]

# anchor -> SUM OF SQUARES (covers sequences)
def gen_anchor_into_sumsquares():
    a=random.choice([anchor_lcmgcd, anchor_modexp])()
    if a is None: return None
    val, desc = a
    n=val % 20 + 8
    ans=n*(n+1)*(2*n+1)//6
    phr=random.choice([
        f"Let v be {desc}. Compute 1²+2²+...+((v mod 20)+8)².",
        f"v is {desc}. What is the sum of the squares of the first (v mod 20)+8 positive integers?",
    ])
    return phr, ans, "anchor_into_sumsquares", [7,53]

CHAINS=[
    ("anchor_into_combinations", gen_anchor_into_combinations),
    ("anchor_into_trapezoid",    gen_anchor_into_trapezoid),
    ("anchor_into_inclexcl",     gen_anchor_into_inclexcl),
    ("anchor_into_divisors",     gen_anchor_into_divisors),
    ("anchor_into_sumsquares",   gen_anchor_into_sumsquares),
]

def build(per):
    for name,fn in CHAINS:
        made=0; guard=0
        while made<per and guard<per*120:
            guard+=1
            r=fn()
            if r is None: continue
            add(r[0],r[1],r[2],r[3]); made+=1

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--per",type=int,default=100)
    ap.add_argument("--sample",type=int,default=0)
    ap.add_argument("--out",default="/home/faisalnab25/data/depth1_dataset_v4.json")
    ap.add_argument("--seed",type=int,default=42)
    args=ap.parse_args()
    random.seed(args.seed); build(args.per)
    print(f"Generated {len(PROBLEMS)} depth-1 problems across {len(CHAINS)} chain types")
    cov=set()
    for p in PROBLEMS: cov.update(p['amc_targets'])
    print(f"depth-1 partner coverage adds AMC: {sorted(cov)}")
    for t,c in sorted(Counter(p['chain_type'] for p in PROBLEMS).items()):
        print(f"  {t:28} {c}")
    if args.sample:
        for p in random.sample(PROBLEMS,min(args.sample,len(PROBLEMS))):
            print("\n["+p['chain_type']+"] ans="+p['answer']); print("  "+p['problem'][:160])
        return
    with open(args.out,"w") as f: json.dump(PROBLEMS,f,indent=2)
    print(f"Saved to {args.out}")

if __name__=="__main__": main()
