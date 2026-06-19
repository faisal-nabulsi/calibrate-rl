# depth-1 calibration readout — 500 rows, 46 chains
in-band chains: **31/46** | mean goldilocks-frac: 0.08

flagged (need edits): **15**

| chain | n | mean | gold% | too_hard | too_easy | top3 | verdict | direction |
|---|--|--|--|--|--|--|--|---|
| chain_arith_series_sum__constrained_digit_count | 10 | 0.188 | 0.1 | 0.7 | 0.1 | 0.225 | TOO_HARD | ease (fewer steps/constraints); don't over-ease past 0.75 |
| chain_count_obtuse_triangles__equalization_fraction | 7 | 0.036 | 0.0 | 0.714 | 0.0 | 0.25 | TOO_HARD | ease (fewer steps/constraints); don't over-ease past 0.75 |
| chain_distinct_product_count__modular_exponent | 7 | 0.179 | 0.0 | 0.714 | 0.0 | 0.125 | TOO_HARD | ease (fewer steps/constraints); don't over-ease past 0.75 |
| chain_frobenius_stamps__telescoping_mn | 12 | 0.0 | 0.0 | 1.0 | 0.0 | 0.15 | TOO_HARD | ease (fewer steps/constraints); don't over-ease past 0.75 |
| chain_lattice_points_circle__inclusion_exclusion_3set | 7 | 0.125 | 0.0 | 0.857 | 0.0 | 0.25 | TOO_HARD | ease (fewer steps/constraints); don't over-ease past 0.75 |
| chain_log_laws__complement_prob_mn | 15 | 0.55 | 0.133 | 0.067 | 0.267 | 0.325 | LOW_DIVERSITY | diversify the non-fed inputs; if feeder-capped (few distinct V), FLAG for human feeder-pass |
| chain_mean_removal__modular_exponent | 12 | 0.906 | 0.0 | 0.0 | 0.667 | 0.175 | TOO_EASY | harden (more steps/constraints) |
| chain_ordered_triple_constraint__box_diagonal_sq | 15 | 0.175 | 0.067 | 0.467 | 0.0 | 0.1 | TOO_HARD | ease (fewer steps/constraints); don't over-ease past 0.75 |
| chain_percent_compound__algebraic_system_2eq | 11 | 0.864 | 0.0 | 0.0 | 0.455 | 0.225 | TOO_EASY | harden (more steps/constraints) |
| chain_perfect_square_divisible__telescoping_mn | 15 | 0.217 | 0.0 | 0.733 | 0.133 | 0.15 | TOO_HARD | ease (fewer steps/constraints); don't over-ease past 0.75 |
| chain_rate_closing__telescoping_mn | 7 | 0.089 | 0.0 | 0.714 | 0.0 | 0.175 | TOO_HARD | ease (fewer steps/constraints); don't over-ease past 0.75 |
| chain_roots_of_unity_sum__equalization_fraction | 12 | 0.125 | 0.0 | 0.25 | 0.0 | 0.275 | TOO_HARD | ease (fewer steps/constraints); don't over-ease past 0.75 |
| chain_sum_of_squares__complex_modulus_power | 9 | 0.083 | 0.0 | 0.667 | 0.0 | 0.1 | TOO_HARD | ease (fewer steps/constraints); don't over-ease past 0.75 |
| chain_vieta_pair_count__complex_modulus_power | 13 | 0.01 | 0.0 | 0.923 | 0.0 | 0.154 | TOO_HARD | ease (fewer steps/constraints); don't over-ease past 0.75 |
| chain_vieta_sumcubes__inclusion_exclusion_3set | 12 | 0.979 | 0.0 | 0.0 | 0.833 | 0.1 | TOO_EASY | harden (more steps/constraints) |
| chain_algebraic_system_2eq__modular_exponent | 9 | 0.722 | 0.0 | 0.111 | 0.444 | 0.075 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_alternating_cubes__multi_constraint_square | 9 | 0.389 | 0.222 | 0.222 | 0.0 | 0.2 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_arith_term_filter__constrained_digit_count | 10 | 0.5 | 0.1 | 0.2 | 0.1 | 0.25 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_complement_prob_mn__algebraic_system_2eq | 8 | 0.766 | 0.125 | 0.0 | 0.25 | 0.225 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_complex_eq_solcount__custom_binary_op | 10 | 0.575 | 0.0 | 0.0 | 0.1 | 0.175 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_complex_modulus_power__box_diagonal_sq | 12 | 0.344 | 0.25 | 0.0 | 0.0 | 0.075 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_constrained_digit_count__inclusion_exclusion_3set | 9 | 0.417 | 0.0 | 0.444 | 0.0 | 0.2 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_constrained_divisor_count__telescoping_mn | 12 | 0.208 | 0.0 | 0.417 | 0.0 | 0.225 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_constrained_subset_count__algebraic_system_2eq | 18 | 0.319 | 0.111 | 0.278 | 0.111 | 0.2 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_continued_fraction__inclusion_exclusion_3set | 8 | 0.328 | 0.0 | 0.25 | 0.0 | 0.154 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_count_pythagorean__custom_binary_op | 6 | 0.396 | 0.0 | 0.0 | 0.0 | 0.225 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_custom_binary_op__divisor_sum_filter | 10 | 0.362 | 0.1 | 0.3 | 0.2 | 0.175 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_digit_count_bigprod__complement_prob_mn | 13 | 0.558 | 0.154 | 0.077 | 0.077 | 0.25 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_divisor_sum_filter__modular_exponent | 9 | 0.431 | 0.333 | 0.0 | 0.0 | 0.15 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_equalization_fraction__box_diagonal_sq | 12 | 0.521 | 0.0 | 0.0 | 0.083 | 0.15 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_geo_first_exceed__equalization_fraction | 13 | 0.654 | 0.077 | 0.0 | 0.077 | 0.275 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_inclusion_exclusion_3set__modular_exponent | 11 | 0.216 | 0.182 | 0.182 | 0.0 | 0.175 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_infinite_product_exp__modular_exponent | 10 | 0.388 | 0.1 | 0.3 | 0.0 | 0.3 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_lcm_gcd_system__inclusion_exclusion_3set | 9 | 0.347 | 0.222 | 0.111 | 0.0 | 0.175 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_modular_exponent__divisor_sum_filter | 13 | 0.404 | 0.077 | 0.077 | 0.0 | 0.225 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_multi_constraint_square__algebraic_system_2eq | 8 | 0.359 | 0.0 | 0.0 | 0.0 | 0.175 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_point_rotation__modular_exponent | 15 | 0.442 | 0.067 | 0.333 | 0.267 | 0.075 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_poly_remainder__telescoping_mn | 14 | 0.607 | 0.143 | 0.0 | 0.071 | 0.225 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_polynomial_sign_intervals__complex_modulus_power | 9 | 0.292 | 0.111 | 0.333 | 0.0 | 0.175 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_primality_in_sequence__equalization_fraction | 12 | 0.375 | 0.25 | 0.0 | 0.0 | 0.25 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_prime_power_divisors__inclusion_exclusion_3set | 13 | 0.606 | 0.154 | 0.077 | 0.385 | 0.175 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_telescoping_mn__inclusion_exclusion_3set | 9 | 0.306 | 0.111 | 0.111 | 0.0 | 0.175 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_three_number_system__divisor_sum_filter | 9 | 0.611 | 0.222 | 0.111 | 0.333 | 0.1 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_trapezoid_area__algebraic_system_2eq | 11 | 0.705 | 0.0 | 0.091 | 0.0 | 0.2 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_triangular_filter_count__algebraic_system_2eq | 9 | 0.333 | 0.222 | 0.222 | 0.0 | 0.175 | IN_BAND | leave (difficulty-usable + diverse) |
| chain_unit_conversion_area__divisor_sum_filter | 16 | 0.453 | 0.125 | 0.062 | 0.125 | 0.225 | IN_BAND | leave (difficulty-usable + diverse) |


