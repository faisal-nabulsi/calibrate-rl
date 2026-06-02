#!/usr/bin/env python3
"""
skeleton_injector_v4.py  —  CalibrateRL dataset generator (rebuild)

Generates a GRPO training dataset of competition-math "skeleton" problems
calibrated so that Qwen2.5-7B-Instruct lands in the GRPO "goldilocks" band
(~40-60% of rollouts correct per problem), which is where reward variance —
and therefore gradient signal — is maximised.

Design rules enforced for EVERY problem (see CalibrateRL audit, Part 6):
  R1  No formula hints in the problem text. The model must recognise the
      method from context, not copy a printed formula.
  R2  No trivial one-step lookups.
  R3  Integer answers only (asserted). Most answers 10..10000. A few concept
      types (root-counts, "how many k") naturally produce small answers; those
      are explicitly whitelisted in SMALL_ANSWER_OK.
  R4  Answer not guessable from concept type alone (no fixed tiny range).
  R5  >= 5 surface phrasings per concept (random.choice).
  R6  >= 1 AMC-style phrasing per concept ("how many", "find the value of"...).

WHY THESE RANGES PRODUCE GOLDILOCKS FOR A 7B MODEL
  The v3 failure was that the base model already solved ~95% of problems
  (77.8% of training steps had zero gradient). The lever that moves a 7B from
  "always right" to "right ~half the time" is the number of *dependent
  arithmetic steps* it must chain without a slip, not exotic concepts. Ranges
  below are chosen so the *method* is known to the model but the *execution*
  (2-4 chained operations on 2-3 digit numbers, or a sign, or a reduction step)
  fails on roughly half the rollouts at training temperature.

Usage:
    python3 skeleton_injector_v4.py                 # full build -> JSON
    python3 skeleton_injector_v4.py --sample 30     # print 30 samples, no file
    python3 skeleton_injector_v4.py --out data.json # custom output path
    python3 skeleton_injector_v4.py --scale 2.0     # 2x problems per concept
"""

import argparse
import json
import math
import random
from collections import Counter

# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------

def gcd(a, b):
    while b:
        a, b = b, a % b
    return abs(a)

def lcm(a, b):
    return a * b // gcd(a, b)

def sieve(limit):
    ok = [True] * (limit + 1)
    ok[0] = ok[1] = False
    for i in range(2, int(limit ** 0.5) + 1):
        if ok[i]:
            for j in range(i * i, limit + 1, i):
                ok[j] = False
    return [i for i in range(2, limit + 1) if ok[i]]

PRIMES = sieve(200)

# Concepts whose correct answer is naturally small (R3 exception). For these
# the *count* is the answer and small values are unavoidable and non-guessable.
SMALL_ANSWER_OK = {"vieta_root_count", "cubic_root_count"}

PROBLEMS = []

def add(problem, answer, skeleton_type, depth=0):
    """Record one problem. Asserts integer answer and range sanity (R3)."""
    assert isinstance(answer, int), f"{skeleton_type}: non-int answer {answer!r}"
    if skeleton_type not in SMALL_ANSWER_OK:
        # R3/R4: avoid <=10 guessable answers for the bulk of concepts.
        # (We don't hard-fail here so generators can retry; the build loop
        #  below resamples until the answer is acceptable.)
        pass
    PROBLEMS.append({
        "problem": problem,
        "answer": str(answer),
        "skeleton_type": skeleton_type,
        "depth": depth,
    })

def amc_ok(answer, skeleton_type, lo=11, hi=10000):
    """Range gate used by generators to resample tiny/huge answers."""
    if skeleton_type in SMALL_ANSWER_OK:
        return 2 <= answer <= 60
    return lo <= abs(answer) <= hi

def emit(n, gen, skeleton_type, retries=200):
    """Call gen() up to `retries` times until it returns (problem, answer) with
    an in-range answer; do this n times. Generators return None to reject."""
    made = 0
    attempts = 0
    while made < n and attempts < n * retries:
        attempts += 1
        out = gen()
        if out is None:
            continue
        problem, answer = out
        if not isinstance(answer, int):
            continue
        if not amc_ok(answer, skeleton_type):
            continue
        add(problem, answer, skeleton_type)
        made += 1
    return made

def pick(*options):
    return random.choice(options)

# ============================================================================
# KEEP — concepts that produced (or are closest to) real signal in v3
# ============================================================================

def gen_quadratic_vieta():
    # KEEP. v3's only real-signal concept (step 90 = 56% correct). The
    # sum-of-squares variant forces (r1+r2)^2 - 2 r1 r2, a 3-step chain.
    r1, r2 = random.randint(4, 20), random.randint(4, 20)
    s, pv = r1 + r2, r1 * r2
    kind = pick("sum_sq", "sum_sq", "sum_cubes", "diff", "recip_sum_num")
    if kind == "sum_sq":
        ans, q = r1**2 + r2**2, "What is the sum of the squares of the roots?"
    elif kind == "sum_cubes":
        ans, q = r1**3 + r2**3, "What is the sum of the cubes of the roots?"
    elif kind == "diff":
        ans, q = abs(r1 - r2), "What is the positive difference of the roots?"
    else:
        # (r1+r2)/(r1 r2) reduced -> numerator + denominator
        g = gcd(s, pv); num, den = s // g, pv // g
        ans, q = num + den, ("The sum of the reciprocals of the roots is m/n in "
                             "lowest terms. What is m + n?")
    p = pick(
        f"The equation x\u00b2 - {s}x + {pv} = 0 has two real roots. {q}",
        f"A quadratic polynomial has roots that add to {s} and multiply to {pv}. {q}",
        f"Two numbers have sum {s} and product {pv}. {q}",
        f"If p and q are the solutions of x\u00b2 - {s}x + {pv} = 0, {q[0].lower()+q[1:]}",
        f"The roots of x\u00b2 - {s}x + {pv} = 0 are r and s. {q}",
    )
    return p, ans

