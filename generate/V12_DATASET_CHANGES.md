# v11 → v12 Dataset Changes (data-grounded)

> Every change below is justified by a cited result from the **v10 training run**
> or the **v11 2048 calibration**. Extends the Drive "v11 Action Plan" (Doc4) with
> an **answer-diversity audit** (new this round) and the **3-concept ablation**
> concept picks. Target generator: `generate/skeleton_injector_v12.py` (fork of v11).
> v12 is also the substrate for Michael's falsification ablation (full vs
> random-same-size vs goldilocks) — coordinate data changes with him.

## Evidence base

**v10 training** — `run_20260607_033330`, Qwen2.5-7B + LoRA/GRPO, 106 train / 12 holdout, 120 steps (4.6 epochs), @1024:
- Held-out mean_pass_rate: base **0.537** → **0.651 @step 81 (3 epochs, +0.114)** → **0.672 @step 120**.
- **Overfit onset:** held-out saturated at step 81 while train reward kept climbing (0.711 window avg @108). The 106-set was the bottleneck, not the method.
- **Ghost batches rose 7% → 13%** as concepts were "used up" (calibration decaying mid-run).
- AMC: **32/83 → 34/83** (+3 covered, −1 uncovered; the −1 broke easy problems base already had).
- Stability clean: entropy 0.130→0.110, KL ~0.004, boxed_rate 0.96 (no reward hacking).

**v11 calibration** — `calib_v11_2048_7B.json`, 500×8 @2048:
- Zones: **goldilocks 240 (48%)**, borderline 106 (21%), too_easy 103 (21%), too_hard 51 (10%). Mean pass **0.55** (easy-skewed — too_easy is 2× too_hard, so most fix-work is *raising* difficulty).
- **31% pre-baked ghost batches** (154/500 `advantage_std=0`) — v10's plateau mechanism present *before training starts*.
- 2048 payoff: too-hard 16%→10%, truncation 14%→1%. Grader sanity: 0/236 false-negatives.

## Headline v12 changes

1. **Bigger, lower-epoch train set.** v10 overfit by epoch 3 → v12 ~300 clean goldilocks (no borderline padding) @ ~225 steps ≈ 3 effective epochs.
2. **Attack pre-baked ghosts (31% → <10%).** Most are *representation bugs*, not difficulty — fix at the generator.
3. **Raise difficulty, net.** Mean pass 0.55 + too_easy 2× too_hard → harder variants via constraint/step count, **never number size** (§4).
4. **Carry forward:** 2048 tokens (validated), base AMC = 32/83 (retire 18/83), temp 1.0.

## Per-concept generator changes (`skeleton_injector_v12.py`)

### A. Representation fixes — kill ghost batches (highest value)
| concept | v11 evidence | change |
|---|---|---|
| **log_laws** | 17% gold, bimodal free-vs-impossible (`log2(2^14)` trivial / `log3(1594323)` impossible) → ghost-heavy | standardize to **exponent-explicit, combined-argument** form (product/quotient rule); keep answer `e1+e2-e3` UNCHANGED so the PR #6 recomputer / kathryne's verification stays valid. Unlocks AMC #5,#51,#80. |
| **ordered_triple_constraint** | 31% gold; NL phrasing → pr≈0; consistent off-by-one (count−1) | switch to **explicit-inequality** phrasing; fix the count−1 bug. |

### B. Answer-diversity / cardinality fixes — NEW (not in v11 plan)
Doc4 left these in "leave alone" on **gold% alone**. An answer-diversity audit this round shows they are **answer-hackable** (the multi_constraint_square / count_pythagorean "just say the common answer" lesson). Both are 3-concept-ablation picks, so they must be training-grade:

| concept | audit (gen_clean) | change |
|---|---|---|
| **complex_modulus_power** | 86 unique / **14 distinct answers / top-3 = 43%**; gen_clean low-cardinality warning | widen parameter ranges (distinct moduli/arguments) → lift cardinality; target top-3 < 15%. |
| **constrained_divisor_count** | 176 unique / **19 distinct / top-3 = 38%** (divisor counts are structurally small ints) | widen constraint variety (C knob); if still concentrated, cap per-answer frequency in gen_clean. |

### C. Scaffold / route to chaining
| concept | v11 evidence | change |
|---|---|---|
| **constrained_subset_count** | 17% gold, depth-1 composition | scaffold down (set {1..8}, mod 3, size-2) for a depth-0-trainable variant — **changes the answer → recomputer update + re-verify** — OR route to Phase-3 chaining (it's the ready pilot). Covers AMC 1,15,27,57,81. |

### D. Raise difficulty (group A levers, from v11)
- **perfect_square_divisible**: non-square composite divisors (12,18,50), not squares.
- **divisor_sum_filter**: n with ≥3 distinct odd prime factors (not prime powers like 256).
- **algebraic_system_2eq**: reject all-1-coefficient rows; mixed larger coefficients.
- **complement_prob_mn**: higher thresholds (0.9, 0.95), larger dice.
- **prime_power_divisors**: raise + resample (also low n).

### E. Resample only (low n in v11)
box_diagonal_sq, lattice_points_circle, count_pythagorean, prime_power_divisors.

### F. Leave alone — confirmed clean on gold% AND diversity
inclusion_exclusion_3set (63% gold, **360 distinct / top-3 2%** ✓), lcm_gcd_system, roots_of_unity_sum, triangular_filter_count, telescoping_mn, continued_fraction, alternating_cubes, complex_eq_solcount, polynomial_sign_intervals.

## Hyperparameters (v12)
| knob | v10 | v12 |
|---|---|---|
| train size | 106 | ~300 (clean goldilocks, no borderline) |
| steps | 120 (4.6 ep) | ~225 (~3 ep) |
| calib tokens | 1024 | 2048 |
| holdout | 12 (1/concept) | 3–5/concept |
| LoRA rank | 32 | 32 → 64 |
| temperature | 1.0 | 1.0 |

## Gates before any v12 training
1. Gold machine-verified for equalization_fraction, log_laws, complement_prob_mn — **done** (PR #6 recomputers / kathryne).
2. After each generator change: recalibrate affected concepts @2048 → confirm **ghost fraction down** AND **answer top-3 < 15%** before the concept enters selection.
