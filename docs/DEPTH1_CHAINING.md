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

## 4. Why every current chain ends in `modular_exponent` (a real lesson)

We *tried* to vary the target (some chains ending in "count ordered triples," some in "smallest
number with D divisors"). A diversity check caught a problem: those targets **collapse** — each
intermediate maps to basically one final answer, so the answers cluster (top-3 share 27–57%,
which fails the gate). `modular_exponent` (`a^e mod m`) stays diverse even when the count `e` only
takes a few values, because `a` and `m` change every time. So **all second-wave chains feed a
count into an exponent.** Variety comes from the *eight different counting concepts* on the front
end, not from the back end. (The first-wave chains use other targets that *do* stay diverse —
see the coverage table.)

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

**Depth-1 chains (21 total).** Wave 1 = 3 (varied targets), wave 2 = 8 (count → exponent),
wave 3 = 10 (value → base):

| wave | chain (feeder → target) | feeder's intermediate → role | AMC |
|---|---|---|---|
| 1 | log_laws → ordered_triple_constraint | log value → triple-sum N | 21,47 |
| 1 | prime_power_divisors → constrained_divisor_count | smallest-N-with-D-divisors → count its divisors | 75 |
| 1 | constrained_divisor_count → modular_exponent | divisor count → exponent | 55 |
| 2 | count_obtuse_triangles → modular_exponent | count → exponent e | 18 |
| 2 | arith_term_filter → modular_exponent | count → exponent e | 72 |
| 2 | primality_in_sequence → modular_exponent | count → exponent e | 37 |
| 2 | vieta_pair_count → modular_exponent | count → exponent e | 70 |
| 2 | frobenius_stamps → modular_exponent | count → exponent e | 71 |
| 2 | geo_first_exceed → modular_exponent | index → exponent e | 7 |
| 2 | digit_count_bigprod → modular_exponent | digit count → exponent e | 60 |
| 2 | sum_of_squares → modular_exponent | count → exponent e | 7,53 |
| 3 | arith_series_sum / distinct_product_count / mean_removal / rate_closing / trapezoid_area / percent_compound / three_number_system / infinite_product_exp / vieta_sumcubes / unit_conversion_area → modular_exponent | **value V → base** (`Vᵏ mod m`) | (partner-only) |

**Why wave 3 feeds the *base* (a different pattern).** These 10 are *value*-producers — a count has
a natural role as an exponent, but an arbitrary value doesn't. They're tagged in the code as
"irreducibly one-step": a single-step problem **can't be calibrated into the goldilocks band**
(base either trivially solves it or answer-hacks it), so they're *useless as standalone atomics* and
**must** be composed to become a training signal. We feed the computed value `V` as the modexp
**base** — `Vᵏ mod m`, well-posed for any `V≥2` — because the `Vᵏ mod m` tail is high-entropy even
when the atomic `V` is thin (it fixes the diversity problem the standalone atomics had). The hand-off
is admittedly contrived (a "value" has no natural number-theory role), and these map to **partner-only
AMC that base already solves** — so wave 3 is low-AMC-value; its purpose is making these concepts
goldilocks-trainable + general multi-step practice. Gold = `pow(V,k,m)`, exact by construction (the
atomic's gold `V` is reused). `point_rotation` is excluded — its answer can be negative.

> **Verification note for wave 3:** unlike waves 1–2, these have **no `check_dataset` recomputer**
> (UNCHECKED, same as the partner atomics). Golds are construction-correct (reused atomic `V` +
> `pow`) and build-verified, but there's no durable independent text-recompute. Add recomputers if
> these ever feed a high-stakes run.

**Not yet:** 3-concept chains; goldilocks *calibration* of the chains (against the depth-0-trained
model — next milestone); wave-3 `check_dataset` recomputers; `point_rotation`.

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
