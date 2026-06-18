# Manual Feeder-Diversity Pass (depth-1 chains)

> The ~10 "feeder-bound" depth-1 chains the autonomous campaign **structurally cannot
> calibrate** — and the human-authorized surgery to fix them. Started 2026-06-17 [faisal].
> Apply AFTER the calibration campaign finishes iter-5 (it re-runs the atom-equivalence test
> each iter; feeder edits would fail its freeze-guard mid-run). Feeder atoms are disjoint from
> the campaign's chain-layer edits, so this branch merges cleanly with the campaign's result.

## Why the campaign can't fix these

A depth-1 chain = `feeder()` produces V → V feeds a target adapter. The campaign edits the
**chain layer only** (depth-0 atoms frozen by the equivalence test). Some chains stay
too-hard / dedupe-FAIL because the **feeder atom** is the wall, and the only chain-layer levers
are exhausted. Crucially, raising feeder cardinality the obvious way — widening the feeder's
number range — is **forbidden** (§4 "difficulty via constraints, never number size"; the
KnobBank `apply_edit` hard-rejects widening any `num`-class value). So these need a **manual,
human-reviewed structural** pass that the autonomous loop is not allowed to do.

## The two kinds of feeder-bound chain (diagnosed at N=3000, not the noisy n=5 readout)

1. **Dedupe-blocked** — too-hard, but the campaign can't *ease* them because easing collapses
   the unique-problem-text survival below 0.90 (low distinct feeder sub-questions). **Fixable
   here** by adding a *structural* cardinality knob (more distinct V at the SAME number size).
   - `ordered_triple_constraint→cdc`, `alternating_cubes→multisquare`, `frobenius_stamps→telescoping`.
2. **Feeder-difficulty** — too-hard because the model can't *execute* the feeder sub-problem
   (low P(feeder-hit)); answer diversity is already fine. **Cardinality surgery does nothing**
   for these — the only structural lever is making the feeder sub-problem fewer-steps (changes
   the concept), or letting **depth-1 training** lift the model (the recursive-gap point in
   `all_experiments_retrospective.md`). Disposition: defer to post-depth-1-training re-measure.
   - `box_diagonal_sq`, `prime_power_divisors`, `lattice_points_circle`, `vieta_pair_count`,
     `polynomial_sign_intervals`, `constrained_subset_count`, the modexp-target hard chains.

## The mechanism (structural cardinality knob, num-free)

Add an `S`/`C`-class structural knob to the feeder generator that multiplies distinct V at a
fixed number range. Because the atom is deliberately changed, it **leaves the wiring-equivalence
baseline** (removed from `TARGETS` in `test_knob_equivalence.py`, following the existing
"restructured for answer-diversity" precedent) and is instead guarded by **static_checks
(dedupe/top3) + check_dataset golds**. Per concept: edit the generator + knob, update the
recomputer, drop from equivalence TARGETS, validate (golds exact + chain dedupe ≥0.90).

## Done

### `ordered_triple_constraint` ✅ (the validated template)
- **Lever:** a `parts` knob k∈{3,4} — count integer **k-tuples** `0≤a_1<…<a_k` with sum N
  (k=3 reproduces the old `_triples_gold`; k=4 is a parallel count-family at the same N∈[10,20]).
  Pure structure, no number-size change.
- **Result:** distinct-V 11→21; chain `chain_ordered_triple_constraint__constrained_digit_count`
  dedupe **0.830 FAIL → 0.905 PASS**, golds 181/181 exact (both k), top3 0.182. Equivalence test
  still PASS (17 untouched concepts byte-identical).
- **Note:** the *standalone* depth-0 atom dedupe is 0.475 — pre-existing (this atom was always
  low-cardinality standalone; this change improved it). Irrelevant: depth-0 is done/capped and
  never regenerated; the campaign gates only the chains.

### `alternating_cubes` ✅ (batch 2)
- **Lever:** a `start` index — a PARTIAL alternating-cube sum from k=start∈{1,2,3} (start=1 ==
  the old full sum). Same `top` range, parallel value-families.
- **Result:** distinct-V 17→53; chain `chain_alternating_cubes__multi_constraint_square` dedupe
  **0.955 PASS**, golds 191/191 exact, top3 0.246. (Recomputer gotcha fixed: the displayed
  "2³-1³" signs the odd bases through `ints()` → take `abs()`.)

### `frobenius_stamps` ✅ (batch 2)
- **Lever:** a `variant` ∈ {count, max} — the Sylvester **count** `(a-1)(b-1)/2` vs the Frobenius
  **number** `ab-a-b`. Two disjoint value-families at the same pair range.
- **Result:** distinct-V 22→45; chain `chain_frobenius_stamps__telescoping_mn` dedupe **0.950
  PASS**, golds 190/190 exact, top3 0.068. (Recomputer: match `largest|greatest|biggest` case-
  insensitively to pick the `max` formula.)

→ **All 3 dedupe-blocked chains fixed.**

## The ~6 feeder-difficulty chains — investigated, deliberately NOT surgered

`box_diagonal_sq→perfsq`, `prime_power_divisors→perfsq`, `lattice_points_circle→ie3`,
`vieta_pair_count→algebraic`, `polynomial_sign_intervals→algebraic`,
`constrained_subset_count→complement`.

These are too-hard because the model can't *execute* the feeder sub-problem (deep search /
factorization / enumeration), not because of cardinality. Two findings made "leave them" the
right call, not a punt:

1. **They're borderline, not deeply hard.** iter-3 means: box_diagonal 0.25, prime_power 0.25,
   polynomial_sign 0.275 (already in the loose band [0.25,0.75]); lattice 0.208, vieta 0.225,
   constrained_subset 0.229 (just below). The campaign's overall mean is still climbing
   (0.308→0.374 over iters 1–3, iters 4–5 pending), so the borderline ones likely tip in on their own.
2. **The only feeder lever would damage the concept.** Making these feeders fewer-steps (the
   only structural easing left — number size is §4-forbidden, cardinality is irrelevant to their
   hardness) would trivialize the exact compositional skill depth-1 exists to teach. That's the
   wrong trade.

**Disposition:** let the campaign finish (iters 4–5) and re-measure against the **depth-1-trained**
model — the recursive-gap point (`all_experiments_retrospective.md`): training on the ~38
calibratable chains lifts feeder execution, which is what these need. No generator surgery.