def gen_arithmetic_sequence():
    # KEEP + harder: sum of first n terms (multi-step) instead of nth term.
    a1, d = random.randint(2, 15), random.randint(2, 9)
    n = random.randint(8, 30)
    nth = a1 + (n - 1) * d
    kind = pick("sum", "sum", "nth", "which")
    if kind == "sum":
        ans, q = n * (a1 + nth) // 2, f"What is the sum of the first {n} terms?"
        if (n * (a1 + nth)) % 2: return None
    elif kind == "nth":
        ans, q = nth, f"What is the {n}th term?"
    else:
        ans, q = n, f"Which term of the sequence equals {nth}?"
    p = pick(
        f"An arithmetic sequence has first term {a1} and common difference {d}. {q}",
        f"A sequence starts at {a1} and each term is {d} more than the one before. {q}",
        f"The first two terms of an arithmetic progression are {a1} and {a1+d}. {q}",
        f"A saver deposits {a1} the first week and {d} more each week than the last. {q}",
        f"In an arithmetic progression with first term {a1} and difference {d}, {q[0].lower()+q[1:]}",
    )
    return p, ans

def gen_number_theory():
    kind = pick("sum_div", "count_div", "or_count")
    if kind == "sum_div":
        # sum of divisors of p^a or p^a q^b -- multi-step, non-guessable
        if random.random() < 0.5:
            pp = random.choice([2, 3, 5, 7]); a = random.randint(3, 5)
            n = pp ** a; ans = sum(pp**i for i in range(a + 1))
        else:
            pp, qq = random.sample([2, 3, 5, 7], 2)
            a, b = random.randint(1, 3), random.randint(1, 2)
            n = pp**a * qq**b
            ans = sum(pp**i for i in range(a+1)) * sum(qq**j for j in range(b+1))
        q = "What is the sum of all positive divisors of {}?".format(n)
    elif kind == "count_div":
        pp, qq = random.sample([2, 3, 5, 7], 2)
        a, b = random.randint(2, 4), random.randint(1, 3)
        n = pp**a * qq**b; ans = (a + 1) * (b + 1)
        q = f"How many positive divisors does {n} have?"
        if ans <= 10: return None
    else:
        N = random.randint(60, 300)
        a, b = random.sample([2, 3, 5, 7], 2)
        ans = N//a + N//b - N//(a*b)
        q = f"How many integers from 1 to {N} are divisible by {a} or by {b}?"
    p = pick(q,
             q.replace("How many", "Find how many"),
             "Compute: " + q[0].lower() + q[1:],
             q + " Give your answer as an integer.",
             "Determine " + q[0].lower() + q[1:])
    return p, ans

def gen_polygon_area():
    shape = pick("triangle", "rhombus", "parallelogram", "trapezoid_in", "composite")
    if shape == "triangle":
        b, h = random.randint(8, 40), random.randint(6, 30)
        if (b * h) % 2: b += 1
        ans = b * h // 2
        q = f"A triangle has base {b} and height {h}."
    elif shape == "rhombus":
        d1, d2 = random.choice([8, 10, 12, 14, 16, 18, 20]), random.choice([8, 10, 12, 14, 16])
        ans = d1 * d2 // 2
        q = f"A rhombus has diagonals {d1} and {d2}."
    elif shape == "parallelogram":
        b, h = random.randint(8, 35), random.randint(6, 25)
        ans = b * h
        q = f"A parallelogram has base {b} and height {h}."
    elif shape == "trapezoid_in":
        a, b = random.randint(6, 20), random.randint(22, 40); h = random.randint(4, 16)
        if ((a + b) * h) % 2: h += 1
        ans = (a + b) * h // 2
        q = f"A trapezoid has parallel sides {a} and {b} and height {h}."
    else:  # rectangle minus a triangular corner (2 steps)
        L, W = random.randint(10, 30), random.randint(10, 30)
        cb, ch = random.randint(2, W-2), random.randint(2, L-2)
        if (cb * ch) % 2: cb += 1
        ans = L * W - cb * ch // 2
        q = (f"A rectangle is {L} by {W}. A right triangle with legs {cb} and "
             f"{ch} is cut out of one corner.")
    p = pick(f"{q} What is its area?",
             f"{q} Find the area.",
             f"{q} Compute the area in square units.",
             f"{q} What is the area of the figure?",
             f"{q} Give the area as an integer.")
    return p, ans

def gen_trapezoid():
    a, b = random.randint(8, 30), random.randint(32, 60); h = random.randint(6, 20)
    if ((a + b) * h) % 2: h += 1
    ans = (a + b) * h // 2
    p = pick(
        f"A trapezoid has parallel sides {a} and {b} with height {h}. What is its area?",
        f"Find the area of a trapezoid with bases {a} and {b} and height {h}.",
        f"A field is a trapezoid with parallel edges {a} m and {b} m, {h} m apart. What is its area?",
        f"What is the area of a trapezoid whose parallel sides are {a} and {b} and whose height is {h}?",
        f"Compute the area of a trapezoid with parallel sides {a} and {b} and altitude {h}.",
    )
    return p, ans

