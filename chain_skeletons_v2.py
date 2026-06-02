import random
import json
import math

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    return a * b // gcd(a, b)

problems = []

def add(problem, answer, reasoning, chain_type):
    problems.append({
        "problem": problem,
        "answer": str(answer),
        "reasoning": reasoning,
        "chain_type": chain_type,
        "depth": 1
    })

N_EACH = 100
TRIPLES = [(3,4,5),(5,12,13),(8,15,17),(9,12,15)]

# ── CHAIN 1: GCD → Pythagorean ─────────────────────────────────────────
# Find GCD, use it as a leg of a known triple
for _ in range(N_EACH):
    A = random.randint(12, 30)
    B = random.randint(12, 30)
    g = gcd(A, B)
    # Pick a triple where one leg equals g
    valid = [(p,q,h) for p,q,h in TRIPLES if p == g or q == g]
    if not valid:
        # fallback: use 3,4,5 scaled if g is small enough
        if g <= 5:
            p,q,h = 3*g, 4*g, 5*g
        else:
            continue
    else:
        p,q,h = random.choice(valid)
    other_leg = q if p == g else p
    answer = h
    add(
        f"A gardener wants to plant {A} roses and {B} tulips in equal rows. "
        f"First find the maximum row length (GCD of {A} and {B}). "
        f"Then use that number as one leg of a right triangle with other leg {other_leg}. "
        f"What is the hypotenuse?",
        answer,
        f"Step 1: GCD({A},{B}) = {g}. Step 2: hyp = sqrt({g}²+{other_leg}²) = {h}.",
        "gcd_into_pythagorean"
    )

# ── CHAIN 2: GCD → Interior Angles ─────────────────────────────────────
# Find GCD, add 2 to get polygon sides
for _ in range(N_EACH):
    A = random.randint(12, 30)
    B = random.randint(12, 30)
    g = gcd(A, B)
    sides = g + 2
    if sides < 3 or sides > 12:
        continue
    angle_sum = (sides - 2) * 180
    add(
        f"A gardener has {A} roses and {B} tulips. "
        f"Find the GCD of {A} and {B}. "
        f"Add 2 to get the number of sides of a polygon. "
        f"What is the sum of the interior angles?",
        angle_sum,
        f"Step 1: GCD({A},{B}) = {g}. Step 2: sides = {g}+2 = {sides}. Step 3: ({sides}-2)×180 = {angle_sum}°.",
        "gcd_into_polygon"
    )

# ── CHAIN 3: GCD → Tournament ───────────────────────────────────────────
# Find GCD, use as number of teams
for _ in range(N_EACH):
    A = random.randint(12, 30)
    B = random.randint(12, 30)
    g = gcd(A, B)
    if g < 4 or g > 8:
        continue
    games = g * (g-1) // 2
    add(
        f"A gardener has {A} roses and {B} tulips. "
        f"Find the GCD of {A} and {B}. "
        f"That many teams compete in a tournament where every team plays every other team once. "
        f"Using C(N,2) = N×(N-1)/2, how many games are played?",
        games,
        f"Step 1: GCD({A},{B}) = {g}. Step 2: C({g},2) = {g}×{g-1}/2 = {games} games.",
        "gcd_into_tournament"
    )

# ── CHAIN 4: Pythagorean → Committee ────────────────────────────────────
# Find hypotenuse, use as group size for committee
for _ in range(N_EACH):
    p, q, hyp = random.choice(TRIPLES)
    K = random.randint(2, 3)
    if hyp < K + 2:
        continue
    N = min(hyp, 8)  # cap at 8 to keep goldilocks
    answer = math.comb(N, K)
    add(
        f"A right triangle has legs {p} and {q}. Find the hypotenuse. "
        f"Then choose a committee of {K} people from that many students "
        f"using C(N,K) = N!/(K!×(N-K)!). How many committees are possible?",
        answer,
        f"Step 1: hyp = {hyp}. Step 2: C({N},{K}) = {answer}.",
        "pythagorean_into_committee"
    )

# ── CHAIN 5: Pythagorean → LCM ──────────────────────────────────────────
# Find hypotenuse, find LCM with another number
for _ in range(N_EACH):
    p, q, hyp = random.choice(TRIPLES)
    B = random.randint(4, 12)
    while B == hyp:
        B = random.randint(4, 12)
    L = lcm(hyp, B)
    if L > 100:
        continue
    add(
        f"A right triangle has legs {p} and {q}. Find the hypotenuse. "
        f"Then find the LCM of the hypotenuse and {B}.",
        L,
        f"Step 1: hyp = {hyp}. Step 2: LCM({hyp},{B}) = {L}.",
        "pythagorean_into_lcm"
    )

