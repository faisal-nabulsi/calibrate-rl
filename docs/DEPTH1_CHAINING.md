# Depth-1 chaining — how the composite dataset works (plain-language guide)

This explains, in simple terms, how the depth-1 ("chained") problems are built: how we
decide which concepts to combine, what the knobs are, why the static gate matters, and
exactly what's new in the generator. If you've never touched this code, start here.

---

## 1. The one-sentence idea

**Depth-0** problems are *one step* ("how many divisors of 1008 are odd?" → 6).
**Depth-1** problems *chain two steps*: the answer of step A becomes a number inside
step B, so the model has to do A, carry the result, and then do B.

> *"Let e be the number of obtuse triangles with perimeter ≤ 14. What is 7^e mod 67?"*

The model must (A) count obtuse triangles → get a number `e`, then (B) compute `7^e mod 67`.
One problem, two linked skills. That "carry the number from A into B" is the skill depth-1
training teaches — and the [base diagnostic](../results/chain_depth1_base_diag_300_findings.md)
showed the base model can do the individual steps but **fails to chain them** (~88% on the
steps, ~50% on the whole). Closing that gap is the entire point.

---

## 2. The anatomy of a chain

Every chain is `A → B`: **A is the "feeder"** (it produces a number), **B is the "target"**
(that number is plugged into one of B's inputs).

```
   concept A           the number             concept B
 (count obtuse   ──►   e = 6 (the      ──►   (a^e mod m)   ──►  final answer
  triangles)           "intermediate")
```

- **intermediate** = the number A produces that gets fed into B (here, `e = 6`). We store it
  in the problem's metadata as `intermediate_gold` so we can later check whether the model
  computed it correctly (that's how the composition-gap diagnostic works).
- **embed, don't announce.** The problem text *embeds* A as a sub-question ("Let e be the
  number of …") — it never says "first do A, then do B." The model has to *realize* it needs
  the intermediate. That's what makes it a real chaining test instead of two separate questions.
- **the gold is exact by construction.** We don't guess the answer. A's code computes the
  intermediate, B's code computes the final from it — both are the same trusted "oracles" the
  depth-0 generators already use, just run back-to-back. Compose two correct steps → correct answer.

---

## 3. How we decide which two concepts to combine

Not every pair makes a sensible chain. A pair has to clear **three filters**, in order:

**Filter 1 — is it *feed-legal*? (mechanical, automated)**
A's answer has to *fit* into B's input. Example: if A usually answers 6–20 and B's input
("the exponent e") only accepts 4–20, that's a legal feed. If A answers in the thousands and
B wants a small exponent, it's illegal.
We compute this automatically for **every** (A, B, input) combination and save it as the
**compatibility map** (`build_chain_compat.py` → `chain_compat_v*.json`). It's purely
mechanical — it only checks whether the *numbers* line up, using each concept's knob ranges +
a sample of A's answers. **No model, no GPU.** It also rejects feeds where A only ever produces
a handful of distinct values (that would make a boring, answer-hackable chain).

**Filter 2 — is it *natural*? (human judgment)**
Feed-legal is necessary but **not** sufficient. The map will happily tell you "feed the sum of
two cube-roots into a percentage problem's starting dollar amount" is legal — but that's a
*contrived staple*, not real reasoning. We only build chains where the hand-off *means*
something: "a **count** becomes an **exponent**," "the **smallest number with D divisors** then
gets its **divisors counted**." This is a judgment call and it's why we don't auto-build every
legal pair (there are hundreds).

**Filter 3 — does it keep answers *diverse*? (the static gate, automated)**
Even a natural chain can be bad if the final answers cluster on a few values (the model can then
"guess 5" and be right too often). We measure this and reject anything where the top-3 answers
are too common. See §6.

---

## 4. The diversity rule: multi-input targets (not "everything ends in modexp")

An earlier design fed every chain into `modular_exponent`, because the first targets we tried
(count-ordered-triples, smallest-number-with-D-divisors) **collapse** — each intermediate maps to
basically one final answer, so the answers cluster (top-3 27–57%, gate fail). But modexp isn't
special. The real rule:

> **A target stays answer-diverse iff it is MULTI-INPUT.** Feed the intermediate `V` into *one* of
> the target's inputs and let its *other* inputs supply independent entropy. Single-input targets
> (cdc-count, ordered-triple, ppd, …) collapse because the one fed value determines the answer.

`modular_exponent` works because `Vᵏ mod m` has the modulus + other base as free entropy — but so do
plenty of concepts. `tools/scan_chain_targets.py` measures this empirically and the current chain set
spreads the final step across **9 distinct target concepts** (modexp is now only the *fallback* for the
few feeders whose output fits no other target's envelope). The menu, with the input we feed:

| target | fed input | free entropy from |
|---|---|---|
| algebraic_system_2eq | `x` (one unknown) | the other two unknowns `y,z` |
| inclusion_exclusion_3set | range bound `U` | the divisor triple `a,b,c` |
| perfect_square_divisible | `limit` | the divisor `div` |
| telescoping_mn | term count `N` | the gap |
| constrained_digit_count | digit-sum target | the range `[lo,hi]` |
| equalization_fraction | #glasses `g` | the fill fraction |
| complement_prob_mn | #die faces | the threshold |
| multi_constraint_square | `limit` | divisor + last-digit |
| modular_exponent | base / exponent | the other base + modulus (fallback) |

---

## 5. The "combine 3 skeletons" idea (3-concept chains)

A 2-concept chain is `A → B`. A **3-concept chain** is `A → B → C`: A's answer feeds B, B's answer
feeds C — two hand-offs, so it stresses chaining even harder. Example sketch: "count something →
use it as an exponent → count the divisors of *that* result."

We've **deliberately not built these yet.** Reasons: they're harder to make natural, harder to
keep diverse, and we wanted to prove 2-concept chains transfer first (the §6a "validate then
scale" discipline). The metadata is already shaped to allow 3-way chains later, and AMC #55's
full decomposition (modexp × cdc × divisor_sum_filter) is the obvious first 3-way target.

---

## 6. Knobs — the difficulty dials

A "knob" is a tunable number (or list) pulled *out* of the generator code into a small JSON file
(`automation/calibrator/knobs/<concept>.json`), so difficulty can be adjusted **without editing
code**. Each knob says: its current value/range, its type, a hard *envelope* it can never exceed,
and a **class**:

| class | meaning | can it be made bigger? |
|---|---|---|
| **num** | a raw number size (a base, a bound, a coordinate) | **No** — widening is *blocked* |
| **C** | a count of steps/constraints (how many terms, how many divisors) | Yes, within the envelope |
| **S** | a structure/method switch (which operation, which phrasing) | Yes, within the envelope |

The golden rule (CLAUDE.md §4): **make problems harder by adding steps/constraints, never by
using bigger numbers.** Big numbers just make tedious problems the model fails for the wrong
reason. The code *enforces* this — try to widen a `num` knob and it errors out. A chain's knob
file simply holds the knobs of *both* concepts it combines (plus which input is fed).

---

## 7. The static gate — and why it's non-negotiable

The golds are **generated by code**, so a single generator bug = training the model on **wrong
answers**, and nothing downstream can recover from that. The static gate is the safety net. It
checks, with **no model involved**:

1. **Golds are correct** — an *independent* recomputer re-derives the answer straight from the
   problem text and compares. (Every chain has one in `prep/check_dataset.py`.) Mismatch = bad data.
2. **No duplicates / no conflicts** — the same question never carries two different answers.
3. **Answers are diverse** — top-3 answer share ≤ 0.30, and enough distinct answers (not
   answer-hackable).
4. **Draw-equivalence** (for knob-wiring): the same random seed produces the *exact same* problem
   as before the knobs were pulled out — proof we didn't accidentally change anything.

**Yes, it's important.** It's the difference between "we think the data is right" and "we proved
it." The second-wave chains passed it 480/480 golds, 0 conflicts, top-3 0.09–0.16.

---

## 8. What's new in the generator (checklist)

If you're reading the code, here's everything depth-1 added on top of the depth-0 generators:

- **`@concept("chain_A__B", [amc])`** — composite generators, named `chain_<feeder>__<target>`.
- **Oracle composition** — call A's answer-function, then B's, back-to-back (gold exact).
- **Feed-gate** — `_parent_envelope(B, input)` reads B's legal range and rejects/re-samples if
  A's answer doesn't fit. Never hard-coded.
- **Embed-not-announce** surface text (the model must discover the sub-step).
- **`intermediate_gold`** in metadata (enables the composition-gap measurement).
- **Knob files per chain** (hold both concepts' knobs) + the shared `knob_loader`.
- **Recomputers** in `check_dataset.py` (independent gold check, per chain).
- **Equivalence fixture/test** for any knob-wiring (byte-identical before/after).

---

## 9. What's covered today

**Depth-1 chains (47 total) — one per concept, maximally diverse.** Every one of the 47 concepts
(28 depth-0 atomics + 19 partners) appears as a **feeder** exactly once, and the final step is spread
across **9 distinct target concepts** (§4 menu). modexp is now only **5/47 (11%)** — the fallback for
the 5 feeders whose output fits no other target's envelope (`modular_exponent, infinite_product_exp,
mean_removal, point_rotation, distinct_product_count`).

Built by one factory in `generate/skeleton_injector_v12.py` (`_register_diverse_chain` + the `_ADAPT`
target adapters + the `_DIVERSE_CHAINS` feeder→target map). Final-step distribution:

| target concept | # chains |
|---|---|
| algebraic_system_2eq | 7 |
| inclusion_exclusion_3set | 7 |
| perfect_square_divisible | 6 |
| modular_exponent | 6 |
| telescoping_mn | 6 |
| constrained_digit_count | 5 |
| equalization_fraction | 5 |
| complement_prob_mn | 4 |
| multi_constraint_square | 1 |

*(Counts are AFTER the self-chain reassignment, which shifted 4 targets: algebraic 8→7, modexp 5→6, telescoping 5→6, complement 5→4. Sum = 47.)*

**Verification** (`tools/verify_diverse_chains.py`): 47/47 chains pass — **0 gold mismatches, 0 unparsed**,
top-3 ≤ 0.30, full feeder coverage. Golds are construction-correct (feeder's own oracle `V` → target
oracle) *and* independently text-recomputed from the target clause + the stored `intermediate_gold`.

**AMC-targeting dropped by design.** The old set hand-picked #55/#75 directions; this set optimizes
*diversity + coverage* (general composition is the goal — depth-0/AMC is capped, §0). Chains carry no
AMC tag. The assignment is reproducible via `tools/scan_chain_targets.py`.

**Deferred (same as before):** per-chain `knobs/*.json` wiring and the `check_dataset` recomputers
(the build-time recompute in `verify_diverse_chains.py` is the current gold gate); goldilocks
*calibration* against the depth-0-trained model (curriculum-gated); 3-concept chains.

---

## 10. How to add a new chain (short recipe)

1. Pick a feeder A and target B where (a) the compat map says feed-legal, (b) the hand-off is
   *natural*, (c) the target keeps answers diverse (prefer modexp for count-feeders).
2. Add `automation/calibrator/knobs/chain_A__B.json` (both concepts' knobs + `fed_param`).
3. Add the `@concept("chain_A__B", …)` generator: draw A's params → compute intermediate →
   feed-gate → draw B's params → compute final → embed-not-announce text → `intermediate_gold` meta.
4. Add a recomputer to `prep/check_dataset.py` and register it.
5. Run `static_checks.py --concept chain_A__B` and `check_dataset.py` on a sample pool — both must pass.

---

## Files
- Generators + oracles: `generate/skeleton_injector_v12.py` (search `DEPTH-1 CHAINING`)
- Knobs: `automation/calibrator/knobs/chain_*.json` · loader: `automation/calibrator/knob_loader.py`
- Compatibility map: `automation/calibrator/build_chain_compat.py`
- Gold recomputers / static gate: `prep/check_dataset.py`, `automation/calibrator/static_checks.py`
- Why-these-chains rationale: `CLAUDE.md` §6 / §6a · base diagnostic: `results/chain_depth1_base_diag_300_findings.md`