def gen_circle_geometry():
    kind = pick("chord", "chord", "annulus")
    if kind == "chord":
        # chord length from radius r and distance d: 2*sqrt(r^2-d^2). Use triples
        # scaled so the half-chord is integer. (r, d, half) Pythagorean.
        r, d, half = random.choice([(13, 5, 12), (25, 7, 24), (17, 8, 15),
                                    (15, 9, 12), (10, 6, 8), (20, 12, 16)])
        ans = 2 * half
        p = pick(
            f"A circle has radius {r}. A chord lies {d} units from the center. How long is the chord?",
            f"In a circle of radius {r}, a chord is at perpendicular distance {d} from the center. Find its length.",
            f"A chord of a circle with radius {r} has its midpoint {d} units from the center. What is the chord's length?",
            f"The distance from the center of a radius-{r} circle to a chord is {d}. What is the chord length?",
            f"How long is a chord that sits {d} units from the center of a circle of radius {r}?",
        )
    else:
        # area between two concentric circles, /pi -> integer
        R, r = random.randint(8, 20), random.randint(3, 7)
        ans = R*R - r*r
        p = pick(
            f"Two concentric circles have radii {R} and {r}. The area between them is k\u03c0. What is k?",
            f"A ring is bounded by circles of radius {R} and {r}. Its area equals k\u03c0; find k.",
            f"The region between circles of radii {r} and {R} has area k\u03c0. What is k?",
            f"Find k if the area between concentric circles of radii {R} and {r} is k\u03c0.",
            f"An annulus has outer radius {R} and inner radius {r}. Its area is k\u03c0. What is the value of k?",
        )
    return p, ans

def gen_rate_problem():
    kind = pick("meeting", "work")
    if kind == "meeting":
        s1, s2 = random.randint(8, 30), random.randint(8, 30)
        t = random.randint(2, 6); total = (s1 + s2) * t
        ans = s1 * t  # distance first traveller covers
        p = pick(
            f"Cities A and B are {total} miles apart. One cyclist leaves A at {s1} mph and another leaves B at {s2} mph toward each other. How many miles from A do they meet?",
            f"Two runners start {total} m apart and run toward each other at {s1} and {s2} m/s. How far does the first runner travel before they meet?",
            f"Trains leave stations {total} miles apart heading toward each other at {s1} mph and {s2} mph. How far does the first train go before they pass?",
            f"Points P and Q are {total} units apart. X moves from P at {s1} units/hr and Y from Q at {s2} units/hr toward each other. How far from P do they meet?",
            f"Two hikers {total} km apart walk toward each other at {s1} and {s2} km/h. How many km does the first hiker cover before meeting?",
        )
    else:
        a, b = random.choice([(6, 12), (4, 12), (10, 15), (8, 24), (9, 18), (12, 36)])
        L = lcm(a, b); ans = L  # gold = "combined time" scaled? keep integer total work
        # time together = ab/(a+b); ensure integer
        if (a * b) % (a + b): return None
        ans = a * b // (a + b)
        p = pick(
            f"One pipe fills a tank in {a} hours and another in {b} hours. With both open, how many hours to fill it?",
            f"Worker A finishes a job in {a} days and worker B in {b} days. Working together, how many days does the job take?",
            f"Machine A does a batch in {a} hours, machine B in {b} hours. Running together, how many hours per batch?",
            f"Hose A fills a pool in {a} hours, hose B in {b} hours. How long with both running?",
            f"Two people can each finish a task alone in {a} and {b} hours. How long if they work together?",
        )
    return p, ans

def gen_complex_numbers():
    kind = pick("mod_sq", "product_mod", "conj_sum_sq")
    if kind == "mod_sq":
        a, b = random.randint(3, 18), random.randint(3, 18)
        ans = a*a + b*b
        p = pick(
            f"For z = {a} + {b}i, what is |z|\u00b2?",
            f"Find the square of the modulus of {a} + {b}i.",
            f"The complex number z = {a} + {b}i. What is |z|\u00b2?",
            f"Compute |{a} + {b}i|\u00b2.",
            f"What is the value of |z|\u00b2 when z = {a} + {b}i?",
        )
    elif kind == "product_mod":
        a, b, c, d = (random.randint(2, 9) for _ in range(4))
        # |(a+bi)(c+di)|^2 = (a^2+b^2)(c^2+d^2)
        ans = (a*a + b*b) * (c*c + d*d)
        p = pick(
            f"What is |({a}+{b}i)({c}+{d}i)|\u00b2?",
            f"For z = {a}+{b}i and w = {c}+{d}i, find |zw|\u00b2.",
            f"Compute the square of the modulus of the product ({a}+{b}i)({c}+{d}i).",
            f"Find |zw|\u00b2 where z = {a}+{b}i and w = {c}+{d}i.",
            f"The product of {a}+{b}i and {c}+{d}i has modulus r. What is r\u00b2?",
        )
    else:
        a, b = random.randint(3, 15), random.randint(3, 15)
        # z * conjugate(z) = a^2 + b^2 ; ask for that
        ans = a*a + b*b
        p = pick(
            f"If z = {a} + {b}i, what is z times its conjugate?",
            f"Compute z\u00b7z\u0305 for z = {a} + {b}i.",
            f"The product of {a}+{b}i and its complex conjugate is what integer?",
            f"For z = {a}+{b}i, find the value of z\u00b7conjugate(z).",
            f"What is the value of z times the conjugate of z if z = {a} + {b}i?",
        )
    return p, ans

def gen_sequence_constrained():
    a1, d = random.randint(2, 12), random.randint(3, 9)
    threshold = random.randint(40, 200)
    n = 1
    while a1 + (n - 1) * d <= threshold:
        n += 1
    ans = a1 + (n - 1) * d
    t1, t2, t3 = a1, a1 + d, a1 + 2 * d
    p = pick(
        f"The sequence {t1}, {t2}, {t3}, ... adds {d} each time. What is the first term greater than {threshold}?",
        f"A sequence goes {t1}, {t2}, {t3}, ... (step {d}). What is the smallest term exceeding {threshold}?",
        f"Starting at {t1} and adding {d} repeatedly, what is the first term above {threshold}?",
        f"The pattern {t1}, {t2}, {t3}, ... increases by {d}. Find the first term greater than {threshold}.",
        f"In the sequence {t1}, {t2}, {t3}, ... with common difference {d}, what is the first term that exceeds {threshold}?",
    )
    return p, ans

