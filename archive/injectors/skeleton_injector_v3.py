import random
import json
import math
from collections import Counter

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    return a * b // gcd(a, b)

def sieve(limit):
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, limit+1, i):
                is_prime[j] = False
    return [i for i in range(2, limit+1) if is_prime[i]]

PRIMES = sieve(50)
TRIPLES = [(3,4,5),(6,8,10),(3,4,5),(6,8,10),(3,4,5)]  # restrict to reliable triples
CYCLES = {2:[2,4,8,6],3:[3,9,7,1],4:[4,6],5:[5],6:[6],7:[7,9,3,1],8:[8,4,2,6],9:[9,1]}

all_problems = []

def add(problem, answer, skeleton_type):
    assert isinstance(answer, int), f"Non-int answer in {skeleton_type}: {answer} ({type(answer)})"
    all_problems.append({
        "problem": problem,
        "answer": str(answer),
        "skeleton_type": skeleton_type,
        "depth": 0
    })

N = 200

# ══════════════════════════════════════════════════════════════
# TIER 1
# ══════════════════════════════════════════════════════════════

# ── 1. LINEAR SYSTEMS ─────────────────────────────────────────
for _ in range(N):
    x = random.randint(2, 10)
    y = random.randint(2, 10)
    a1 = random.randint(1, 4)
    b1 = random.randint(1, 4)
    a2 = random.randint(1, 4)
    b2 = random.randint(1, 4)
    while a1*b2 == a2*b1:
        a2, b2 = random.randint(1, 4), random.randint(1, 4)
    c1 = a1*x + b1*y
    c2 = a2*x + b2*y
    target = random.choice(["x","y","sum","diff","product"])
    if target == "x": answer, q = x, "What is the value of x?"
    elif target == "y": answer, q = y, "What is the value of y?"
    elif target == "sum": answer, q = x+y, "What is x + y?"
    elif target == "diff": answer, q = abs(x-y), "What is |x - y|?"
    else: answer, q = x*y, "What is xy?"
    phrasing = random.randint(1, 5)
    if phrasing == 1:
        p = f"If {a1}x + {b1}y = {c1} and {a2}x + {b2}y = {c2}, {q}"
    elif phrasing == 2:
        p = f"Two numbers x and y satisfy {a1}x + {b1}y = {c1} and {a2}x + {b2}y = {c2}. {q}"
    elif phrasing == 3:
        p = f"Solve the system {a1}x + {b1}y = {c1} and {a2}x + {b2}y = {c2}. {q}"
    elif phrasing == 4:
        p = f"A store sells apples for ${a1} and oranges for ${b1}. A customer buys x apples and y oranges for ${c1}. Another buys {a2} times as many apples and {b2} times as many oranges for ${c2}. {q}"
    else:
        p = f"The equations {a1}x + {b1}y = {c1} and {a2}x + {b2}y = {c2} have a unique solution. {q}"
    add(p, answer, "linear_system")