## edits this iteration
# depth-1 calibration — iter1 chain-layer edits

15 chains flagged. **12 edited (all PASS the static gate: golds/dedupe/top3 at n=200, seed=42 →
STATIC CHECKS: PASS 12/12). 3 left unchanged as not chain-layer-fixable (documented below).**
Only per-chain knob files were touched — `skeleton_injector_v12.py` is byte-unchanged (an
`fns`-knob adapter branch was tried then reverted; see equalize note).

Method note: I first tried aggressive eases (digit span→[69..169], telescoping gap→[1],
ie3 nsets→[1], an equalize small-fraction knob). The gate's resample-on-None harness exposed
that these collapse **dedupe/top3** (the iter-1–5 thrash mode that the rules warn about). I
backed each off to the **easiest setting that still clears the gate**. All difficulty moves are
via step/constraint count, not number size. (Per-iter SAMPLE top3 was ignored — n=40 showed
0.45 on two chains that are 0.22/0.23 at the gate's n=200, exactly the small-sample noise the
brief flagged.)

## TOO_HARD → eased (fewer steps/constraints) — 8
- **arith_series_sum__constrained_digit_count** — span `[149..799]`→`[149..549]` (drop the two
  longest scans 649/799). Only a modest ease on purpose: shrinking the scan window further
  clusters the digit-sum counts and busts top3 (0.305 at [149..349]). The answer-diversity floor
  caps how far this eases. Gate top3 0.235.