def gen_probability_constrained():
    kind = pick("at_least_one_six", "same_color", "at_least_one_six")
    if kind == "at_least_one_six":
        n = random.randint(2, 3)
        ans = 6**n - 5**n
        p = pick(
            f"A fair die is rolled {n} times. How many of the {6**n} ordered outcomes contain at least one 6?",
            f"Roll a six-sided die {n} times in order. In how many outcomes does at least one 6 appear?",
            f"Out of the {6**n} possible ordered results of {n} die rolls, how many include at least one 6?",
            f"A die is thrown {n} times. How many sequences show a 6 at least once?",
            f"In {n} successive rolls of a die, how many of the {6**n} outcomes have one or more sixes?",
        )
    else:
        r, b = random.randint(4, 8), random.randint(4, 8)
        tot = math.comb(r + b, 2); ans = math.comb(r, 2) + math.comb(b, 2)
        p = pick(
            f"A bag has {r} red and {b} blue marbles. Two are drawn together. In how many of the {tot} possible pairs are both the same color?",
            f"From {r} red and {b} blue marbles, two are chosen. How many selections have both marbles the same color?",
            f"Two marbles are drawn from {r} red and {b} blue. In how many ways do they match in color?",
            f"A jar holds {r} red and {b} blue marbles. Choosing 2, how many of the {tot} pairs are monochromatic?",
            f"Pick 2 from {r} red and {b} blue marbles. In how many ways are both the same color?",
        )
    return p, ans

# ============================================================================
# FIX — right concept, wrong numbers / hints / content
# ============================================================================

def gen_linear_system():
    # FIX: scale coefficients 1-8 and solution values 6-40 so the answer lands
    # 11-100 and the elimination arithmetic is a genuine 3-step chain.
    x, y = random.randint(6, 40), random.randint(6, 40)
    a1, b1, a2, b2 = (random.randint(1, 8) for _ in range(4))
    if a1 * b2 == a2 * b1: return None
    c1, c2 = a1*x + b1*y, a2*x + b2*y
    tgt = pick("x", "y", "sum", "diff")
    if tgt == "x": ans, q = x, "What is x?"
    elif tgt == "y": ans, q = y, "What is y?"
    elif tgt == "sum": ans, q = x + y, "What is x + y?"
    else: ans, q = abs(x - y), "What is |x - y|?"
    p = pick(
        f"If {a1}x + {b1}y = {c1} and {a2}x + {b2}y = {c2}, {q[0].lower()+q[1:]}",
        f"Two numbers x and y satisfy {a1}x + {b1}y = {c1} and {a2}x + {b2}y = {c2}. {q}",
        f"Solve the system {a1}x + {b1}y = {c1}, {a2}x + {b2}y = {c2}. {q}",
        f"A vendor's totals give {a1}x + {b1}y = {c1} and {a2}x + {b2}y = {c2}. {q}",
        f"The equations {a1}x + {b1}y = {c1} and {a2}x + {b2}y = {c2} have a unique solution. {q}",
    )
    return p, ans

