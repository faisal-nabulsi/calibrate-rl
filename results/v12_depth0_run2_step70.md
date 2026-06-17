# v12 Depth-0 **Run-2** — Step-70 Eval Review
**2026-06-16 · prepared by kathryne · status: RUN IN PROGRESS (step 70/112, ~63%, epoch 0.625)**

W&B: https://wandb.ai/rl-intro/tiny-math-solver/runs/6rtzxaks
Box: L40S `i-07455ba55e473769d` · output `run_20260615_212515` · S3 `runs/v12_depth0_run2/`
(checkpoint-70 written 02:36 UTC; step-80 expected ~03:20.)

## TL;DR — the step-30 "early-peak-then-fade" flag did NOT pan out
- Held-out **recovered and made new highs**. mean_pass_rate (K=4, 79 frozen problems):
  **0.475 → 0.497 → 0.541 → 0.532 → 0.554 → 0.554 → 0.554 → 0.589** (step 0/10/20/30/40/50/60/70).
- Step-70 is the **best point yet: +0.114 abs / +24% rel vs base**, and still climbing — NOT the
  v10/run-1 peak-then-decay shape the step-30 note warned about. The step-30 dip (−0.009) was noise.
- One real caveat: **pass@4 diverges from mean_pass**. pass@4 peaked step-40 (0.924) and has
  drifted back to 0.873 (= step-10 level) while mean_pass kept rising. Read: probability mass is
  **concentrating** on problems it can already do (more of the 4 rollouts land), but it's **lost ~2–3
  problems entirely** that it had at step 40. Net still strongly positive; watch it.
- Training internals all green. No instability. **Caveat: K=4 is noisy** and the load-bearing
  concept-vs-template question (Zaid 06-11 / Michael's by-framing eval) is **still the discriminator** —
  held-out climbing does NOT settle it.

## Held-out trajectory (K=4, frozen 79-problem set, ~3/concept)
| step | mean_pass | Δ base | pass@4 | Δ base |
|---|---|---|---|---|
| 0 (base) | 0.4747 | — | 0.7975 | — |
| 10 | 0.4968 | +0.022 | 0.8734 | +0.076 |
| 20 | 0.5411 | +0.066 | 0.8987 | +0.101 |
| 30 | 0.5316 | +0.057 | 0.8608 | +0.063 |
| 40 | 0.5538 | +0.079 | **0.9241** | **+0.127** |
| 50 | 0.5538 | +0.079 | 0.8861 | +0.089 |
| 60 | 0.5538 | +0.079 | 0.8734 | +0.076 |
| 70 | **0.5886** | **+0.114** | 0.8734 | +0.076 |

mean_pass: clean monotone-ish climb after the s30 wobble. pass@4: peaks s40, eases off → the
mean/pass@4 split above.

## Per-concept, base → step 70 (18 up / 6 down / 3 flat — broad + net positive)
*(n=2–3 per concept at K=4 — directional only, heavy noise.)*
- **Big gainers:** inclusion_exclusion_3set **+0.75** (0.08→0.83), roots_of_unity_sum +0.42,
  count_pythagorean / equalization_fraction / perfect_square_divisible / complex_eq_solcount **+0.33**,
  continued_fraction +0.25.
- **Regressors:** box_diagonal_sq −0.25, complex_modulus_power −0.25, prime_power_divisors /
  lcm_gcd_system / custom_binary_op −0.17, alternating_cubes −0.08.
- **Update vs step-30:** modular_exponent **recovered** (was −0.25 at s30, now +0.08). Of the two
  depth-1 chain feeders flagged at s30, modexp is back in the black; **prime_power_divisors is still
  down −0.17** — the one to keep an eye on since depth-1 is curriculum-gated on this checkpoint.

## Training internals through step 70 (`checkpoint-70/trainer_state.json`)
| metric | reading | verdict |
|---|---|---|
| reward (total) | ~0.61 mean, early(≤20) 0.56 → late(≥50) 0.64 | mild real uptrend |
| ghost (`frac_reward_zero_std`) | mean **0.168**, max 0.5, last 0.0 | healthy (v3 was 77.8%) |
| KL | 0.0 → 0.0018, mean 0.0024 | stable, no divergence |
| grad_norm | 0.028–0.111 (last 0.043) | tiny, no instability |
| entropy | ~0.07–0.19, flat ~0.115 | stable, not collapsing |
| completions length | mean 780, **last 935 (rising)**; clipped_ratio **0.031 at s70** (1/32 hit 2048) | 2048 holding but truncation just starting to flicker — watch |

## Calls
1. **Recommend killing the step-30 watch-flag.** This is not an early-peak run; held-out is at its
   best at step 70 and still rising. If anything the useful checkpoint is late, not ~step 20.
2. **Watch the mean/pass@4 split + the creeping completion length (clip 0→0.031).** If pass@4 keeps
   sliding while length grows, that's mild over-training/verbosity past the real ceiling — decide
   then whether to stop at 80–90 or run the full 112.
3. **Concept-vs-template is still the gate** for "depth-0 done." A climbing held-out is necessary,
   not sufficient — Michael's by-framing analysis still owns that verdict.
