import random
import json
import math

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    return a * b // gcd(a, b)

all_problems = []

def add(problem, answer, reasoning, skeleton_type):
    all_problems.append({
        "problem": problem,
        "answer": str(answer),
        "reasoning": reasoning,
        "skeleton_type": skeleton_type
    })

N_EACH = 200

# GCD gardener — cap at 30
for _ in range(N_EACH):
    A = random.randint(12, 30)
    B = random.randint(12, 30)
    answer = gcd(A, B)
    add(
        f"A gardener wants to plant {A} roses and {B} tulips in rows, with each row containing only one type of flower. All rows must have the same length, and no flowers are left over. What is the maximum number of flowers per row?",
        answer,
        f"Maximum = GCD({A},{B}) = {answer}",
        "gcd_gardener"
    )

# LCM buses — cap at 12, ensure shared factor for smaller LCM
for _ in range(N_EACH):
    A = random.randint(4, 12)
    B = random.randint(4, 12)
    while B == A or lcm(A, B) > 60:
        B = random.randint(4, 12)
    answer = lcm(A, B)
    add(
        f"Two buses leave a station at the same time. Bus A comes every {A} minutes and Bus B comes every {B} minutes. After how many minutes will both buses arrive at the station at the same time again?",
        answer,
        f"LCM({A},{B}) = {answer} minutes.",
        "lcm_buses"
    )

# Pythagorean triples — only reliable ones
for _ in range(N_EACH):
    triples = [(3,4,5),(5,12,13),(8,15,17),(9,12,15)]
    p, q, hyp = random.choice(triples)
    add(
        f"A right triangle has legs of length {p} and {q}. What is the length of the hypotenuse?",
        hyp,
        f"hyp² = {p}² + {q}² = {p**2+q**2}. hyp = {hyp}",
        "pythagorean"
    )

# Composite area — cap numbers
for _ in range(N_EACH):
    L = random.randint(4, 8)
    W = random.randint(3, 6)
    H = random.randint(2, 4)
    if (L * H) % 2 != 0:
        H += 1
    answer = L * W + (L * H) // 2
    add(
        f"A rectangle has length {L} and width {W}. A triangle with base {L} and height {H} sits on top of it. What is the total area of the combined figure?",
        answer,
        f"Rectangle = {L}×{W} = {L*W}. Triangle = (1/2)×{L}×{H} = {L*H//2}. Total = {answer}",
        "composite_area"
    )

# Trapezoid — ensure even result
for _ in range(N_EACH):
    A = random.randint(4, 10)
    B = random.randint(A+2, 16)
    H = random.randint(3, 8)
    if (A + B) * H % 2 != 0:
        H += 1
    answer = (A + B) * H // 2
    add(
        f"A trapezoid has two parallel sides of length {A} and {B}, and a height of {H}. What is its area?",
        answer,
        f"Area = (1/2) × ({A}+{B}) × {H} = {answer}",
        "trapezoid"
    )

# Interior angles
for _ in range(N_EACH):
    N = random.randint(5, 9)
    answer = (N - 2) * 180
    add(
        f"What is the sum of the interior angles of a polygon with {N} sides?",
        answer,
        f"Sum = ({N}-2) × 180 = {answer} degrees.",
        "interior_angles"
    )

# Units digit — restrict to reliable bases
cycles = {3:[3,9,7,1], 5:[5], 6:[6], 7:[7,9,3,1], 9:[9,1]}
for _ in range(N_EACH):
    B = random.choice([3, 5, 6, 7, 9])
    E = random.randint(10, 30)
    cycle = cycles[B]
    answer = cycle[(E-1) % len(cycle)]
    add(
        f"What is the units digit of {B}^{E}?",
        answer,
        f"Units digits of powers of {B} cycle: {cycle}. Units digit = {answer}",
        "units_digit"
    )

# Divisors — explicit formula hint, simple numbers only
for _ in range(N_EACH):
    P, Q = random.sample([2, 3, 5], 2)
    A = random.randint(1, 2)
    Bexp = random.randint(1, 2)
    answer = (A+1)*(Bexp+1)
    N_val = P**A * Q**Bexp
    add(
        f"How many positive divisors does {N_val} have? (Note: {N_val} = {P}^{A} × {Q}^{Bexp}. Use the formula (a+1)×(b+1) where a and b are the exponents.)",
        answer,
        f"({A}+1)×({Bexp}+1) = {A+1}×{Bexp+1} = {answer}",
        "divisors"
    )