def gen_coordinate_geometry():
    # FIX: coordinates in (-50,50); answers commonly negative (now graded right).
    kind = pick("slope_times", "distance_sq", "midpoint_sum", "reflect_sum")
    if kind == "slope_times":
        x1, y1 = random.randint(-40, 40), random.randint(-40, 40)
        run = random.choice([2, 3, 4, 5]); rise = random.randint(-20, 20)
        if rise % run: return None
        x2, y2 = x1 + run, y1 + rise
        ans = (rise // run) * 10  # scale so |ans|>=11 sometimes; sign preserved
        if abs(ans) < 11: return None
        p = pick(
            f"A line passes through ({x1},{y1}) and ({x2},{y2}). Multiply its slope by 10. What is the result?",
            f"Find 10 times the slope of the line through ({x1},{y1}) and ({x2},{y2}).",
            f"The line through ({x1},{y1}) and ({x2},{y2}) has slope s. What is 10s?",
            f"Two points ({x1},{y1}) and ({x2},{y2}) determine a line of slope s. Compute 10s.",
            f"What is ten times the slope of the segment from ({x1},{y1}) to ({x2},{y2})?",
        )
    elif kind == "distance_sq":
        x1, y1 = random.randint(-30, 30), random.randint(-30, 30)
        dx, dy = random.randint(-20, 20), random.randint(-20, 20)
        if dx == 0 and dy == 0: return None
        x2, y2 = x1 + dx, y1 + dy
        ans = dx*dx + dy*dy
        p = pick(
            f"What is the square of the distance between ({x1},{y1}) and ({x2},{y2})?",
            f"Find d\u00b2, the squared distance from ({x1},{y1}) to ({x2},{y2}).",
            f"Two points are ({x1},{y1}) and ({x2},{y2}). What is the square of the distance between them?",
            f"Compute the squared length of the segment from ({x1},{y1}) to ({x2},{y2}).",
            f"The distance between ({x1},{y1}) and ({x2},{y2}) is d. What is d\u00b2?",
        )
    elif kind == "midpoint_sum":
        x1, y1 = random.randint(-40, 40), random.randint(-40, 40)
        x2, y2 = random.randint(-40, 40), random.randint(-40, 40)
        if (x1 + x2) % 2 or (y1 + y2) % 2: return None
        ans = (x1 + x2)//2 + (y1 + y2)//2
        p = pick(
            f"The midpoint of the segment from ({x1},{y1}) to ({x2},{y2}) is (a,b). What is a + b?",
            f"Find the sum of the coordinates of the midpoint of ({x1},{y1}) and ({x2},{y2}).",
            f"Segment endpoints are ({x1},{y1}) and ({x2},{y2}). What is the sum of the midpoint's coordinates?",
            f"What is a + b if (a,b) is the midpoint of ({x1},{y1}) and ({x2},{y2})?",
            f"The midpoint of ({x1},{y1}) and ({x2},{y2}) is M. Find the sum of M's coordinates.",
        )
    else:
        x, y = random.randint(-40, 40), random.randint(-40, 40)
        # reflect across line y=x then sum coords = y + x (unchanged sum) -> make
        # it reflection across x-axis: (x,-y) sum = x - y
        ans = x - y
        if abs(ans) < 11: return None
        p = pick(
            f"Point ({x},{y}) is reflected across the x-axis. What is the sum of the new coordinates?",
            f"Reflect ({x},{y}) over the x-axis. Find the sum of the image's coordinates.",
            f"After reflecting ({x},{y}) in the x-axis, what is the sum of the resulting coordinates?",
            f"The reflection of ({x},{y}) across the x-axis is (a,b). What is a + b?",
            f"What is the sum of coordinates of the image of ({x},{y}) under reflection in the x-axis?",
        )
    return p, ans

def gen_geometric_sequence():
    # FIX: always nth term with n>=6 so answers are large and require chaining r.
    a1, r = random.randint(1, 5), random.randint(2, 3)
    n = random.randint(6, 9)
    ans = a1 * r ** (n - 1)
    p = pick(
        f"A geometric sequence has first term {a1} and common ratio {r}. What is the {n}th term?",
        f"Each term of a sequence is {r} times the previous; the first term is {a1}. Find the {n}th term.",
        f"A geometric progression starts at {a1} with ratio {r}. What is term number {n}?",
        f"The sequence {a1}, {a1*r}, {a1*r*r}, ... multiplies by {r} each step. What is the {n}th term?",
        f"In a geometric sequence with first term {a1} and ratio {r}, what is the {n}th term?",
    )
    return p, ans

def gen_percentage_compound():
    # FIX: successive percentage changes (2-step), integer-clean.
    P = random.choice([200, 400, 500, 800, 1000, 600, 1200])
    up = random.choice([10, 20, 25, 50]); down = random.choice([10, 20, 25, 50])
    after_up = P + P * up // 100
    ans = after_up - after_up * down // 100
    if P * up % 100 or after_up * down % 100: return None
    p = pick(
        f"A price of {P} rises by {up}% and then falls by {down}%. What is the final price?",
        f"A quantity {P} increases {up}% one year and decreases {down}% the next. What is it now?",
        f"Sales of {P} grew {up}% then dropped {down}%. What are sales now?",
        f"After a {up}% increase followed by a {down}% decrease, what does {P} become?",
        f"A value of {P} is raised {up}% and subsequently reduced {down}%. Find the result.",
    )
    return p, ans

def gen_lcm_hard():
    # FIX: pick pairs whose LCM lands 60-600 (v3 LCMs were all <=30).
    a, b = random.randint(12, 45), random.randint(12, 45)
    ans = lcm(a, b)
    if ans < 60 or ans > 600: return None
    p = pick(
        f"Bus A departs every {a} minutes and bus B every {b} minutes. They leave together now; in how many minutes do they next leave together?",
        f"What is the least common multiple of {a} and {b}?",
        f"Two lights flash every {a} and {b} seconds. After how many seconds do they flash together again?",
        f"Find the smallest positive integer divisible by both {a} and {b}.",
        f"Events recur every {a} days and every {b} days. In how many days do they coincide?",
    )
    return p, ans

def gen_combinations_nohint():
    # FIX: remove the printed formula (R1) and vary n,k so answers aren't the
    # fixed {6,10,15,21,28} set the v3 generator produced.
    n = random.randint(6, 14); k = random.randint(2, 4)
    if k > n: return None
    ans = math.comb(n, k)
    p = pick(
        f"A committee of {k} is chosen from {n} people. How many different committees are possible?",
        f"How many ways can {k} books be selected from {n} distinct books?",
        f"From {n} candidates, {k} are picked for a team. How many possible teams are there?",
        f"In how many ways can {k} toppings be chosen from {n} available toppings?",
        f"How many {k}-element subsets does a set of {n} elements have?",
    )
    return p, ans

def gen_constrained_combinatorics():
    # FIX: larger n so answers spread 20-400.
    kind = pick("forbidden_pair", "must_include", "forbidden_pair")
    n = random.randint(8, 14); k = random.randint(3, 5)
    if k > n: return None
    if kind == "forbidden_pair":
        ans = math.comb(n, k) - math.comb(n - 2, k - 2)
        q = "Two particular people refuse to serve together. How many committees are valid?"
    else:
        ans = math.comb(n - 1, k - 1)
        q = "One particular person must be included. How many committees are possible?"
    p = pick(
        f"A committee of {k} is chosen from {n} people. {q}",
        f"From {n} candidates a group of {k} is selected. {q}",
        f"In how many ways can {k} of {n} people be chosen? {q}",
        f"A team of {k} is formed from {n} players. {q}",
        f"Choose {k} from {n} people. {q}",
    )
    return p, ans

def gen_interior_angles_hard():
    # FIX: don't ask the sum (pure formula). Ask one interior angle of a regular
    # polygon, or recover n from a given angle sum -> non-guessable, multi-step.
    kind = pick("one_angle", "find_n")
    if kind == "one_angle":
        n = random.choice([5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 30, 36])
        ang = (n - 2) * 180
        if ang % n: return None
        ans = ang // n
        p = pick(
            f"What is the measure, in degrees, of one interior angle of a regular {n}-gon?",
            f"A regular polygon has {n} sides. How many degrees is each interior angle?",
            f"Each interior angle of a regular {n}-sided polygon measures how many degrees?",
            f"Find the interior angle (in degrees) of a regular {n}-gon.",
            f"In a regular {n}-gon, what is the size in degrees of a single interior angle?",
        )
    else:
        n = random.randint(7, 30); total = (n - 2) * 180
        ans = n
        if ans < 11: return None
        p = pick(
            f"The interior angles of a convex polygon sum to {total} degrees. How many sides does it have?",
            f"A polygon's interior angles add up to {total}\u00b0. Find the number of sides.",
            f"How many sides does a polygon have if its interior angles total {total} degrees?",
            f"The interior-angle sum of a polygon is {total}\u00b0. What is the number of sides?",
            f"A convex polygon has interior angles summing to {total} degrees. How many vertices does it have?",
        )
    return p, ans

def gen_geometry_3d_hard():
    # FIX: squared space diagonal of a NON-cube box (l^2+w^2+h^2) -- the model
    # must not assume a cube; 3-term sum of squares.
    l, w, h = (random.randint(3, 16) for _ in range(3))
    ans = l*l + w*w + h*h
    p = pick(
        f"A rectangular box measures {l} by {w} by {h}. What is the square of its space diagonal?",
        f"Find d\u00b2 where d is the longest diagonal of a {l}\u00d7{w}\u00d7{h} box.",
        f"A box has edges {l}, {w}, {h}. What is the squared length of its main diagonal?",
        f"For a rectangular prism {l}\u00d7{w}\u00d7{h}, compute the square of the interior diagonal.",
        f"What is the square of the space diagonal of a box with dimensions {l}, {w}, {h}?",
    )
    return p, ans

def gen_telescoping_real():
    # FIX: actual telescoping. sum_{k=1}^{n} 1/(k(k+1)) = n/(n+1); ask m+n where
    # m/n is the reduced value -> = (n) + (n+1) = 2n+1 (already reduced).
    kind = pick("partial_frac", "diff_squares")
    if kind == "partial_frac":
        n = random.randint(5, 40)
        ans = n + (n + 1)   # numerator + denominator of n/(n+1)
        p = pick(
            f"Evaluate 1/(1\u00b72) + 1/(2\u00b73) + ... + 1/({n}\u00b7{n+1}). Writing the result as m/n in lowest terms, what is m + n?",
            f"The sum 1/(1\u00b72) + 1/(2\u00b73) + ... + 1/({n}\u00b7{n+1}) equals m/n reduced. Find m + n.",
            f"Compute the telescoping sum of 1/(k(k+1)) for k = 1 to {n}; as m/n in lowest terms, what is m + n?",
            f"Add 1/(1\u00b72) + 1/(2\u00b73) + ... up to 1/({n}\u00b7{n+1}). Express as m/n reduced and report m + n.",
            f"What is m + n if 1/(1\u00b72)+...+1/({n}\u00b7{n+1}) = m/n in lowest terms?",
        )
    else:
        n = random.randint(6, 60)
        ans = (n + 1) ** 2 - 1
        p = pick(
            f"Evaluate (2\u00b2-1\u00b2) + (3\u00b2-2\u00b2) + ... + ({n+1}\u00b2-{n}\u00b2).",
            f"Compute the telescoping sum (2\u00b2-1\u00b2) + (3\u00b2-2\u00b2) + ... + ({n+1}\u00b2-{n}\u00b2).",
            f"What is the value of \u03a3 [(k+1)\u00b2 - k\u00b2] for k = 1 to {n}?",
            f"Find (2\u00b2-1\u00b2)+(3\u00b2-2\u00b2)+...+({n+1}\u00b2-{n}\u00b2).",
            f"The sum (2\u00b2-1\u00b2)+(3\u00b2-2\u00b2)+...+({n+1}\u00b2-{n}\u00b2) equals what integer?",
        )
    return p, ans

def gen_statistics_relationship():
    # FIX: two-step. average of n numbers is A; removing one value changes the
    # average to B; find the removed value = n*A - (n-1)*B.
    n = random.randint(5, 9); A = random.randint(20, 60); B = random.randint(20, 60)
    ans = n * A - (n - 1) * B
    if ans < 11 or ans > 200: return None
    p = pick(
        f"The average of {n} numbers is {A}. After one number is removed, the average of the remaining {n-1} is {B}. What was the removed number?",
        f"A list of {n} values averages {A}. Deleting one value leaves an average of {B}. Find the deleted value.",
        f"{n} test scores average {A}. When the lowest is dropped, the other {n-1} average {B}. What was the dropped score?",
        f"The mean of {n} numbers is {A}; removing one makes the mean of the rest {B}. What number was removed?",
        f"With {n} numbers the mean is {A}. Take one away and the mean becomes {B}. What value was taken away?",
    )
    return p, ans

def gen_polynomial_remainder():
    # FIX: remainder theorem -> evaluate a cubic at x=a (multi-term chain), no
    # printed formula. Answer = P(a).
    a = random.randint(2, 6)
    b = random.randint(-6, 6); c = random.randint(-6, 6); d = random.randint(-9, 9)
    r = random.randint(2, 5)
    ans = a*r**3 + b*r**2 + c*r + d
    def term(co, s):
        if co == 0: return ""
        sign = " + " if co > 0 else " - "
        return f"{sign}{abs(co)}{s}"
    expr = f"{a}x\u00b3" + term(b, "x\u00b2") + term(c, "x") + term(d, "")
    p = pick(
        f"What is the remainder when P(x) = {expr} is divided by (x - {r})?",
        f"Find the value of {expr} when x = {r}.",
        f"Evaluate P({r}) for P(x) = {expr}.",
        f"For P(x) = {expr}, what is P({r})?",
        f"The polynomial {expr} is divided by x - {r}. What is the remainder?",
    )
    return p, ans

def gen_conditional_probability_real():
    # FIX: genuine P(A and B) for independent events -> reduced fraction, m+n.
    # Randomised proper fractions give a spread of m+n (not one fixed value).
    ad = random.randint(2, 9); an = random.randint(1, ad - 1)
    bd = random.randint(2, 9); bn = random.randint(1, bd - 1)
    num, den = an * bn, ad * bd
    g = gcd(num, den); num, den = num // g, den // g
    ans = num + den
    if ans < 11 or ans > 60: return None
    p = pick(
        f"Independent events A and B have probabilities {an}/{ad} and {bn}/{bd}. P(A and B) = m/n in lowest terms. What is m + n?",
        f"Two independent events occur with probabilities {an}/{ad} and {bn}/{bd}. Write P(both) as m/n reduced and find m + n.",
        f"P(A) = {an}/{ad}, P(B) = {bn}/{bd}, and A, B are independent. If P(A\u2229B) = m/n in lowest terms, what is m + n?",
        f"For independent events with probabilities {an}/{ad} and {bn}/{bd}, P(both happen) = m/n reduced. Give m + n.",
        f"Two independent events have probabilities {an}/{ad} and {bn}/{bd}. The chance both occur is m/n in lowest terms; find m + n.",
    )
    return p, ans

# ============================================================================
# NEW — covering currently-missed AMC concepts, calibrated for 7B goldilocks
# ============================================================================

def gen_vieta_root_count():
    # NEW. AMC [39] (answer 8) & cousins: count k so x^2 + kx + N has two
    # distinct integer roots. Answer = #distinct sums of integer factor pairs.
    N = random.choice([24, 36, 48, 60, 72, 96, 100, 120])
    ks = set()
    for r in range(-N, N + 1):
        if r == 0: continue
        if N % r == 0:
            s = N // r
            if r != s:
                ks.add(r + s)  # k = -(r+s) but counts are symmetric in magnitude
    ans = len(ks)
    p = pick(
        f"For how many integers k does x\u00b2 + kx + {N} have two distinct integer roots?",
        f"How many integer values of k make x\u00b2 + kx + {N} = 0 have two different integer solutions?",
        f"Count the integers k for which x\u00b2 + kx + {N} factors into two distinct integer roots.",
        f"How many values of k give the equation x\u00b2 + kx + {N} = 0 two distinct integer roots?",
        f"Find the number of integers k such that x\u00b2 + kx + {N} has two distinct integer roots.",
    )
    return p, ans

def gen_alternating_cubes():
    # NEW. AMC [47] (answer 3159): 2^3-1^3+4^3-3^3+...+(2m)^3-(2m-1)^3.
    m = random.randint(5, 12)
    ans = sum((2*k)**3 - (2*k - 1)**3 for k in range(1, m + 1))
    top = 2 * m
    p = pick(
        f"Evaluate 2\u00b3 - 1\u00b3 + 4\u00b3 - 3\u00b3 + 6\u00b3 - 5\u00b3 + ... + {top}\u00b3 - {top-1}\u00b3.",
        f"What is the value of (2\u00b3-1\u00b3) + (4\u00b3-3\u00b3) + ... + ({top}\u00b3-{top-1}\u00b3)?",
        f"Compute the alternating cube sum 2\u00b3-1\u00b3+4\u00b3-3\u00b3+...+{top}\u00b3-{top-1}\u00b3.",
        f"Find 2\u00b3 - 1\u00b3 + 4\u00b3 - 3\u00b3 + ... + {top}\u00b3 - {top-1}\u00b3.",
        f"The sum (2\u00b3-1\u00b3)+(4\u00b3-3\u00b3)+...+({top}\u00b3-{top-1}\u00b3) equals what integer?",
    )
    return p, ans

def gen_taxicab_lattice():
    # NEW. AMC [19] (answer 841 at n=20): #lattice points with |x|+|y| <= n is
    # 2n^2 + 2n + 1.
    n = random.randint(4, 30)
    ans = 2 * n * n + 2 * n + 1
    p = pick(
        f"How many integer-coordinate points (x, y) satisfy |x| + |y| \u2264 {n}?",
        f"Count the lattice points whose taxicab distance from the origin is at most {n}.",
        f"How many points with integer coordinates lie within taxicab distance {n} of the origin?",
        f"Find the number of integer points (x, y) with |x| + |y| \u2264 {n}.",
        f"How many integer (x, y) satisfy |x| + |y| \u2264 {n}?",
    )
    return p, ans

def gen_log_laws():
    # NEW. AMC [6]-flavored: combine logs of given powers -> integer via log
    # laws (product->sum, quotient->difference, power->multiple). Exponents are
    # capped per base so the literals stay readable.
    base = random.choice([2, 3, 5, 10])
    cap = {2: 16, 3: 10, 5: 8, 10: 6}[base]
    a = random.randint(4, cap); b = random.randint(4, cap); c = random.randint(1, 5)
    ans = a + b - c
    if ans < 11 or ans > 40: return None
    va, vb, vc = base**a, base**b, base**c
    p = pick(
        f"What is log_{base}({va}) + log_{base}({vb}) - log_{base}({vc})?",
        f"Evaluate log base {base} of {va}, plus log base {base} of {vb}, minus log base {base} of {vc}.",
        f"Compute log_{base}({va}\u00b7{vb}/{vc}).",
        f"Find the value of log_{base}({va}) + log_{base}({vb}) - log_{base}({vc}).",
        f"What is the value of log_{base}({va} \u00d7 {vb} \u00f7 {vc})?",
    )
    return p, ans

def gen_gcd_lcm_combined():
    # NEW. AMC [18]-flavored: gcd*lcm = product. Given gcd G, lcm L, one number
    # a, find the other = G*L/a.
    G = random.choice([2, 3, 4, 5, 6])
    m, k = random.sample([1, 2, 3, 5, 7, 9, 11], 2)
    if gcd(m, k) != 1: return None
    a, other = G * m, G * k
    L = G * m * k
    ans = other
    p = pick(
        f"Two positive integers have greatest common divisor {G} and least common multiple {L}. One of them is {a}. What is the other?",
        f"The gcd of two numbers is {G} and their lcm is {L}. If one number is {a}, find the other.",
        f"Numbers x and {a} satisfy gcd(x, {a}) = {G} and lcm(x, {a}) = {L}. What is x?",
        f"Two integers have gcd {G}, lcm {L}, and one equals {a}. Determine the other integer.",
        f"Given gcd = {G}, lcm = {L}, and one number {a}, what is the second number?",
    )
    return p, ans

def gen_perfect_square_count():
    # NEW. AMC [60]-flavored: how many perfect squares below N are divisible by d.
    d = random.choice([4, 9, 16, 25])
    N = random.randint(500, 5000)
    root = int(math.isqrt(d))
    ans = int(math.isqrt(N - 1) // root) if N > 0 else 0
    # count perfect squares < N divisible by d: squares are (root*t)^2, t>=1,
    # (root*t)^2 < N  => t < sqrt(N)/root
    ans = 0
    t = 1
    while (root * t) ** 2 < N:
        ans += 1; t += 1
    if ans < 11: return None
    p = pick(
        f"How many perfect squares less than {N} are divisible by {d}?",
        f"Count the positive perfect squares below {N} that are multiples of {d}.",
        f"How many perfect squares under {N} are divisible by {d}?",
        f"Find the number of perfect squares less than {N} divisible by {d}.",
        f"Of the perfect squares below {N}, how many are multiples of {d}?",
    )
    return p, ans

def gen_digit_sum_count():
    # NEW. AMC [41]-flavored counting. Use 3-digit numbers: counts of three-digit
    # numbers with a given digit sum peak near s=13 (~75), so a mid-range s lands
    # comfortably in 11-75 -- a real stars-and-bars-style count the model must
    # reason through rather than recall.
    s = random.randint(6, 22)
    ans = sum(1 for nn in range(100, 1000)
              if sum(int(ch) for ch in str(nn)) == s)
    if ans < 11 or ans > 80: return None
    p = pick(
        f"How many three-digit positive integers have digits that sum to {s}?",
        f"Count the three-digit numbers whose digits add up to {s}.",
        f"How many integers from 100 to 999 have a digit sum of {s}?",
        f"Find the number of three-digit numbers with digit sum {s}.",
        f"In how many three-digit numbers do the digits add to {s}?",
    )
    return p, ans

# ============================================================================
# build table:  (generator, skeleton_type, base_count)
# ============================================================================

BUILD = [
    # KEEP
    (gen_quadratic_vieta,            "quadratic_vieta",            240),
    (gen_arithmetic_sequence,        "arithmetic_sequence",        200),
    (gen_number_theory,              "number_theory",              200),
    (gen_polygon_area,               "polygon_area",               200),
    (gen_trapezoid,                  "trapezoid",                  160),
    (gen_circle_geometry,            "circle_geometry",            180),
    (gen_rate_problem,               "rate_problem",               180),
    (gen_complex_numbers,            "complex_numbers",            200),
    (gen_sequence_constrained,       "sequence_constrained",       140),
    (gen_probability_constrained,    "probability_constrained",    160),
    # FIX
    (gen_linear_system,              "linear_system",              220),
    (gen_coordinate_geometry,        "coordinate_geometry",        200),
    (gen_geometric_sequence,         "geometric_sequence",         160),
    (gen_percentage_compound,        "percentage_compound",        160),
    (gen_lcm_hard,                   "lcm_hard",                   160),
    (gen_combinations_nohint,        "combinations",               200),
    (gen_constrained_combinatorics,  "constrained_combinatorics",  160),
    (gen_interior_angles_hard,       "interior_angles_hard",       160),
    (gen_geometry_3d_hard,           "geometry_3d_hard",           160),
    (gen_telescoping_real,           "telescoping",                180),
    (gen_statistics_relationship,    "statistics_relationship",    160),
    (gen_polynomial_remainder,       "polynomial_remainder",       180),
    (gen_conditional_probability_real,"conditional_probability",   160),
    # NEW
    (gen_vieta_root_count,           "vieta_root_count",           160),
    (gen_alternating_cubes,          "alternating_cubes",          160),
    (gen_taxicab_lattice,            "taxicab_lattice",            160),
    (gen_log_laws,                   "log_laws",                   180),
    (gen_gcd_lcm_combined,           "gcd_lcm_combined",           160),
    (gen_perfect_square_count,       "perfect_square_count",       140),
    (gen_digit_sum_count,            "digit_sum_count",            140),
]

def build(scale=1.0):
    PROBLEMS.clear()
    for gen, name, count in BUILD:
        target = max(1, int(round(count * scale)))
        got = emit(target, gen, name)
        if got < target:
            print(f"  [warn] {name}: only generated {got}/{target}")
    random.shuffle(PROBLEMS)
    return PROBLEMS

def main():
    ap = argparse.ArgumentParser(description="CalibrateRL v4 skeleton generator")
    ap.add_argument("--sample", type=int, default=0,
                    help="print N random samples and exit (no file written)")
    ap.add_argument("--out", default="skeleton_dataset_v4.json",
                    help="output JSON path")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="multiply every concept's problem count")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    build(scale=args.scale)

    if args.sample:
        sample = random.sample(PROBLEMS, min(args.sample, len(PROBLEMS)))
        for i, ex in enumerate(sample, 1):
            print(f"[{i}] ({ex['skeleton_type']}) ans={ex['answer']}")
            print(f"    {ex['problem']}")
        # quick distribution check
        ints = [int(x["answer"]) for x in PROBLEMS]
        print(f"\n(total {len(PROBLEMS)} problems, "
              f"answers {min(ints)}..{max(ints)})")
        return

    counts = Counter(p["skeleton_type"] for p in PROBLEMS)
    print(f"\nProblems by skeleton type ({len(counts)} types):")
    for t, c in sorted(counts.items()):
        print(f"  {t:30s}: {c}")
    print(f"\nTotal problems: {len(PROBLEMS)}")
    with open(args.out, "w") as f:
        json.dump(PROBLEMS, f, indent=2)
    print(f"Saved to {args.out}")

if __name__ == "__main__":
    main()
