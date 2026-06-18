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

## Next (same template)

- `alternating_cubes→multi_constraint_square` and `frobenius_stamps→telescoping_mn` — the other
  two dedupe-blocked chains. Their cardinality is less extreme (distV 17 / 22) and the chain
  issue is easing-collapse, so assess whether a structural feeder knob or a target-side
  diversity lever is the cleaner fix before editing.
- Feeder-difficulty set: **do not** cardinality-surgery; re-measure against the depth-1-trained
  model once the first depth-1 run lands.