# Handshakes — N=4-6
for _ in range(N_EACH):
    N = random.randint(4, 6)
    answer = N * (N-1) // 2
    add(
        f"How many handshakes occur if {N} people each shake hands with every other person exactly once? Use the formula C(N,2) = N×(N-1)/2.",
        answer,
        f"C({N},2) = {N}×{N-1}/2 = {answer}",
        "handshakes"
    )

# Tournament — N=4-6
for _ in range(N_EACH):
    N = random.randint(4, 6)
    answer = N * (N-1) // 2
    add(
        f"{N} teams each play every other team exactly once. Using the formula C(N,2) = N×(N-1)/2, how many total games are played?",
        answer,
        f"C({N},2) = {N}×{N-1}/2 = {answer} games.",
        "tournament"
    )

# Circular seating — N=4-5
for _ in range(N_EACH):
    N = random.randint(4, 5)
    answer = math.factorial(N - 1)
    add(
        f"{N} people are seated at a circular table. Fix one person to remove rotational duplicates, then arrange the remaining {N-1} people. How many distinct arrangements are there?",
        answer,
        f"({N-1})! = {answer}",
        "circular_seating"
    )

# Committee — N=5-6
for _ in range(N_EACH):
    N = random.randint(5, 6)
    K = random.randint(2, 3)
    answer = math.comb(N, K)
    add(
        f"A committee of {K} people is chosen from {N} students. Using C(N,K) = N!/(K!×(N-K)!), how many committees are possible?",
        answer,
        f"C({N},{K}) = {answer}",
        "committee"
    )

# Binary strings — length 3-4 only
for _ in range(N_EACH):
    N = random.randint(3, 4)
    K = random.randint(1, N-1)
    answer = math.comb(N, K)
    add(
        f"A binary string of length {N} has exactly {K} ones and the rest zeros. Use C({N},{K}) to count how many such strings exist.",
        answer,
        f"C({N},{K}) = {answer}",
        "binary_string"
    )

# Passcode
for _ in range(N_EACH):
    N = random.randint(2, 3)
    M = random.randint(3, 5)
    answer = M ** N
    add(
        f"A passcode uses {N} digits, each chosen from 1 to {M}, and repetition is allowed. How many passcodes are possible?",
        answer,
        f"{M}^{N} = {answer}",
        "passcode"
    )

# Marble fraction — force clean fractions only (1/2, 1/3, 2/3, 1/4, 3/4)
clean_fractions = [(1,2),(1,3),(2,3),(1,4),(3,4)]
for _ in range(N_EACH):
    num, den = random.choice(clean_fractions)
    R = num
    B = den - num
    add(
        f"A bag contains {R} red marbles and {B} blue marbles. What fraction of the marbles are red? Simplify your answer.",
        f"{num}/{den}",
        f"Red = {R}. Total = {den}. Fraction = {num}/{den}",
        "marble_fraction"
    )

# Spinner — keep as is
for _ in range(N_EACH):
    N = random.choice([2, 3, 4, 5, 6])
    add(
        f"A spinner has {N} equal sections numbered 1 to {N}. What is the probability of landing on section 1? Write as a fraction.",
        f"1/{N}",
        f"1 out of {N} equal sections. P = 1/{N}",
        "spinner_simple"
    )

# Coin flips
for _ in range(N_EACH):
    N = random.randint(2, 3)
    K = random.randint(1, N-1)
    favorable = math.comb(N, K)
    add(
        f"You flip a fair coin {N} times. How many ways can you get exactly {K} heads? (Hint: use C({N},{K}))",
        favorable,
        f"C({N},{K}) = {favorable}",
        "coin_flips_simple"
    )

# Sum of multiples — range under 25, explicit hint
for _ in range(N_EACH):
    N = random.randint(15, 25)
    A = random.randint(2, 5)
    k = (N-1) // A
    answer = A * k * (k+1) // 2
    multiples = [str(A*i) for i in range(1, k+1)]
    add(
        f"What is the sum of all positive integers less than {N} that are divisible by {A}? (Hint: list the multiples of {A} less than {N}, then add them up)",
        answer,
        f"Multiples: {', '.join(multiples)}. Sum = {answer}",
        "sum_multiples"
    )

# Shuffle and save
random.shuffle(all_problems)

from collections import Counter
type_counts = Counter(p['skeleton_type'] for p in all_problems)
print("\nProblems by skeleton type:")
for t, c in sorted(type_counts.items()):
    print(f"  {t}: {c}")
print(f"\nTotal problems: {len(all_problems)}")

with open("/teamspace/studios/this_studio/rl-intro/main/data/skeleton_dataset_v2.json", "w") as f:
    json.dump(all_problems, f, indent=2)
print("Saved to main/data/skeleton_dataset_v2.json")