# ── CHAIN 6: LCM → Tournament ───────────────────────────────────────────
# Find LCM, use units digit as number of teams
for _ in range(N_EACH):
    A = random.randint(4, 10)
    B = random.randint(4, 10)
    while B == A:
        B = random.randint(4, 10)
    L = lcm(A, B)
    if L > 60:
        continue
    units = L % 10
    if units < 4 or units > 8:
        continue
    games = units * (units-1) // 2
    add(
        f"Two buses meet every {A} and {B} minutes. Find the LCM. "
        f"Use the units digit of the LCM as the number of teams in a tournament "
        f"where every team plays every other team once using C(N,2). "
        f"How many games are played?",
        games,
        f"Step 1: LCM({A},{B}) = {L}. Step 2: units digit = {units}. Step 3: C({units},2) = {games}.",
        "lcm_into_tournament"
    )

# ── CHAIN 7: Handshakes → Divisors ──────────────────────────────────────
# Find handshakes, count divisors
for _ in range(N_EACH):
    N = random.randint(4, 7)
    handshakes = N * (N-1) // 2
    divisors = sum(1 for i in range(1, handshakes+1) if handshakes % i == 0)
    add(
        f"{N} people each shake hands with every other person exactly once. "
        f"Use C(N,2) = N×(N-1)/2 to find total handshakes. "
        f"Then count how many positive divisors that number has.",
        divisors,
        f"Step 1: C({N},2) = {handshakes} handshakes. Step 2: divisors of {handshakes} = {divisors}.",
        "handshakes_into_divisors"
    )

# ── CHAIN 8: Tournament → Interior Angles ───────────────────────────────
# Find games played, use games+2 as polygon sides
for _ in range(N_EACH):
    N = random.randint(4, 6)
    games = N * (N-1) // 2
    sides = games + 2
    if sides < 5 or sides > 10:
        continue
    angle_sum = (sides - 2) * 180
    add(
        f"{N} teams compete where every team plays every other team once. "
        f"Find total games using C(N,2) = N×(N-1)/2. "
        f"Add 2 to get the number of sides of a polygon. "
        f"What is the sum of its interior angles?",
        angle_sum,
        f"Step 1: C({N},2) = {games} games. Step 2: sides = {games}+2 = {sides}. Step 3: ({sides}-2)×180 = {angle_sum}°.",
        "tournament_into_polygon"
    )

# ── CHAIN 9: Committee → Trapezoid ──────────────────────────────────────
# Find committees, use as sum of parallel sides
for _ in range(N_EACH):
    N = random.randint(5, 7)
    K = random.randint(2, 3)
    committees = math.comb(N, K)
    H = random.randint(2, 6)
    if (committees * H) % 2 != 0:
        H += 1
    area = committees * H // 2
    add(
        f"A committee of {K} people is chosen from {N} students using C(N,K). "
        f"How many committees are possible? "
        f"Use that as the sum of the two parallel sides of a trapezoid with height {H}. "
        f"What is the area?",
        area,
        f"Step 1: C({N},{K}) = {committees}. Step 2: area = ({committees}×{H})/2 = {area}.",
        "committee_into_trapezoid"
    )

# ── CHAIN 10: Units Digit → Passcode ────────────────────────────────────
# Find units digit, use as pool size for passcode
for _ in range(N_EACH):
    cycles = {3:[3,9,7,1], 5:[5], 6:[6], 7:[7,9,3,1], 9:[9,1]}
    B = random.choice([3,5,6,7,9])
    E = random.randint(10, 20)
    cycle = cycles[B]
    units = cycle[(E-1) % len(cycle)]
    if units < 3 or units > 6:
        continue
    N_digits = random.randint(2, 3)
    passcodes = units ** N_digits
    add(
        f"Find the units digit of {B}^{E}. "
        f"Use that as the pool size for a {N_digits}-digit passcode where repetition is allowed. "
        f"How many passcodes are possible?",
        passcodes,
        f"Step 1: units digit of {B}^{E} = {units}. Step 2: {units}^{N_digits} = {passcodes} passcodes.",
        "units_digit_into_passcode"
    )

# ── COMBINE WITH V2 SIMPLE SKELETONS ────────────────────────────────────
random.shuffle(problems)

with open('/teamspace/studios/this_studio/rl-intro/main/data/skeleton_dataset_v2.json') as f:
    simple = json.load(f)
for p in simple:
    p['depth'] = 0

all_problems = simple + problems
random.shuffle(all_problems)

from collections import Counter
chain_counts = Counter(p['chain_type'] for p in problems)
print("\nChained problems by type:")
for t, c in sorted(chain_counts.items()):
    print(f"  {t}: {c}")

print(f"\nSimple (depth 0): {len(simple)}")
print(f"Chained (depth 1): {len(problems)}")
print(f"Total: {len(all_problems)}")

with open('/teamspace/studios/this_studio/rl-intro/main/data/chained_dataset_v2.json', 'w') as f:
    json.dump(all_problems, f, indent=2)
print("Saved to main/data/chained_dataset_v2.json")