# ── 1b. LINEAR SYSTEMS CONSTRAINED ────────────────────────────
for _ in range(N//2):
    x = random.randint(1, 8)
    y = random.randint(x+1, 10)
    a1 = random.randint(1, 3)
    b1 = random.randint(1, 3)
    c1 = a1*x + b1*y
    target = random.choice(["x","y","sum"])
    if target == "x": answer, q = x, "What is the value of x?"
    elif target == "y": answer, q = y, "What is the value of y?"
    else: answer, q = x+y, "What is x + y?"
    phrasing = random.randint(1, 5)
    if phrasing == 1:
        p = f"Positive integers x and y satisfy {a1}x + {b1}y = {c1} with x < y. {q}"
    elif phrasing == 2:
        p = f"Two positive integers x and y satisfy {a1}x + {b1}y = {c1} and x + y = {x+y}. {q}"
    elif phrasing == 3:
        p = f"A store sells x items at ${a1} and y items at ${b1} for a total of ${c1}. If x < y and both are positive integers, {q}"
    elif phrasing == 4:
        p = f"Positive integers x and y satisfy {a1}x + {b1}y = {c1} and x · y = {x*y}. {q}"
    else:
        p = f"Two positive whole numbers satisfy {a1}x + {b1}y = {c1} where x is the smaller. {q}"
    add(p, answer, "linear_system_constrained")

# ── 2. QUADRATIC / VIETA'S ────────────────────────────────────
for _ in range(N):
    r1 = random.randint(3, 12)
    r2 = random.randint(3, 12)
    s = r1 + r2
    pv = r1 * r2
    target = random.choice(["sum","product","sum_sq","diff","b_plus_c"])
    if target == "sum": answer, q = s, "What is the sum of the roots?"
    elif target == "product": answer, q = pv, "What is the product of the roots?"
    elif target == "sum_sq": answer, q = r1**2+r2**2, "What is the sum of the squares of the roots?"
    elif target == "diff": answer, q = abs(r1-r2), "What is the positive difference between the roots?"
    else: answer, q = -s+pv, "For the quadratic written as x² + bx + c, what is b + c?"
    phrasing = random.randint(1, 5)
    if phrasing == 1:
        p = f"The equation x² - {s}x + {pv} = 0 has two real roots. {q}"
    elif phrasing == 2:
        p = f"A quadratic polynomial has roots {r1} and {r2}. {q}"
    elif phrasing == 3:
        p = f"Two numbers multiply to {pv} and add to {s}. {q}"
    elif phrasing == 4:
        p = f"The roots of x² - {s}x + {pv} are the dimensions of a rectangle. {q}"
    else:
        p = f"If p and q are solutions to x² - {s}x + {pv} = 0, {q.lower()}"
    add(p, answer, "quadratic_vieta")

# ── 2b. QUADRATIC CONSTRAINED (roots must be prime or distinct) ─
for _ in range(N//2):
    constraint = random.choice(["both_prime","distinct_positive","one_double"])
    if constraint == "both_prime":
        p1 = random.choice(PRIMES[:8])
        p2 = random.choice(PRIMES[:8])
        s = p1 + p2
        pv = p1 * p2
        target = random.choice(["sum","product","diff"])
        if target == "sum": answer, q = s, "What is the sum of the roots?"
        elif target == "product": answer, q = pv, "What is the product of the roots?"
        else: answer, q = abs(p1-p2), "What is the positive difference between the roots?"
        phrasing = random.randint(1, 5)
        if phrasing == 1:
            p = f"The quadratic x² - {s}x + {pv} = 0 has two prime roots. {q}"
        elif phrasing == 2:
            p = f"Both roots of x² - {s}x + {pv} are prime numbers. {q}"
        elif phrasing == 3:
            p = f"A quadratic has two prime roots that sum to {s} and multiply to {pv}. {q}"
        elif phrasing == 4:
            p = f"Two prime numbers satisfy p + q = {s} and p · q = {pv}. {q}"
        else:
            p = f"Find two primes whose sum is {s} and product is {pv}. {q}"
        add(p, answer, "quadratic_constrained")
    elif constraint == "distinct_positive":
        r1 = random.randint(1, 6)
        r2 = random.randint(r1+1, 9)
        s = r1 + r2
        pv = r1 * r2
        answer = r2
        phrasing = random.randint(1, 5)
        if phrasing == 1:
            p = f"The equation x² - {s}x + {pv} = 0 has two distinct positive roots. What is the larger root?"
        elif phrasing == 2:
            p = f"Two distinct positive integers have sum {s} and product {pv}. What is the larger one?"
        elif phrasing == 3:
            p = f"A quadratic x² - {s}x + {pv} has two unequal positive roots. What is the greater root?"
        elif phrasing == 4:
            p = f"Find the larger of the two distinct positive solutions to x² - {s}x + {pv} = 0."
        else:
            p = f"Two different positive numbers sum to {s} and multiply to {pv}. What is the larger?"
        add(p, answer, "quadratic_constrained")
    else:
        r = random.randint(2, 7)
        s = 2*r
        pv = r*r
        answer = r
        phrasing = random.randint(1, 5)
        if phrasing == 1:
            p = f"The equation x² - {s}x + {pv} = 0 has a repeated root. What is the root?"
        elif phrasing == 2:
            p = f"A quadratic x² - {s}x + {pv} has exactly one distinct root. What is it?"
        elif phrasing == 3:
            p = f"Two equal numbers sum to {s} and multiply to {pv}. What is that number?"
        elif phrasing == 4:
            p = f"Find the double root of x² - {s}x + {pv} = 0."
        else:
            p = f"The quadratic x² - {s}x + {pv} has discriminant zero. What is the root?"
        add(p, answer, "quadratic_constrained")

# ── 3. ARITHMETIC SEQUENCES ───────────────────────────────────
for _ in range(N):
    a1 = random.randint(1, 10)
    d = random.randint(1, 7)
    n = random.randint(5, 15)
    nth = a1 + (n-1)*d
    target = random.choice(["nth","sum","which_term"])
    if target == "nth":
        answer, q = nth, f"What is the {n}th term?"
    elif target == "sum":
        if n*(a1+nth) % 2 != 0:
            n += 1
            nth = a1 + (n-1)*d
        answer, q = n*(a1+nth)//2, f"What is the sum of the first {n} terms?"
    else:
        answer, q = n, f"Which term equals {nth}?"
    phrasing = random.randint(1, 5)
    if phrasing == 1:
        p = f"An arithmetic sequence has first term {a1} and common difference {d}. {q}"
    elif phrasing == 2:
        p = f"A sequence starts at {a1} and each term is {d} more than the previous. {q}"
    elif phrasing == 3:
        p = f"The first two terms of an arithmetic sequence are {a1} and {a1+d}. {q}"
    elif phrasing == 4:
        p = f"A student saves ${a1} in week 1 and increases savings by ${d} each week. {q}"
    else:
        p = f"In an arithmetic progression with first term {a1} and constant difference {d}, {q.lower()}"
    add(p, answer, "arithmetic_sequence")

# ── 3b. SEQUENCE CONSTRAINED ──────────────────────────────────
for _ in range(N//2):
    a1 = random.randint(1, 10)
    d = random.randint(2, 6)
    constraint = random.choice(["first_exceeding","first_exceeding","first_exceeding"])
    if constraint == "first_exceeding":
        threshold = random.randint(20, 60)
        n = 1
        while a1 + (n-1)*d <= threshold:
            n += 1
        answer = a1 + (n-1)*d
        t1,t2,t3 = a1, a1+d, a1+2*d
        phrasing = random.randint(1, 5)
        if phrasing == 1:
            p = f"The sequence {t1}, {t2}, {t3}, ... continues adding {d} each time. What is the first term greater than {threshold}?"
        elif phrasing == 2:
            p = f"A sequence goes {t1}, {t2}, {t3}, ... (adding {d} each step). What is the smallest term exceeding {threshold}?"
        elif phrasing == 3:
            p = f"Starting: {t1}, {t2}, {t3}, ... each term {d} more than the last. What is the first term above {threshold}?"
        elif phrasing == 4:
            p = f"The pattern {t1}, {t2}, {t3}, ... adds {d} each time. What is the first term greater than {threshold}?"
        else:
            p = f"Sequence: {t1}, {t2}, {t3}, ... (common difference {d}). What is the first term that exceeds {threshold}?"
        add(p, answer, "sequence_constrained")
    elif constraint == "last_below":
        threshold = random.randint(30, 80)
        last = a1
        term = a1
        while term + d < threshold:
            term += d
            last = term
        answer = last
        phrasing = random.randint(1, 5)
        if phrasing == 1:
            p = f"An arithmetic sequence has first term {a1} and common difference {d}. What is the largest term less than {threshold}?"
        elif phrasing == 2:
            p = f"A sequence starts at {a1} increasing by {d} each time. What is the last term below {threshold}?"
        elif phrasing == 3:
            p = f"Starting from {a1} with step {d}, what is the greatest term that stays under {threshold}?"
        elif phrasing == 4:
            p = f"In the sequence {a1}, {a1+d}, {a1+2*d}, ..., what is the last term less than {threshold}?"
        else:
            p = f"What is the largest number in the sequence {a1}, {a1+d}, {a1+2*d}, ... that is below {threshold}?"
        add(p, answer, "sequence_constrained")
    else:
        lo = random.randint(10, 30)
        hi = random.randint(40, 80)
        count = 0
        term = a1
        while term <= hi:
            if term >= lo:
                count += 1
            term += d
        if count > 0:
            phrasing = random.randint(1, 5)
            if phrasing == 1:
                p = f"How many terms of the sequence starting at {a1} with difference {d} fall between {lo} and {hi} inclusive?"
            elif phrasing == 2:
                p = f"A sequence begins at {a1} and increases by {d}. How many terms are in the range [{lo}, {hi}]?"
            elif phrasing == 3:
                p = f"Count the terms of {a1}, {a1+d}, {a1+2*d}, ... that satisfy {lo} ≤ term ≤ {hi}."
            elif phrasing == 4:
                p = f"How many values in the arithmetic sequence (first term {a1}, difference {d}) are between {lo} and {hi}?"
            else:
                p = f"In the sequence {a1}, {a1+d}, {a1+2*d}, ..., how many terms satisfy {lo} ≤ term ≤ {hi}?"
            add(p, count, "sequence_constrained")

# ── 4. GEOMETRIC SEQUENCES ────────────────────────────────────
for _ in range(N):
    a1 = random.randint(1, 4)
    r = random.randint(2, 3)
    n = random.randint(3, 6)
    nth = a1 * r**(n-1)
    target = random.choice(["nth","ratio","nth"])
    if target == "nth":
        answer, q = nth, f"What is the {n}th term?"
    elif target == "ratio":
        answer, q = r, "What is the common ratio?"
    else:
        answer, q = nth, f"What is the {n}th term?"
    phrasing = random.randint(1, 5)
    if phrasing == 1:
        p = f"A geometric sequence has first term {a1} and common ratio {r}. {q}"
    elif phrasing == 2:
        p = f"Each term of a sequence is {r} times the previous. The first term is {a1}. {q}"
    elif phrasing == 3:
        p = f"A geometric progression starts at {a1} with ratio {r}. {q}"
    elif phrasing == 4:
        p = f"The sequence {a1}, {a1*r}, {a1*r**2}, ... has constant ratio. {q}"
    else:
        p = f"A geometric sequence: first term {a1}, each next term multiplied by {r}. {q}"
    add(p, answer, "geometric_sequence")

# ── 5. CIRCLE GEOMETRY ────────────────────────────────────────
for _ in range(N):
    prob_type = random.choice(["chord","inscribed_right","radius_sq","two_circles"])
    if prob_type == "chord":
        d_half, half_chord, r = random.choice(TRIPLES)
        chord = 2 * half_chord
        phrasing = random.randint(1, 5)
        if phrasing == 1:
            p = f"A circle has radius {r}. A chord is {d_half} units from the center. What is the length of the chord?"
        elif phrasing == 2:
            p = f"In a circle with radius {r}, the perpendicular distance from the center to a chord is {d_half}. How long is the chord?"
        elif phrasing == 3:
            p = f"A chord of a circle with radius {r} has its midpoint {d_half} units from the center. What is the chord's length?"
        elif phrasing == 4:
            p = f"The center of a circle with radius {r} is {d_half} units from a chord. Find the chord length."
        else:
            p = f"How long is a chord that is {d_half} units from the center of a circle with radius {r}?"
        add(p, chord, "circle_geometry")
    elif prob_type == "inscribed_right":
        pt, qt, hyp = random.choice(TRIPLES)
        if hyp % 2 == 0:
            r = hyp // 2
            phrasing = random.randint(1, 5)
            if phrasing == 1:
                p = f"A right triangle with hypotenuse {hyp} is inscribed in a circle. What is the radius?"
            elif phrasing == 2:
                p = f"A circle circumscribes a right triangle whose hypotenuse is {hyp}. What is the circle's radius?"
            elif phrasing == 3:
                p = f"The hypotenuse of a right triangle inscribed in a circle is {hyp}. Find the circumradius."
            elif phrasing == 4:
                p = f"What is the radius of the circle circumscribed about a right triangle with hypotenuse {hyp}?"
            else:
                p = f"A right triangle fits inside a circle with hypotenuse as diameter. Hypotenuse = {hyp}. What is the radius?"
            add(p, r, "circle_geometry")
    elif prob_type == "radius_sq":
        r = random.randint(2, 10)
        phrasing = random.randint(1, 5)
        if phrasing == 1:
            p = f"A circle has area {r**2}π. What is the square of its radius?"
        elif phrasing == 2:
            p = f"If a circle's area is {r**2}π square units, what is r²?"
        elif phrasing == 3:
            p = f"A circular field has area {r**2}π. Find the square of the radius."
        elif phrasing == 4:
            p = f"For a circle with area {r**2}π, compute the square of the radius."
        else:
            p = f"A circle's area equals {r**2}π. What is r²?"
        add(p, r*r, "circle_geometry")
    else:
        t1 = random.choice([(6,8,10),(8,6,10)])
        t2 = random.choice([(5,12,13),(12,5,13)])
        r1 = t1[2] // 2
        r2 = t2[2] // 2
        answer = r1*r1 + r2*r2
        p = f"Circle A circumscribes a right triangle with hypotenuse {t1[2]}. Circle B circumscribes a right triangle with hypotenuse {t2[2]}. What is r₁² + r₂²?"
        add(p, answer, "circle_geometry")

# ── 6. COORDINATE GEOMETRY ────────────────────────────────────
for _ in range(N):
    prob_type = random.choice(["integer_slope","distance_triple","midpoint_sum","rotation"])
    if prob_type == "integer_slope":
        rise = random.choice([-4,-3,-2,-1,1,2,3,4])
        run = random.randint(1, 4)
        if rise % run == 0:
            slope = rise // run
            x1, y1 = random.randint(-3,3), random.randint(-3,3)
            x2, y2 = x1+run, y1+rise
            phrasing = random.randint(1, 5)
            if phrasing == 1:
                p = f"What is the slope of the line through ({x1},{y1}) and ({x2},{y2})?"
            elif phrasing == 2:
                p = f"A line passes through ({x1},{y1}) and ({x2},{y2}). What is its slope?"
            elif phrasing == 3:
                p = f"Find the slope of the segment from ({x1},{y1}) to ({x2},{y2})."
            elif phrasing == 4:
                p = f"Two points ({x1},{y1}) and ({x2},{y2}) determine a line. What is the slope?"
            else:
                p = f"What is the rate of change of y with respect to x for the line through ({x1},{y1}) and ({x2},{y2})?"
            add(p, slope, "coordinate_geometry")
    elif prob_type == "distance_triple":
        pt, qt, hyp = random.choice(TRIPLES)
        x1, y1 = random.randint(-3,3), random.randint(-3,3)
        x2, y2 = x1+pt, y1+qt
        phrasing = random.randint(1, 5)
        if phrasing == 1:
            p = f"What is the distance between ({x1},{y1}) and ({x2},{y2})?"
        elif phrasing == 2:
            p = f"Find the length of the segment from ({x1},{y1}) to ({x2},{y2})."
        elif phrasing == 3:
            p = f"Two points in the plane are ({x1},{y1}) and ({x2},{y2}). How far apart are they?"
        elif phrasing == 4:
            p = f"A segment has endpoints ({x1},{y1}) and ({x2},{y2}). What is its length?"
        else:
            p = f"Compute the distance between ({x1},{y1}) and ({x2},{y2})."
        add(p, hyp, "coordinate_geometry")
    elif prob_type == "midpoint_sum":
        x1,y1 = random.randint(-4,4), random.randint(-4,4)
        x2,y2 = random.randint(-4,4), random.randint(-4,4)
        if (x1+x2)%2==0 and (y1+y2)%2==0:
            mx,my = (x1+x2)//2, (y1+y2)//2
            answer = mx+my
            phrasing = random.randint(1, 5)
            if phrasing == 1:
                p = f"The midpoint of the segment from ({x1},{y1}) to ({x2},{y2}) is (a,b). What is a+b?"
            elif phrasing == 2:
                p = f"Find the sum of the coordinates of the midpoint of ({x1},{y1}) and ({x2},{y2})."
            elif phrasing == 3:
                p = f"What is the sum of the x and y coordinates of the midpoint of the segment connecting ({x1},{y1}) and ({x2},{y2})?"
            elif phrasing == 4:
                p = f"Segment AB has A=({x1},{y1}) and B=({x2},{y2}). What is the sum of the midpoint's coordinates?"
            else:
                p = f"The midpoint of ({x1},{y1}) and ({x2},{y2}) is point M. What is the sum of M's coordinates?"
            add(p, answer, "coordinate_geometry")
    else:
        x = random.randint(1, 5)
        y = random.randint(1, 5)
        angle = random.choice([90, 180, 270])
        if angle == 90: nx,ny = -y,x
        elif angle == 180: nx,ny = -x,-y
        else: nx,ny = y,-x
        answer = nx+ny
        phrasing = random.randint(1, 5)
        if phrasing == 1:
            p = f"Point ({x},{y}) is rotated {angle}° counterclockwise about the origin. What is the sum of the new point's coordinates?"
        elif phrasing == 2:
            p = f"After rotating ({x},{y}) by {angle}° counterclockwise around the origin, what is the sum of the resulting coordinates?"
        elif phrasing == 3:
            p = f"Apply a {angle}° counterclockwise rotation to ({x},{y}) about the origin. What is the sum of the image's coordinates?"
        elif phrasing == 4:
            p = f"What is the sum of the coordinates of the image of ({x},{y}) under a {angle}° counterclockwise rotation about the origin?"
        else:
            p = f"Rotate ({x},{y}) counterclockwise by {angle}° about the origin. Find the sum of the x and y coordinates of the result."
        add(p, answer, "coordinate_geometry")

# ── 7. MODULAR ARITHMETIC ─────────────────────────────────────
for _ in range(N):
    prob_type = random.choice(["power_mod","sum_mod","product_mod"])
    if prob_type == "power_mod":
        base = random.randint(2, 9)
        mod = random.randint(5, 13)
        exp = random.randint(15, 60)
        answer = pow(base, exp, mod)
        phrasing = random.randint(1, 5)
        if phrasing == 1:
            p = f"What is the remainder when {base}^{exp} is divided by {mod}?"
        elif phrasing == 2:
            p = f"Find {base}^{exp} mod {mod}."
        elif phrasing == 3:
            p = f"When {base} is raised to the {exp} power and divided by {mod}, what is the remainder?"
        elif phrasing == 4:
            p = f"Compute the remainder of {base}^{exp} ÷ {mod}."
        else:
            p = f"What is {base}^{exp} modulo {mod}?"
        add(p, answer, "modular_arithmetic")
    elif prob_type == "sum_mod":
        n = random.randint(20, 100)
        mod = random.randint(3, 9)
        answer = (n*(n+1)//2) % mod
        phrasing = random.randint(1, 5)
        if phrasing == 1:
            p = f"What is the remainder when 1+2+3+...+{n} is divided by {mod}?"
        elif phrasing == 2:
            p = f"Find the sum of integers from 1 to {n}, then find its remainder when divided by {mod}."
        elif phrasing == 3:
            p = f"What is (1+2+...+{n}) mod {mod}?"
        elif phrasing == 4:
            p = f"Compute the remainder when the sum of the first {n} positive integers is divided by {mod}."
        else:
            p = f"The sum 1+2+3+...+{n} is divided by {mod}. What is the remainder?"
        add(p, answer, "modular_arithmetic")
    else:
        a = random.randint(2, 9)
        b = random.randint(2, 9)
        mod = random.randint(4, 12)
        answer = (a*b) % mod
        phrasing = random.randint(1, 5)
        if phrasing == 1:
            p = f"What is the remainder when {a}×{b} is divided by {mod}?"
        elif phrasing == 2:
            p = f"Find ({a}×{b}) mod {mod}."
        elif phrasing == 3:
            p = f"Compute {a}×{b}, then find the remainder when divided by {mod}."
        elif phrasing == 4:
            p = f"What is {a} times {b} modulo {mod}?"
        else:
            p = f"When {a*b} is divided by {mod}, what is the remainder?"
        add(p, answer, "modular_arithmetic")

# ── 8. DIGIT COUNTING ─────────────────────────────────────────
for _ in range(N):
    prob_type = random.choice(["power_digits","product_digits","factorial_digits"])
    if prob_type == "power_digits":
        base = random.choice([2,3,5])
        exp = random.randint(5, 25)
        answer = len(str(base**exp))
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"How many digits does {base}^{exp} have?"
        elif phrasing == 2: p = f"How many digits are in the base-ten representation of {base}^{exp}?"
        elif phrasing == 3: p = f"When {base}^{exp} is written out in full, how many digits does it contain?"
        elif phrasing == 4: p = f"The number {base}^{exp} is expressed in decimal. How many digits does it have?"
        else: p = f"Find the number of digits in {base}^{exp}."
        add(p, answer, "digit_counting")
    elif prob_type == "product_digits":
        a = random.choice([2,4,5,8])
        ea = random.randint(3, 8)
        b = random.choice([2,5])
        eb = random.randint(3, 8)
        answer = len(str((a**ea)*(b**eb)))
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"How many digits does {a}^{ea} × {b}^{eb} have?"
        elif phrasing == 2: p = f"What is the number of digits in the product {a}^{ea} · {b}^{eb}?"
        elif phrasing == 3: p = f"When {a}^{ea} × {b}^{eb} is computed, how many digits appear?"
        elif phrasing == 4: p = f"Find the digit count of {a}^{ea} × {b}^{eb}."
        else: p = f"The product {a}^{ea} · {b}^{eb} — how many digits does it have?"
        add(p, answer, "digit_counting")
    else:
        n = random.randint(3, 8)
        answer = len(str(math.factorial(n)))
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"How many digits does {n}! have?"
        elif phrasing == 2: p = f"How many digits are in {n} factorial?"
        elif phrasing == 3: p = f"When {n}! is written in decimal, how many digits does it contain?"
        elif phrasing == 4: p = f"Find the number of digits in {n}!."
        else: p = f"The number {n}! — how many digits is it?"
        add(p, answer, "digit_counting")

# ── 9. RATE / WORK ────────────────────────────────────────────
for _ in range(N):
    prob_type = random.choice(["meeting","work_together","speed_distance"])
    if prob_type == "meeting":
        s1 = random.randint(2, 5)
        s2 = random.randint(2, 5)
        total = (s1+s2)*random.randint(2, 4)
        time = total//(s1+s2)
        dist1 = s1*time
        phrasing = random.randint(1, 5)
        if phrasing == 1:
            p = f"Two people start {total} miles apart and walk toward each other at {s1} mph and {s2} mph. How many miles does the first person walk before they meet?"
        elif phrasing == 2:
            p = f"Cities A and B are {total} miles apart. Alice bikes from A at {s1} mph and Bob from B at {s2} mph. How many miles from A do they meet?"
        elif phrasing == 3:
            p = f"Two trains {total} miles apart travel toward each other at {s1} mph and {s2} mph. How far does the first train travel before they meet?"
        elif phrasing == 4:
            p = f"Two runners start {total} meters apart heading toward each other at {s1} and {s2} m/s. How far does the first runner travel before meeting?"
        else:
            p = f"Points P and Q are {total} units apart. X moves from P at {s1} units/hr toward Q. Y moves from Q at {s2} units/hr toward P. How far from P do they meet?"
        add(p, dist1, "rate_problem")
    elif prob_type == "work_together":
        rates = [(2,3),(2,4),(3,4),(3,6),(4,6),(2,6)]
        r1,r2 = random.choice(rates)
        L = lcm(r1,r2)
        work_rate = L//r1 + L//r2
        if L % work_rate == 0:
            time = L//work_rate
            phrasing = random.randint(1, 5)
            if phrasing == 1:
                p = f"Person A completes a job in {r1} hours. Person B in {r2} hours. How long working together?"
            elif phrasing == 2:
                p = f"Pipe A fills a tank in {r1} hours. Pipe B fills it in {r2} hours. How many hours with both open?"
            elif phrasing == 3:
                p = f"Machine A processes a batch in {r1} hours. Machine B in {r2} hours. Working simultaneously, how long for one batch?"
            elif phrasing == 4:
                p = f"Worker A paints a room in {r1} days. Worker B in {r2} days. Working together, how many days?"
            else:
                p = f"Two people complete a task alone in {r1} and {r2} hours. How long if they work together?"
            add(p, time, "rate_problem")
    else:
        speed = random.randint(20, 80)
        time = random.randint(1, 6)
        dist = speed*time
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A car travels at {speed} mph for {time} hours. How many miles does it travel?"
        elif phrasing == 2: p = f"At {speed} miles per hour, how far does a train travel in {time} hours?"
        elif phrasing == 3: p = f"A cyclist rides at {speed} km/h for {time} hours. How far do they go?"
        elif phrasing == 4: p = f"A plane flies at {speed} mph. What distance does it cover in {time} hours?"
        else: p = f"Moving at a constant {speed} units per hour for {time} hours, what distance is covered?"
        add(p, dist, "rate_problem")

# ── 10. PERCENTAGE / RATIO ────────────────────────────────────
for _ in range(N):
    prob_type = random.choice(["percent_change","percent_of","ratio_split"])
    if prob_type == "percent_change":
        original = random.choice([100,200,80,120,60,50,150])
        pct = random.choice([10,20,25,50])
        direction = random.choice([True,False])
        new_val = original + original*pct//100 if direction else original - original*pct//100
        phrasing = random.randint(1, 5)
        if direction:
            if phrasing == 1: p = f"A price of ${original} increases by {pct}%. What is the new price?"
            elif phrasing == 2: p = f"A value of {original} grows by {pct}%. What is the result?"
            elif phrasing == 3: p = f"After a {pct}% increase, a quantity of {original} becomes what?"
            elif phrasing == 4: p = f"Sales were {original} units and increased by {pct}%. What are the new sales?"
            else: p = f"If {original} is increased by {pct} percent, what is the new amount?"
        else:
            if phrasing == 1: p = f"A price of ${original} decreases by {pct}%. What is the sale price?"
            elif phrasing == 2: p = f"A score of {original} drops by {pct}%. What is the new score?"
            elif phrasing == 3: p = f"After a {pct}% discount, an item costing ${original} sells for how much?"
            elif phrasing == 4: p = f"A population of {original} decreases by {pct}%. What is the new population?"
            else: p = f"If {original} is reduced by {pct} percent, what remains?"
        add(p, new_val, "percentage")
    elif prob_type == "percent_of":
        # only use combos that give clean integers
        combos = [(100,10),(100,20),(100,25),(100,50),(200,10),(200,25),(200,50),(80,25),(80,50),(60,50),(120,25),(40,50),(40,25)]
        total, pct = random.choice(combos)
        answer = total*pct//100
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"What is {pct}% of {total}?"
        elif phrasing == 2: p = f"Find {pct} percent of {total}."
        elif phrasing == 3: p = f"A class of {total} students — {pct}% passed. How many passed?"
        elif phrasing == 4: p = f"A store has {total} items and {pct}% are on sale. How many are on sale?"
        else: p = f"Out of {total}, how many represent {pct}%?"
        add(p, answer, "percentage")
    else:
        a = random.randint(2, 5)
        b = random.randint(2, 5)
        factor = random.randint(2, 6)
        total = (a+b)*factor
        larger = max(a,b)*factor
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"Two quantities are in ratio {a}:{b} and their total is {total}. What is the larger quantity?"
        elif phrasing == 2: p = f"Money is divided in ratio {a}:{b}. The total is ${total}. How much is the larger share?"
        elif phrasing == 3: p = f"A mixture has ingredients A and B in ratio {a}:{b}. Total is {total} liters. How many liters of the larger ingredient?"
        elif phrasing == 4: p = f"Two numbers in ratio {a}:{b} sum to {total}. What is the greater number?"
        else: p = f"Divide {total} in ratio {a}:{b}. What is the larger part?"
        add(p, larger, "percentage")

# ── 11. POLYGON AREA ──────────────────────────────────────────
for _ in range(N):
    shape = random.choice(["triangle","rhombus","rectangle","parallelogram","right_triangle"])
    if shape == "triangle":
        base = random.randint(4, 14)
        height = random.randint(3, 10)
        if base*height%2 != 0: base += 1
        answer = base*height//2
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A triangle has base {base} and height {height}. What is its area?"
        elif phrasing == 2: p = f"Find the area of a triangle with base {base} units and height {height} units."
        elif phrasing == 3: p = f"A triangular sail has base {base} m and perpendicular height {height} m. What is its area?"
        elif phrasing == 4: p = f"What is the area of a triangle whose base is {base} and altitude is {height}?"
        else: p = f"A triangle with base {base} and corresponding height {height} — what is its area?"
        add(p, answer, "polygon_area")
    elif shape == "rhombus":
        d1 = random.choice([6,8,10,12,14])
        d2 = random.choice([6,8,10,12])
        answer = d1*d2//2
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A rhombus has diagonals of length {d1} and {d2}. What is its area?"
        elif phrasing == 2: p = f"Find the area of a rhombus whose diagonals measure {d1} and {d2}."
        elif phrasing == 3: p = f"A diamond-shaped tile has diagonals {d1} and {d2} inches. What is its area?"
        elif phrasing == 4: p = f"What is the area of a rhombus with diagonals {d1} and {d2}?"
        else: p = f"The diagonals of a rhombus are {d1} and {d2}. Find the area."
        add(p, answer, "polygon_area")
    elif shape == "rectangle":
        l = random.randint(7, 15)
        w = random.randint(7, 15)
        answer = l*w
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A rectangle has length {l} and width {w}. What is its area?"
        elif phrasing == 2: p = f"Find the area of a {l} by {w} rectangle."
        elif phrasing == 3: p = f"A rectangular garden is {l} meters by {w} meters. What is its area?"
        elif phrasing == 4: p = f"What is the area of a rectangle with dimensions {l} × {w}?"
        else: p = f"A room measures {l} feet by {w} feet. What is the floor area?"
        add(p, answer, "polygon_area")
    elif shape == "parallelogram":
        base = random.randint(4, 12)
        height = random.randint(3, 10)
        answer = base*height
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A parallelogram has base {base} and height {height}. What is its area?"
        elif phrasing == 2: p = f"Find the area of a parallelogram with base {base} and perpendicular height {height}."
        elif phrasing == 3: p = f"What is the area of a parallelogram whose base is {base} and altitude is {height}?"
        elif phrasing == 4: p = f"A parallelogram has base {base} units and height {height} units. Find its area."
        else: p = f"Compute the area of a parallelogram with base {base} and height {height}."
        add(p, answer, "polygon_area")
    else:
        pt, qt, hyp = random.choice(TRIPLES)
        answer = pt*qt//2
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A right triangle has legs {pt} and {qt}. What is its area?"
        elif phrasing == 2: p = f"Find the area of a right triangle with legs of length {pt} and {qt}."
        elif phrasing == 3: p = f"A right triangle with legs {pt} and {qt} — what is its area?"
        elif phrasing == 4: p = f"What is the area of a right triangle whose two shorter sides are {pt} and {qt}?"
        else: p = f"A right triangle has perpendicular sides {pt} and {qt}. Find its area."
        add(p, answer, "polygon_area")

# ══════════════════════════════════════════════════════════════
# TIER 2
# ══════════════════════════════════════════════════════════════

# ── 12. LOGARITHM PROPERTIES ──────────────────────────────────
for _ in range(N):
    prob_type = random.choice(["log_power","log_eval","log_sum"])
    if prob_type == "log_power":
        base = random.choice([2,3,5,10])
        exp = random.randint(2, 6)
        val = base**exp
        answer = exp
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"What is log base {base} of {val}?"
        elif phrasing == 2: p = f"Solve for x: {base}^x = {val}."
        elif phrasing == 3: p = f"Find x such that {base} raised to the power x equals {val}."
        elif phrasing == 4: p = f"log_{base}({val}) = ?"
        else: p = f"To what power must {base} be raised to get {val}?"
        add(p, answer, "logarithm")
    elif prob_type == "log_eval":
        val = random.choice([1,10,100,1000,10000])
        answer = int(math.log10(val))
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"What is log₁₀({val})?"
        elif phrasing == 2: p = f"Compute log({val}) where log is base 10."
        elif phrasing == 3: p = f"What power of 10 equals {val}?"
        elif phrasing == 4: p = f"Evaluate log base 10 of {val}."
        else: p = f"Find the common logarithm of {val}."
        add(p, answer, "logarithm")
    else:
        base = random.choice([2,3,5])
        e1 = random.randint(1, 4)
        e2 = random.randint(1, 4)
        answer = e1+e2
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"What is log_{base}({base**e1}) + log_{base}({base**e2})?"
        elif phrasing == 2: p = f"Compute log_{base}({base**e1} × {base**e2})."
        elif phrasing == 3: p = f"Find log_{base}({base**e1}) + log_{base}({base**e2})."
        elif phrasing == 4: p = f"Evaluate log_{base}({base**(e1+e2)})."
        else: p = f"What is the sum log_{base}({base**e1}) + log_{base}({base**e2})?"
        add(p, answer, "logarithm")

# ── 13. BASIC PROBABILITY ─────────────────────────────────────
for _ in range(N):
    prob_type = random.choice(["single_die","two_dice","coin_prob"])
    if prob_type == "single_die":
        faces = random.choice([4, 6])
        k = random.randint(1, faces-2)
        answer = faces - k
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A fair {faces}-sided die is rolled. How many outcomes result in rolling more than {k}?"
        elif phrasing == 2: p = f"Roll a {faces}-sided die numbered 1 to {faces}. How many values are greater than {k}?"
        elif phrasing == 3: p = f"A {faces}-sided die is thrown. How many of the possible outcomes show a number greater than {k}?"
        elif phrasing == 4: p = f"On a {faces}-sided die, how many sides show a number greater than {k}?"
        else: p = f"A die has {faces} faces numbered 1 to {faces}. How many faces show a value exceeding {k}?"
        add(p, answer, "probability")
    elif prob_type == "two_dice":
        target = random.randint(5, 9)
        answer = sum(1 for i in range(1,7) for j in range(1,7) if i+j==target)
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"Two fair six-sided dice are rolled. How many of the 36 outcomes have a sum of {target}?"
        elif phrasing == 2: p = f"Roll two standard dice. In how many ways can the dice show a total of {target}?"
        elif phrasing == 3: p = f"Two 6-sided dice are thrown. Count the outcomes where the sum equals {target}."
        elif phrasing == 4: p = f"How many ordered pairs (a,b) with 1≤a,b≤6 satisfy a+b={target}?"
        else: p = f"Two dice are rolled. How many outcomes give a sum of {target}?"
        add(p, answer, "probability")
    else:
        n_f = random.randint(2, 4)
        k_h = random.randint(1, n_f-1)
        answer = math.comb(n_f, k_h)
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A fair coin is flipped {n_f} times. In how many ways can exactly {k_h} heads appear?"
        elif phrasing == 2: p = f"Flip a coin {n_f} times. How many of the possible sequences contain exactly {k_h} heads?"
        elif phrasing == 3: p = f"A coin is tossed {n_f} times. How many outcomes have exactly {k_h} tails?"
        elif phrasing == 4: p = f"In how many ways can {k_h} heads appear in {n_f} coin flips?"
        else: p = f"{n_f} coin flips — how many sequences contain exactly {k_h} heads?"
        add(p, answer, "probability")

# ── 13b. PROBABILITY — AT LEAST ONE (constraint variant) ──────
for _ in range(N//2):
    prob_type = random.choice(["at_least_one_heads","at_least_one_match","at_least_one_six"])
    if prob_type == "at_least_one_heads":
        n_f = random.randint(2, 4)
        answer = 2**n_f - 1
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A fair coin is flipped {n_f} times. How many of the {2**n_f} possible outcomes contain at least one head?"
        elif phrasing == 2: p = f"Flip a coin {n_f} times. In how many sequences does at least one head appear?"
        elif phrasing == 3: p = f"A coin is tossed {n_f} times. How many outcomes are not all tails?"
        elif phrasing == 4: p = f"Out of all {2**n_f} results of {n_f} coin flips, how many include at least one head?"
        else: p = f"{n_f} coin flips — in how many of the {2**n_f} outcomes does at least one head appear?"
        add(p, answer, "probability_constrained")
    elif prob_type == "at_least_one_six":
        n_r = 2  # restrict to 2 rolls for simplicity
        # total outcomes - no sixes = 6^2 - 5^2 = 36 - 25 = 11
        answer = 6**n_r - 5**n_r
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A fair die is rolled {n_r} times. How many of the {6**n_r} outcomes contain at least one 6?"
        elif phrasing == 2: p = f"Roll a six-sided die {n_r} times. In how many outcomes does at least one 6 appear?"
        elif phrasing == 3: p = f"Two dice are rolled one at a time. How many of the {6**n_r} possible sequences show at least one 6?"
        elif phrasing == 4: p = f"Out of {6**n_r} possible results of {n_r} die rolls, how many include at least one 6?"
        else: p = f"{n_r} rolls of a die — in how many of the {6**n_r} outcomes does at least one 6 appear?"
        add(p, answer, "probability_constrained")
    else:
        r = random.randint(2, 4)
        b = random.randint(2, 4)
        total = r + b
        if b >= 2:
            both_blue = math.comb(b, 2)
            tot_ways = math.comb(total, 2)
            answer = tot_ways - both_blue  # count with at least one red
            phrasing = random.randint(1, 5)
            if phrasing == 1: p = f"A bag has {r} red and {b} blue marbles. Two are drawn without replacement. How many of the {tot_ways} possible pairs contain at least one red marble?"
            elif phrasing == 2: p = f"From {r} red and {b} blue marbles, draw 2. How many ways include at least one red?"
            elif phrasing == 3: p = f"A jar has {r} red and {b} blue marbles. Two are drawn. In how many ways is at least one red?"
            elif phrasing == 4: p = f"Draw 2 from {r} red and {b} blue. How many of the {tot_ways} selections are not both blue?"
            else: p = f"From {r} red and {b} blue, choose 2. How many selections have at least one red marble?"
            add(p, answer, "probability_constrained")

# ── 14. CONDITIONAL PROBABILITY ───────────────────────────────
for _ in range(N):
    prob_type = random.choice(["given_first","same_color","independent_and"])
    if prob_type == "given_first":
        r = random.randint(3, 6)
        b = random.randint(2, 4)
        total = r+b
        answer = r - 1  # remaining red marbles after one removed
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A bag has {r} red and {b} blue marbles. One red marble is drawn and removed. How many red marbles remain?"
        elif phrasing == 2: p = f"From {r} red and {b} blue marbles, one red is removed. How many red marbles are left?"
        elif phrasing == 3: p = f"A jar has {r} red and {b} blue candies. After eating one red, how many red candies remain?"
        elif phrasing == 4: p = f"There are {r} red and {b} blue marbles. One red is taken out. How many red marbles are left in the bag?"
        else: p = f"A box has {r} red and {b} blue balls. One red is removed. How many red balls remain?"
        add(p, answer, "conditional_probability")
    elif prob_type == "same_color":
        r = random.randint(2, 4)
        b = random.randint(2, 4)
        total = r+b
        if r >= 2 and b >= 2:
            answer = math.comb(r,2) + math.comb(b,2)  # count of same-color pairs
            phrasing = random.randint(1, 5)
            if phrasing == 1: p = f"A bag has {r} red and {b} blue marbles. Two are drawn without replacement. How many of the {math.comb(total,2)} possible pairs are the same color?"
            elif phrasing == 2: p = f"From {r} red and {b} blue marbles, 2 are chosen. How many ways result in both being the same color?"
            elif phrasing == 3: p = f"Two marbles drawn from {r} red and {b} blue. In how many ways are both the same color?"
            elif phrasing == 4: p = f"A jar holds {r} red and {b} blue. Draw 2. How many of the possible draws give matching colors?"
            else: p = f"Choose 2 from {r} red and {b} blue marbles. How many selections have both marbles the same color?"
            add(p, answer, "conditional_probability")
    else:
        # use simple fractions that multiply to clean answer
        pairs = [(1,2,1,3),(1,3,1,4),(1,2,1,4),(2,3,1,2),(1,4,1,2)]
        p_a_n,p_a_d,p_b_n,p_b_d = random.choice(pairs)
        num = p_a_n*p_b_n
        den = p_a_d*p_b_d
        g = gcd(num, den)
        answer = num//g + den//g
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"Event A has probability {p_a_n}/{p_a_d}. Event B has probability {p_b_n}/{p_b_d}. A and B are independent. P(both occur) = m/n reduced. What is m+n?"
        elif phrasing == 2: p = f"Two independent events have probabilities {p_a_n}/{p_a_d} and {p_b_n}/{p_b_d}. P(both happen) = m/n in lowest terms. Find m+n."
        elif phrasing == 3: p = f"P(A) = {p_a_n}/{p_a_d} and P(B) = {p_b_n}/{p_b_d} with A, B independent. P(A and B) = m/n simplified. What is m+n?"
        elif phrasing == 4: p = f"Two independent events occur with probabilities {p_a_n}/{p_a_d} and {p_b_n}/{p_b_d}. P(both) = m/n reduced. Give m+n."
        else: p = f"Independent events: P(A) = {p_a_n}/{p_a_d}, P(B) = {p_b_n}/{p_b_d}. P(A∩B) = m/n lowest terms. What is m+n?"
        add(p, answer, "conditional_probability")

# ── 15. COMPLEX NUMBERS ───────────────────────────────────────
for _ in range(N):
    prob_type = random.choice(["modulus_sq","powers_of_i","complex_product"])
    if prob_type == "modulus_sq":
        a = random.randint(1, 5)
        b = random.randint(1, 5)
        answer = a**2 + b**2
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"If z = {a} + {b}i, what is |z|²?"
        elif phrasing == 2: p = f"Find the square of the modulus of {a} + {b}i."
        elif phrasing == 3: p = f"For z = {a} + {b}i, compute |z|²."
        elif phrasing == 4: p = f"The complex number z = {a} + {b}i. What is the square of its absolute value?"
        else: p = f"What is |{a} + {b}i|²?"
        add(p, answer, "complex_numbers")
    elif prob_type == "powers_of_i":
        exp = random.randint(1, 50)
        r = exp % 4
        real_p = {0:1,1:0,2:-1,3:0}
        imag_p = {0:0,1:1,2:0,3:-1}
        answer = real_p[r] + imag_p[r]
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"What is the sum of the real and imaginary parts of i^{exp}, where i=√(-1)?"
        elif phrasing == 2: p = f"For i=√(-1), compute Re(i^{exp}) + Im(i^{exp})."
        elif phrasing == 3: p = f"If i²=-1, what is Re(i^{exp}) + Im(i^{exp})?"
        elif phrasing == 4: p = f"i^{exp} = a + bi. What is a+b?"
        else: p = f"Compute the sum of real and imaginary parts of i^{exp} where i=√(-1)."
        add(p, answer, "complex_numbers")
    else:
        # restrict: multiply (a+bi) by real scalar c — simpler computation
        a = random.randint(1, 5)
        b = random.randint(1, 5)
        c = random.randint(2, 4)  # purely real
        real = a*c
        imag = b*c
        answer = real + imag
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"Multiply ({a}+{b}i) by {c}. What is the sum of the real and imaginary parts of the result?"
        elif phrasing == 2: p = f"{c}×({a}+{b}i) = p+qi. What is p+q?"
        elif phrasing == 3: p = f"Compute {c}×({a}+{b}i) and find the sum of real and imaginary parts."
        elif phrasing == 4: p = f"If z = {a}+{b}i, find Re({c}z) + Im({c}z)."
        else: p = f"What is the sum of the real and imaginary parts of {c}×({a}+{b}i)?"
        add(p, answer, "complex_numbers")

# ── 16. POLYNOMIAL REMAINDER ──────────────────────────────────
for _ in range(N):
    root = random.randint(1, 5)
    a = random.randint(1, 3)
    b = random.randint(-5, 5)
    c = random.randint(-5, 5)
    answer = a*root**2 + b*root + c
    def fmt(coef, var):
        if coef == 0: return ""
        if coef == 1: return f"+{var}"
        if coef == -1: return f"-{var}"
        if coef > 0: return f"+{coef}{var}"
        return f"{coef}{var}"
    expr = f"{a}x²{fmt(b,'x')}{'+' + str(c) if c >= 0 else str(c)}"
    phrasing = random.randint(1, 5)
    if phrasing == 1: p = f"What is the value of {expr} at x={root}?"
    elif phrasing == 2: p = f"Evaluate P({root}) where P(x) = {expr}."
    elif phrasing == 3: p = f"Find P({root}) for the polynomial P(x) = {expr}."
    elif phrasing == 4: p = f"When x={root}, what does {expr} equal?"
    else: p = f"Substitute x={root} into {expr}. What is the result?"
    add(p, answer, "polynomial")

# ── 17. 3D GEOMETRY ───────────────────────────────────────────
for _ in range(N):
    shape = random.choice(["cube_diagonal_sq","box_volume","box_surface","cube_volume"])
    if shape == "cube_diagonal_sq":
        s = random.randint(2, 8)
        answer = 3*s*s
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A cube has side length {s}. What is the square of the length of its space diagonal?"
        elif phrasing == 2: p = f"Find d² where d is the main diagonal of a cube with side {s}."
        elif phrasing == 3: p = f"A cube with edge {s} — what is the square of the diagonal connecting opposite vertices?"
        elif phrasing == 4: p = f"What is the square of the longest diagonal in a cube with side {s}?"
        else: p = f"For a cube with side {s}, compute the square of its space diagonal."
        add(p, answer, "geometry_3d")
    elif shape == "box_volume":
        l,w,h = random.randint(2,8), random.randint(2,8), random.randint(2,8)
        answer = l*w*h
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A rectangular box has length {l}, width {w}, and height {h}. What is its volume?"
        elif phrasing == 2: p = f"Find the volume of a box with dimensions {l}×{w}×{h}."
        elif phrasing == 3: p = f"A {l} by {w} by {h} rectangular prism — what is its volume?"
        elif phrasing == 4: p = f"What is the volume of a rectangular box measuring {l}×{w}×{h}?"
        else: p = f"Compute the volume of a rectangular prism with length {l}, width {w}, height {h}."
        add(p, answer, "geometry_3d")
    elif shape == "box_surface":
        l,w,h = random.randint(2,8), random.randint(2,8), random.randint(2,8)
        answer = 2*(l*w + l*h + w*h)
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A rectangular box has length {l}, width {w}, height {h}. What is its surface area?"
        elif phrasing == 2: p = f"Find the total surface area of a box with dimensions {l}×{w}×{h}."
        elif phrasing == 3: p = f"What is the surface area of a {l} by {w} by {h} rectangular prism?"
        elif phrasing == 4: p = f"A gift box has dimensions {l}×{w}×{h}. What is the total surface area?"
        else: p = f"Compute the surface area of a rectangular box with dimensions {l}, {w}, {h}."
        add(p, answer, "geometry_3d")
    else:
        s = random.randint(2, 8)
        answer = s**3
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A cube has side length {s}. What is its volume?"
        elif phrasing == 2: p = f"Find the volume of a cube with edge length {s}."
        elif phrasing == 3: p = f"What is the volume of a cube whose side measures {s}?"
        elif phrasing == 4: p = f"A cubic container has side {s}. What is its volume?"
        else: p = f"Compute the volume of a cube with side {s}."
        add(p, answer, "geometry_3d")

# ── 18. NUMBER THEORY ─────────────────────────────────────────
for _ in range(N):
    prob_type = random.choice(["count_divisors","sum_divisors","count_multiples","prime_count"])
    if prob_type == "count_divisors":
        pp, qq = random.sample([2,3,5,7][:3], 2)
        aa = random.randint(1, 3)
        bb = random.randint(1, 3)
        n = pp**aa * qq**bb
        answer = (aa+1)*(bb+1)
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"How many positive divisors does {n} have?"
        elif phrasing == 2: p = f"Find the number of positive integers that divide {n} evenly."
        elif phrasing == 3: p = f"How many factors does {n} have?"
        elif phrasing == 4: p = f"Count the positive divisors of {n}."
        else: p = f"How many positive integers are divisors of {n}?"
        add(p, answer, "number_theory")
    elif prob_type == "sum_divisors":
        pp = random.choice([2,3,5])
        aa = random.randint(2, 4)
        n = pp**aa
        answer = sum(pp**i for i in range(aa+1))
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"What is the sum of all positive divisors of {n}?"
        elif phrasing == 2: p = f"Add up all positive integers that divide {n}. What is the total?"
        elif phrasing == 3: p = f"Find the sum of divisors of {n}."
        elif phrasing == 4: p = f"Compute the sum of all factors of {n}."
        else: p = f"What is the sum of the positive divisors of {n}?"
        add(p, answer, "number_theory")
    elif prob_type == "count_multiples":
        d = random.randint(3, 9)
        # ensure n is exact multiple of d so answer is clean
        mult = random.randint(8, 20)
        n = d * mult
        answer = mult
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"How many positive integers less than or equal to {n} are divisible by {d}?"
        elif phrasing == 2: p = f"Count the multiples of {d} from 1 to {n}."
        elif phrasing == 3: p = f"How many integers from 1 to {n} have {d} as a factor?"
        elif phrasing == 4: p = f"How many of the integers 1, 2, ..., {n} are multiples of {d}?"
        else: p = f"Among 1 through {n}, how many are divisible by {d}?"
        add(p, answer, "number_theory")
    else:
        n = random.randint(20, 60)
        a = random.choice([2, 3])
        b = random.choice([5, 7])
        answer = n//a + n//b - n//(a*b)
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"How many integers from 1 to {n} are divisible by {a} or {b}?"
        elif phrasing == 2: p = f"Count the integers from 1 to {n} that are multiples of {a} or multiples of {b}."
        elif phrasing == 3: p = f"How many numbers from 1 to {n} have {a} or {b} as a factor?"
        elif phrasing == 4: p = f"Among the integers 1 through {n}, how many are divisible by at least one of {a} or {b}?"
        else: p = f"Find the count of integers from 1 to {n} divisible by {a} or by {b}."
        add(p, answer, "number_theory")

# ── 19. TELESCOPING SUMS ──────────────────────────────────────
for _ in range(N):
    prob_type = random.choice(["partial_fractions","arithmetic_sum","squares_sum"])
    if prob_type == "partial_fractions":
        n = random.randint(3, 10)
        answer = n  # numerator of n/(n+1)
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"The sum 1/(1·2)+1/(2·3)+...+1/({n}·{n+1}) = {n}/{n+1}. What is the numerator?"
        elif phrasing == 2: p = f"Find the sum 1/(1·2)+1/(2·3)+...+1/({n}·{n+1}). The answer is a fraction with denominator {n+1}. What is the numerator?"
        elif phrasing == 3: p = f"The telescoping sum 1/2+1/6+...+1/({n}·{n+1}) simplifies to n/(n+1). What is n?"
        elif phrasing == 4: p = f"What is the numerator when 1/(1·2)+1/(2·3)+...+1/({n}·{n+1}) is written in lowest terms?"
        else: p = f"The sum 1/(1·2)+1/(2·3)+...+1/({n}·{n+1}) equals {n}/{n+1}. What is the numerator?"
        add(p, answer, "telescoping")
    elif prob_type == "arithmetic_sum":
        n = random.randint(4, 12)
        if n*(n+1)%2==0:
            answer = n*(n+1)//2
            phrasing = random.randint(1, 5)
            if phrasing == 1: p = f"What is 1+2+3+...+{n}?"
            elif phrasing == 2: p = f"Find the sum of the first {n} positive integers."
            elif phrasing == 3: p = f"Compute 1+2+3+...+{n}."
            elif phrasing == 4: p = f"What is the sum of all integers from 1 to {n}?"
            else: p = f"Add up all whole numbers from 1 to {n}. What is the total?"
            add(p, answer, "telescoping")
    else:
        n = random.randint(3, 8)
        answer = (n+1)**2 - 1
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"Evaluate (2²-1²)+(3²-2²)+(4²-3²)+...+({n+1}²-{n}²)."
        elif phrasing == 2: p = f"Compute the telescoping sum (2²-1²)+(3²-2²)+...+({n+1}²-{n}²)."
        elif phrasing == 3: p = f"What is the value of (4-1)+(9-4)+(16-9)+...+({(n+1)**2}-{n**2})?"
        elif phrasing == 4: p = f"Find the sum: Σ[(k+1)²-k²] for k=1 to {n}."
        else: p = f"What is (2²-1²)+(3²-2²)+...+({n+1}²-{n}²)?"
        add(p, answer, "telescoping")

# ── 20. MEAN / MEDIAN / MODE ──────────────────────────────────
for _ in range(N):
    prob_type = random.choice(["find_mean","find_missing","find_mean"])
    if prob_type == "find_mean":
        vals = [random.randint(1,20) for _ in range(random.randint(4,7))]
        if sum(vals)%len(vals)==0:
            answer = sum(vals)//len(vals)
            phrasing = random.randint(1, 5)
            if phrasing == 1: p = f"Find the mean of {', '.join(map(str,vals))}."
            elif phrasing == 2: p = f"What is the average of {', '.join(map(str,vals))}?"
            elif phrasing == 3: p = f"Calculate the arithmetic mean of {', '.join(map(str,vals))}."
            elif phrasing == 4: p = f"A data set is {{{', '.join(map(str,vals))}}}. What is the mean?"
            else: p = f"The values are {', '.join(map(str,vals))}. Find their average."
            add(p, answer, "statistics")
    elif prob_type == "find_missing":
        n = random.randint(4, 6)
        mean = random.randint(5, 15)
        vals = [random.randint(1,20) for _ in range(n-1)]
        missing = mean*n - sum(vals)
        if 1 <= missing <= 30:
            phrasing = random.randint(1, 5)
            if phrasing == 1: p = f"A set of {n} numbers has mean {mean}. The known values are {', '.join(map(str,vals))}. What is the missing number?"
            elif phrasing == 2: p = f"The average of {n} values is {mean}. If {n-1} of them are {', '.join(map(str,vals))}, find the remaining value."
            elif phrasing == 3: p = f"{n} quiz scores average {mean}. The first {n-1} scores are {', '.join(map(str,vals))}. What is the last score?"
            elif phrasing == 4: p = f"The mean of {n} numbers is {mean}. {n-1} of them are {', '.join(map(str,vals))}. Find the {n}th number."
            else: p = f"Given {n-1} values {', '.join(map(str,vals))} and mean {mean} for all {n}, what is the missing value?"
            add(p, missing, "statistics")
    else:
        vals = sorted([random.randint(1,20) for _ in range(random.choice([5,7]))])
        mid = len(vals)//2
        answer = vals[mid]
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"Find the median of {', '.join(map(str,vals))}."
        elif phrasing == 2: p = f"What is the middle value when {', '.join(map(str,vals))} is arranged in order?"
        elif phrasing == 3: p = f"The data set {{{', '.join(map(str,vals))}}} — what is the median?"
        elif phrasing == 4: p = f"Arrange {', '.join(map(str,random.sample(vals,len(vals))))} in order and find the median."
        else: p = f"What is the median of {', '.join(map(str,vals))}?"
        add(p, answer, "statistics")

# ── 21. CONSTRAINED COMBINATORICS ─────────────────────────────
for _ in range(N):
    prob_type = random.choice(["restricted_committee","arrangements_forbidden","restricted_committee"])  # digit_sum dropped
    if prob_type == "restricted_committee":
        n = random.randint(6, 9)
        k = random.randint(2, 3)
        total = math.comb(n,k)
        both_on = math.comb(n-2, k-2)
        answer = total - both_on
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"A committee of {k} is chosen from {n} people. Two specific people refuse to serve together. How many valid committees are possible?"
        elif phrasing == 2: p = f"From {n} candidates, choose {k}. Alice and Bob cannot both be selected. How many committees?"
        elif phrasing == 3: p = f"In how many ways can {k} people be chosen from {n} if two particular members cannot both be chosen?"
        elif phrasing == 4: p = f"A team of {k} is selected from {n} players. Two rivals cannot both be on the team. How many possible teams?"
        else: p = f"Choose {k} from {n} people, but persons A and B cannot both be included. How many ways?"
        add(p, answer, "constrained_combinatorics")
    elif prob_type == "arrangements_forbidden":
        n = random.randint(4, 6)
        answer = math.factorial(n-2)
        phrasing = random.randint(1, 5)
        if phrasing == 1: p = f"{n} people stand in a line. Person A must be first and Person B must be last. How many arrangements are possible?"
        elif phrasing == 2: p = f"In how many ways can {n} people line up if the tallest must be at the front and the shortest at the back?"
        elif phrasing == 3: p = f"{n} students are arranged in a row. The president must be first and vice president last. How many arrangements?"
        elif phrasing == 4: p = f"How many ways can {n} people be arranged in a line if two specific people must occupy the first and last positions?"
        else: p = f"{n} runners line up. The fastest is always first and slowest always last. How many arrangements for the others?"
        add(p, answer, "constrained_combinatorics")
    else:
        d = random.randint(2, 3)
        target_sum = random.randint(d, d*4)
        count = sum(1 for num in range(10**(d-1), 10**d) if sum(int(ch) for ch in str(num))==target_sum)
        if 5 <= count <= 150:
            phrasing = random.randint(1, 5)
            if phrasing == 1: p = f"How many {d}-digit positive integers have digits that sum to {target_sum}?"
            elif phrasing == 2: p = f"Count the {d}-digit numbers whose digit sum equals {target_sum}."
            elif phrasing == 3: p = f"How many {d}-digit integers have a digit sum of {target_sum}?"
            elif phrasing == 4: p = f"In how many {d}-digit numbers do the digits add up to {target_sum}?"
            else: p = f"Find the number of {d}-digit positive integers with digit sum {target_sum}."
            add(p, count, "constrained_combinatorics")

# ══════════════════════════════════════════════════════════════
# TIER 3 — KEEP FROM V2
# ══════════════════════════════════════════════════════════════

# ── 22. GCD ───────────────────────────────────────────────────
for _ in range(N):
    A = random.randint(12, 40)
    B = random.randint(12, 40)
    answer = gcd(A, B)
    phrasing = random.randint(1, 5)
    if phrasing == 1: p = f"A gardener wants to plant {A} roses and {B} tulips in equal rows, each with only one type. What is the maximum row length with no flowers left over?"
    elif phrasing == 2: p = f"Two ribbons have lengths {A} cm and {B} cm. What is the greatest length they can both be cut into with no waste?"
    elif phrasing == 3: p = f"What is the greatest common divisor of {A} and {B}?"
    elif phrasing == 4: p = f"Tiles of a single size must exactly cover a {A}-foot wall and a {B}-foot wall. What is the largest possible tile size?"
    else: p = f"Find the largest integer that divides both {A} and {B} evenly."
    add(p, answer, "gcd")

# ── 23. LCM ───────────────────────────────────────────────────
for _ in range(N):
    pairs = [(4,6),(6,8),(4,8),(6,9),(4,10),(6,10),(8,12),(4,12),(9,6),(10,6)]
    A, B = random.choice(pairs)
    answer = lcm(A, B)
    phrasing = random.randint(1, 5)
    if phrasing == 1: p = f"Bus A comes every {A} minutes and Bus B every {B} minutes. They just left together. In how many minutes will they next leave together?"
    elif phrasing == 2: p = f"What is the least common multiple of {A} and {B}?"
    elif phrasing == 3: p = f"Two events repeat every {A} and {B} days. Starting today, when is the next day both occur?"
    elif phrasing == 4: p = f"Signal A flashes every {A} seconds, Signal B every {B} seconds. How many seconds until they flash simultaneously again?"
    else: p = f"Find the smallest positive integer divisible by both {A} and {B}."
    add(p, answer, "lcm")

# ── 24. PYTHAGOREAN ───────────────────────────────────────────
for _ in range(N):
    pt, qt, hyp = random.choice(TRIPLES)
    phrasing = random.randint(1, 5)
    if phrasing == 1: p, answer = f"A right triangle has legs {pt} and {qt}. What is the hypotenuse?", hyp
    elif phrasing == 2: p, answer = f"Two legs of a right triangle are {pt} and {qt}. Find the length of the longest side.", hyp
    elif phrasing == 3: p, answer = f"A ladder leans against a wall. Its base is {pt} feet from the wall and it reaches {qt} feet up. How long is the ladder?", hyp
    elif phrasing == 4: p, answer = f"In a right triangle with shorter sides {pt} and {qt}, what is the hypotenuse?", hyp
    else: p, answer = f"What is the hypotenuse of a right triangle with legs {pt} and {qt}?", hyp
    add(p, answer, "pythagorean")

# ── 25. INTERIOR ANGLES ───────────────────────────────────────
for _ in range(N):
    sides = random.randint(5, 10)
    answer = (sides-2)*180
    phrasing = random.randint(1, 5)
    if phrasing == 1: p = f"What is the sum of the interior angles of a polygon with {sides} sides?"
    elif phrasing == 2: p = f"A convex polygon has {sides} vertices. What do its interior angles sum to in degrees?"
    elif phrasing == 3: p = f"Find the sum of interior angles of a {sides}-gon."
    elif phrasing == 4: p = f"A regular polygon has {sides} sides. What is the total of all its interior angles?"
    else: p = f"What is the sum in degrees of the interior angles of a {sides}-sided polygon?"
    add(p, answer, "interior_angles")

# ── 26. UNITS DIGIT ───────────────────────────────────────────
for _ in range(N):
    B = random.choice([2, 3, 4, 7, 8, 9])  # removed 5,6 — always same digit
    E = random.randint(10, 30)
    answer = CYCLES[B][(E-1)%len(CYCLES[B])]
    phrasing = random.randint(1, 5)
    if phrasing == 1: p = f"What is the units digit of {B}^{E}?"
    elif phrasing == 2: p = f"When {B}^{E} is written in full, what is its last digit?"
    elif phrasing == 3: p = f"Find the ones digit of {B} raised to the power {E}."
    elif phrasing == 4: p = f"What digit appears in the units place of {B}^{E}?"
    else: p = f"Determine the units digit of {B}^{E}."
    add(p, answer, "units_digit")

# ── 27. COMBINATIONS C(N,K) ───────────────────────────────────
for _ in range(N):
    n_val = random.randint(5, 7)
    k_val = 2  # restrict to K=2 only for goldilocks
    answer = math.comb(n_val, k_val)
    phrasing = random.randint(1, 6)
    if phrasing == 1: p = f"A committee of {k_val} is chosen from {n_val} people. Using C(n,k) = n!/(k!(n-k)!), how many committees are possible?"
    elif phrasing == 2: p = f"How many ways can {k_val} books be selected from {n_val} different books? Use C({n_val},{k_val}) = {n_val}!/({k_val}!·{n_val-k_val}!)."
    elif phrasing == 3: p = f"A pizza shop has {n_val} toppings. How many distinct {k_val}-topping pizzas exist? Apply C(n,k) = n!/(k!(n-k)!)."
    elif phrasing == 4: p = f"From {n_val} students, {k_val} are picked for a team. Use C(n,k) = n!/(k!(n-k)!). How many possible teams?"
    elif phrasing == 5: p = f"In how many ways can {k_val} players be chosen from {n_val}? Use the combination formula C(n,k)."
    else: p = f"How many {k_val}-element subsets does a {n_val}-element set have? Use C({n_val},{k_val})."
    add(p, answer, "combinations")

# ── 28. HANDSHAKES / TOURNAMENT ───────────────────────────────
for _ in range(N):
    n_val = random.randint(4, 8)
    answer = n_val*(n_val-1)//2
    phrasing = random.randint(1, 6)
    if phrasing == 1: p = f"At a party, every person shakes hands with every other person exactly once. There are {n_val} people. Using C(n,2) = n(n-1)/2, how many handshakes occur?"
    elif phrasing == 2: p = f"{n_val} teams each play every other team exactly once. Using C(n,2) = n(n-1)/2, how many games are played?"
    elif phrasing == 3: p = f"In a round-robin tournament with {n_val} players, every pair plays once. Apply C(n,2) = n(n-1)/2. How many matches?"
    elif phrasing == 4: p = f"{n_val} friends each send one letter to every other friend. Using C(n,2) = n(n-1)/2, how many letters are sent?"
    elif phrasing == 5: p = f"How many line segments connect {n_val} points if every pair is connected? Use C(n,2) = n(n-1)/2."
    else: p = f"In a group of {n_val} people, each meets every other exactly once. Using C(n,2) = n(n-1)/2, how many meetings?"
    add(p, answer, "combinations")

# ── 29. TRAPEZOID AREA ────────────────────────────────────────
for _ in range(N):
    A = random.randint(4, 12)
    B = random.randint(A+2, 18)
    H = random.randint(3, 8)
    if (A+B)*H%2 != 0: H += 1
    answer = (A+B)*H//2
    phrasing = random.randint(1, 5)
    if phrasing == 1: p = f"A trapezoid has parallel sides {A} and {B} with height {H}. What is its area?"
    elif phrasing == 2: p = f"Find the area of a trapezoid with bases {A} and {B} and height {H}."
    elif phrasing == 3: p = f"A trapezoidal plot has parallel sides {A} m and {B} m and height {H} m. What is its area?"
    elif phrasing == 4: p = f"What is the area of a trapezoid whose parallel sides are {A} and {B} and height is {H}?"
    else: p = f"Compute the area of a trapezoid with parallel sides {A} and {B} and altitude {H}."
    add(p, answer, "trapezoid")

# ══════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════
random.shuffle(all_problems)
counts = Counter(p['skeleton_type'] for p in all_problems)
print(f"\nProblems by skeleton type ({len(counts)} types):")
for t,c in sorted(counts.items()):
    print(f"  {t:40s}: {c}")
print(f"\nTotal problems: {len(all_problems)}")
with open('/teamspace/studios/this_studio/rl-intro/main/data/skeleton_dataset_v3.json','w') as f:
    json.dump(all_problems, f, indent=2)
print("Saved to main/data/skeleton_dataset_v3.json")
