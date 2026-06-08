import random
import json
import math

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    return a * b // gcd(a, b)

def generate_all():
    problems = []

    # Skeleton 2 - Row arrangements
    for _ in range(200):
        N = random.randint(4, 8)
        answer = math.factorial(N - 2)
        problem = f"{N} students are seated in a row. In how many ways can they be arranged if student A must sit in the first seat and student B must sit in the last seat?"
        reasoning = f"Fix A in seat 1 and B in seat {N}. The remaining {N-2} students fill the middle seats in ({N-2})! = {answer} ways."
        problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    # Skeleton 4 - Pizza toppings
    for _ in range(200):
        N = random.randint(6, 10)
        K = random.randint(2, 3)
        answer = math.comb(N, K)
        problem = f"A pizza shop offers {N} toppings. How many distinct {K}-topping pizzas can be made if no topping is repeated?"
        reasoning = f"Order doesn't matter, no repetition. C({N},{K}) = {N}!/({K}!×{N-K}!) = {answer}"
        problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    # Skeleton 9 - Circular seating
    for _ in range(200):
        N = random.randint(4, 7)
        answer = math.factorial(N - 1)
        problem = f"{N} people are seated at a circular table. How many distinct seating arrangements are there (rotations are considered identical)?"
        reasoning = f"Fix one person to eliminate rotations. Arrange the remaining {N-1} people: ({N-1})! = {answer}"
        problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    # Skeleton 12 - Passcode with repetition
    for _ in range(200):
        N = random.randint(2, 4)
        M = random.randint(5, 9)
        answer = M ** N
        problem = f"A passcode uses {N} digits selected from 1 to {M} where repetition is allowed. How many passcodes are possible?"
        reasoning = f"Each of the {N} positions has {M} choices independently. Total = {M}^{N} = {answer}"
        problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    # Skeleton 16 - Binary strings
    for _ in range(200):
        N = random.randint(5, 8)
        K = random.randint(1, N-1)
        answer = math.comb(N, K)
        problem = f"A binary string of length {N} is formed using only 0s and 1s. How many such strings contain exactly {K} ones?"
        reasoning = f"Choose which {K} of the {N} positions hold a 1. C({N},{K}) = {answer}"
        problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    # Skeleton 17 - Marble probability
    for _ in range(200):
        R = random.randint(2, 8)
        B = random.randint(2, 8)
        total = R + B
        g = gcd(R, total)
        num = R // g
        den = total // g
        problem = f"A bag contains {R} red marbles and {B} blue marbles. If one marble is drawn at random, what is the probability it is red? Express as a fraction in lowest terms."
        reasoning = f"Total marbles = {total}. P(red) = {R}/{total} = {num}/{den}"
        problems.append({"problem": problem, "answer": f"{num}/{den}", "reasoning": reasoning})

    # Skeleton 21 - Spinner
    for _ in range(200):
        N = random.randint(6, 12)
        T = random.randint(N//2, N-2)
        answer_num = N - T
        g = gcd(answer_num, N)
        problem = f"A spinner has {N} equal sections numbered 1 through {N}. What is the probability that a spin lands on a number greater than {T}?"
        reasoning = f"Numbers greater than {T}: there are {N}-{T} = {N-T} such numbers. P = {N-T}/{N} = {answer_num//g}/{N//g}"
        problems.append({"problem": problem, "answer": f"{answer_num//g}/{N//g}", "reasoning": reasoning})

    # Skeleton 28 - Coin flips
    for _ in range(200):
        N = random.randint(4, 7)
        K = random.randint(1, N-1)
        favorable = math.comb(N, K)
        total = 2 ** N
        g = gcd(favorable, total)
        problem = f"You flip a fair coin {N} times. What is the probability of getting exactly {K} heads?"
        reasoning = f"Total outcomes = 2^{N} = {total}. Favorable = C({N},{K}) = {favorable}. P = {favorable}/{total} = {favorable//g}/{total//g}"
        problems.append({"problem": problem, "answer": f"{favorable//g}/{total//g}", "reasoning": reasoning})

    # Skeleton 37 - Units digit
    cycles = {2:[2,4,8,6], 3:[3,9,7,1], 4:[4,6], 5:[5], 6:[6], 7:[7,9,3,1], 8:[8,4,2,6], 9:[9,1]}
    for _ in range(200):
        B = random.randint(2, 9)
        E = random.randint(10, 30)
        cycle = cycles[B]
        answer = cycle[(E-1) % len(cycle)]
        problem = f"What is the units digit of {B}^{E}?"
        reasoning = f"The units digits of powers of {B} cycle: {cycle}. Cycle length = {len(cycle)}. {E} mod {len(cycle)} = {E % len(cycle) if E % len(cycle) != 0 else len(cycle)}. Units digit = {answer}"
        problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    # Skeleton 40 - Number of divisors
    primes = [2, 3, 5, 7, 11]
    for _ in range(200):
        P, Q = random.sample(primes[:4], 2)
        A = random.randint(1, 4)
        B = random.randint(1, 3)
        answer = (A+1)*(B+1)
        N = P**A * Q**B
        problem = f"How many positive divisors does {N} have? (Note: {N} = {P}^{A} × {Q}^{B})"
        reasoning = f"Divisor count formula: ({A}+1)×({B}+1) = {A+1}×{B+1} = {answer}"
        problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    # Skeleton 41 - Sum of multiples
    for _ in range(200):
        N = random.randint(50, 100)
        A = random.randint(3, 9)
        k = (N-1) // A
        answer = A * k * (k+1) // 2
        problem = f"What is the sum of all positive integers less than {N} that are divisible by {A}?"
        reasoning = f"Multiples of {A} less than {N}: {A}, {2*A}, ..., {k*A}. k = {k}. Sum = {A} × {k}×{k+1}/2 = {answer}"
        problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    # Skeleton 43 - Composite area
    for _ in range(200):
        L = random.randint(4, 12)
        W = random.randint(3, 8)
        H = random.randint(2, 6)
        answer_num = 2*L*W + L*H
        answer = answer_num / 2
        if answer_num % 2 != 0:
            continue
        answer = answer_num // 2
        problem = f"A rectangle has length {L} and width {W}. A triangle with base {L} and height {H} sits on top of it. What is the total area of the combined figure?"
        reasoning = f"Rectangle area = {L}×{W} = {L*W}. Triangle area = (1/2)×{L}×{H} = {L*H//2}. Total = {L*W} + {L*H//2} = {answer}"
        problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    # Skeleton 45 - Pythagorean theorem
    triples = [(3,4,5),(5,12,13),(8,15,17),(7,24,25),(6,8,10),(9,12,15),(12,16,20)]
    for _ in range(200):
        P, Q, hyp = random.choice(triples)
        problem = f"A right triangle has legs of length {P} and {Q}. What is the length of the hypotenuse?"
        reasoning = f"Pythagorean theorem: hyp² = {P}² + {Q}² = {P**2} + {Q**2} = {P**2+Q**2}. hyp = √{P**2+Q**2} = {hyp}"
        problems.append({"problem": problem, "answer": str(hyp), "reasoning": reasoning})

    return problems

new_problems = generate_all()
print(f"New problems generated: {len(new_problems)}")

# Load existing and combine
with open('/teamspace/studios/this_studio/rl-intro/main/data/skeleton_dataset.json') as f:
    existing = json.load(f)

all_problems = existing + new_problems
random.shuffle(all_problems)

with open('/teamspace/studios/this_studio/rl-intro/main/data/skeleton_dataset.json', 'w') as f:
    json.dump(all_problems, f, indent=2)

print(f"Total problems in dataset: {len(all_problems)}")