- **distinct_product_count__modular_exponent** — k `[2,3]`→`[2,2]` (one squaring, not a cube),
  m `[50,2000]`→`[40,600]`. Fewer exponentiation steps + tighter modular reduction.
- **frobenius_stamps__telescoping_mn** — gap `[1..5]`→`[1,2,3,4]` (drop gap=5, the messiest
  partial-telescoping). Dedupe-bound: gap=[1,2,3] → survival 0.885 (fail); [1,2,3,4] is the
  easiest passing value. Likely still partially feeder-capped (Frobenius is a hard feeder, was
  0.0); direction right, may not fully reach band.
- **lattice_points_circle__inclusion_exclusion_3set** — nsets `[2,3]`→`[1,2]` (mix in the
  single-divisor 1-set IE = fewer constraints). nsets=[1] alone busts dedupe (0.845); [1,2]
  passes (0.940) and still eases.
- **perfect_square_divisible__telescoping_mn** — gap `[1..6]`→`[1,2]` (clean/near-clean
  telescoping, less fraction-reduction work).
- **rate_closing__telescoping_mn** — gap `[1..5]`→`[1,2]` (same lever).
- **sum_of_squares__complex_modulus_power** — k `[1,2]`→`[1]` (compute |z|² not |z|⁴ — one step,
  no 4th power). Likely partially feeder-capped (was 0.083).
- **vieta_pair_count__complex_modulus_power** — k `[1,2]`→`[1]` (same). Was 0.01 → very likely
  feeder-capped (vieta_pair_count is a hard feeder); the target ease is the right direction but
  the feeder probably dominates.

## TOO_EASY → hardened (more steps/constraints) — 3
- **mean_removal__modular_exponent** — k `[2,2]`→`[3,4]` (more modular-multiplication steps),
  m `[30,300]`→`[40,400]`. Was 0.906.
- **vieta_sumcubes__inclusion_exclusion_3set** — nsets `[1]`→`[3]` (single floor-division → full
  3-set inclusion-exclusion, +2 constraints). Was 0.979. Clean §4 harden.
- **percent_compound__algebraic_system_2eq** — coef `[1,7]`→`[2,9]`, y/z `[5,25]`→`[8,35]`. Was
  0.864. CAVEAT: the 2-eq/3-unknown algebraic target has **no constraint-count knob** — the only
  chain-layer harden lever is heavier elimination arithmetic (larger coefficients). Kept modest
  and within envelope; flagging it as the borderline number-size lever, used only because no
  structural knob exists.

## LOW_DIVERSITY → diversified the non-fed input — 1
- **log_laws__complement_prob_mn** — added a `thr` knob (12 thresholds spanning 1/3…7/8). The
  feeder emits **18 distinct V** in [3,30] (NOT feeder-capped); the roll-count answer clustered
  only because the threshold was fixed. Widening the non-fed `thr` spreads r → gate top3 0.160.
  Mean stays ~0.55 (in band) — a diversity-only fix.

## NOT chain-layer-fixable (left unchanged) — 3

### FEEDER-CAPPED (needs human feeder-pass)
- **ordered_triple_constraint__box_diagonal_sq** (TOO_HARD, 0.175) — the box-diagonal target is
  already minimal (one fed edge + two squares); the difficulty is the FEEDER
  ordered_triple_constraint (atom gold ≈20%, a thin near-constant counter). No target-side ease
  exists. Mean ≈ the feeder's own rate — capped there.

### TARGET-DIVERSITY-CAPPED (effectively needs a feeder / fed-range pass)
- **count_obtuse_triangles__equalization_fraction** (0.036) and
  **roots_of_unity_sum__equalization_fraction** (0.125), both TOO_HARD — the equalize target's
  fed input g is bounded 3..14 (~12 distinct V), so its (1−fn)/V answer already sits near the
  0.30 dedupe/top3 ceiling (roots_of_unity baseline top3 ≈0.32). I tried a small-denominator
  `fns` knob to ease the m/n reduction; at gate-n it pushed top3 to 0.35/0.40 → would revert.
  Reverted both the knobs and the adapter branch. The equalize step has no constraint-count
  knob, so any arithmetic ease shrinks fraction variety and busts dedupe — the exact iter-1–5
  failure mode. roots_of_unity's feeder is solvable (atom 64%), so the real lever is widening the
  equalize **fed range** (atomic `equalize_g` envelope 3..14) — out of the chain-layer lane.

Net: **8 eased + 3 hardened + 1 diversified = 12 edited, all gate-green; 3 left flagged for a
human feeder-pass.**
