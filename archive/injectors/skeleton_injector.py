import random
import json
import math

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    return a * b // gcd(a, b)

def generate_problem(skeleton_id, n_samples=100):
    problems = []
    
    if skeleton_id == 1:  # Committee selection
        for _ in range(n_samples):
            N = random.randint(6, 12)
            K = random.randint(2, min(4, N-1))
            answer = math.comb(N, K)
            problem = f"A committee of {K} people is to be chosen from a group of {N} students. How many different committees are possible?"
            reasoning = f"This is a combination problem since order does not matter.\nC({N},{K}) = {N}! / ({K}! × {N-K}!) = {answer}"
            problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})
    
    elif skeleton_id == 3:  # Handshakes
        for _ in range(n_samples):
            N = random.randint(4, 10)
            answer = N * (N-1) // 2
            problem = f"How many ways can {N} people shake hands so that every person shakes hands with every other person exactly once?"
            reasoning = f"Each handshake is a pair of people. Count pairs: C({N},2) = {N}×{N-1}/2 = {answer}"
            problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    elif skeleton_id == 5:  # Tournament games
        for _ in range(n_samples):
            N = random.randint(4, 9)
            answer = N * (N-1) // 2
            problem = f"{N} teams compete in a tournament where every team plays every other team exactly once. How many total games are played?"
            reasoning = f"Each game involves 2 teams. Number of games = C({N},2) = {N}×{N-1}/2 = {answer}"
            problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    elif skeleton_id == 31:  # LCM buses
        for _ in range(n_samples):
            A = random.randint(4, 20)
            B = random.randint(4, 20)
            while B == A:
                B = random.randint(4, 20)
            answer = lcm(A, B)
            problem = f"Two buses leave a station at the same time. Bus A comes every {A} minutes and Bus B comes every {B} minutes. After how many minutes will both buses arrive at the station at the same time again?"
            reasoning = f"The buses meet again at LCM({A},{B}).\nLCM = {answer} minutes."
            problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    elif skeleton_id == 32:  # GCD gardener
        for _ in range(n_samples):
            A = random.randint(12, 60)
            B = random.randint(12, 60)
            answer = gcd(A, B)
            problem = f"A gardener wants to plant {A} roses and {B} tulips in rows, with each row containing only one type of flower. All rows must have the same length, and no flowers are left over. What is the maximum number of flowers per row?"
            reasoning = f"The row length must divide both {A} and {B}. Maximum = GCD({A},{B}) = {answer}"
            problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    elif skeleton_id == 47:  # Interior angles
        for _ in range(n_samples):
            N = random.randint(5, 9)
            answer = (N - 2) * 180
            problem = f"What is the sum of the interior angles of a polygon with {N} sides?"
            reasoning = f"Sum of interior angles = (N-2) × 180 = ({N}-2) × 180 = {N-2} × 180 = {answer} degrees."
            problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    elif skeleton_id == 46:  # Trapezoid area
        for _ in range(n_samples):
            A = random.randint(4, 10)
            B = random.randint(A+2, 18)
            H = random.randint(3, 8)
            answer = (A + B) * H // 2
            if (A + B) * H % 2 != 0:
                continue
            problem = f"A trapezoid has two parallel sides of length {A} and {B}, and a height of {H}. What is its area?"
            reasoning = f"Area = (1/2) × (sum of parallel sides) × height = (1/2) × ({A}+{B}) × {H} = (1/2) × {A+B} × {H} = {answer}"
            problems.append({"problem": problem, "answer": str(answer), "reasoning": reasoning})

    return problems

# Generate dataset
all_problems = []
skeleton_ids = [1, 3, 5, 31, 32, 47, 46]

for sid in skeleton_ids:
    problems = generate_problem(sid, n_samples=200)
    all_problems.extend(problems)
    print(f"Skeleton {sid}: generated {len(problems)} problems")

random.shuffle(all_problems)

# Save dataset
with open("/teamspace/studios/this_studio/rl-intro/main/data/skeleton_dataset.json", "w") as f:
    json.dump(all_problems, f, indent=2)

print(f"\nTotal problems generated: {len(all_problems)}")
print("Saved to main/data/skeleton_dataset.json")
