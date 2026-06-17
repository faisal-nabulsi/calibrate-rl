# v12 Depth-0 **Run-2** — Step-80 Eval Review
**2026-06-16 · prepared by kathryne · status: RUN IN PROGRESS (step 80/112, ~71%, epoch 0.714)**

W&B: https://wandb.ai/rl-intro/tiny-math-solver/runs/6rtzxaks
Box: L40S `i-07455ba55e473769d` · output `run_20260615_212515` · S3 `runs/v12_depth0_run2/`
(checkpoint-80 written 03:26 UTC; step-90 expected ~04:10.)

## TL;DR — step-70 was the top of a noisy plateau, not a climb. Held-out gave back ~⅓ of the gain at step 80.
- mean_pass_rate (K=4, 79 frozen problems):
  **0.475 → 0.497 → 0.541 → 0.532 → 0.554 → 0.554 → 0.554 → 0.589 → 0.557** (step 0/10/.../80).
- Step-80 = **+0.082 abs / +17% rel vs base** — still solidly positive, but **down −0.032 from the
  step-70 high (0.589)**, landing right back on the 0.554 step-40/50/60 level.
- **Corrected read of the step-70 note:** I called step-70 a "new high still climbing" and killed the
  early-peak watch-flag. Step-80 says that was over-read — it's neither a clean climb nor a clean
  peak-then-fade. It's a **plateau in the ~0.55 band** where the periodic K=4 eval (n=2–3/concept)
  has ±0.03 step-to-step noise that swamps the real move. **0.589 was the top of the band, not a trend.**
- pass@4 confirms the plateau: **0.798 → … → 0.924 (s40 peak) → 0.873 → 0.873 → 0.861 (s80)**. Eased
  off its s40 peak and flat since. No new problems being won; mass just sloshing.
- Training internals **all still green** — no instability, ghost healthy, KL flat. The mild
  completion-length / clip creep I flagged at s70 is **holding, not running away** (clip still ~3%).
- **Load-bearing question unchanged:** held-out level does NOT settle concept-vs-template (Zaid 06-11 /
  Michael's by-framing eval). A bouncing plateau is even less of an argument for "depth-0 done" than a
  clean climb was.

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
| 80 | 0.5570 | +0.082 | 0.8608 | +0.063 |

Read the **band**, not the points: mean_pass has sat in **0.53–0.59** since step 20 (six evals,
spread 0.057), pass@4 in **0.86–0.92** since step 10. Step-70's 0.589 and step-30's 0.532 are the
high/low edges of the same noise band, not turning points.

## Per-concept, base → step 80 (14 up / 9 down / 4 flat — still broad + net positive)
*(n=2–3 per concept at K=4 — directional only, heavy noise.)*
- **Big gainers:** equalization_fraction **+0.42** (0.33→0.75), continued_fraction / complex_eq_solcount /
  ordered_triple_constraint **+0.33**, constrained_digit_count / inclusion_exclusion_3set /
  lattice_points_circle / perfect_square_divisible **+0.25**.
- **Regressors:** telescoping_mn **−0.25** (0.33→0.08), prime_power_divisors **−0.17**,
  constrained_subset_count −0.17, modular_exponent / multi_constraint_square / polynomial_sign_intervals /
  triangular_filter_count / alternating_cubes / complement_prob_mn −0.08.
- **Don't trust the step-70→80 deltas** — they are pure K=4 noise: the same concepts swing ±0.4 between
  adjacent evals (ie3 0.83→0.33, telescoping 0.50→0.08, but box_diagonal_sq 0.50→0.88, complex_modulus_power
  0.42→0.83). At n=2–3 one rollout flip = ±0.17–0.33. This is why per-concept reads stay directional-only.
- **Depth-1 watch (curriculum-gated on this ckpt):** **prime_power_divisors still down −0.17** vs base
  (the persistent one — down at s30, s70, s80); **modular_exponent slipped back to −0.08** after recovering
  at s70. Both are chain feeders; thin data, but the pattern on ppd is now three evals deep.

## Training internals through step 80 (`checkpoint-80/trainer_state.json`)
| metric | reading | verdict |
|---|---|---|
| reward (total) | mean 0.599, early(≤20) 0.560 → late(≥60) 0.595 | mild real uptrend, confounded as ever |
| ghost (`frac_reward_zero_std`) | mean **0.163**, max 0.5, **last 5 all 0.0** | healthy (v3 was 77.8%) |
| KL | mean 0.0024, max 0.0071, last 0.0018 | stable, no divergence |
| grad_norm | 0.028–0.111, last 0.047 | tiny, no instability |
| entropy | ~0.07–0.185, flat ~0.115 | stable, not collapsing |
| completions length | mean 791, **last 922** (s70 was 935 — flat, not climbing); clipped_ratio mean 0.011, **last 0.031** (1/32) | length creep **stalled**; 2048 holding, truncation still a flicker |

## Calls
1. **Re-open (don't re-kill) the plateau read.** My step-70 "killed the early-peak flag" call was
   premature — step-80 shows a plateau, not a climb. The honest statement is: **held-out plateaued in
   the ~0.55 band around step 20–40 and has bounced there since.** Useful checkpoint is anywhere in
   40–80; step-70 is not special.
2. **Decision point at step 90.** Two more evals (90, 100/112) settle it. If 90 prints in-band again
   (~0.53–0.59) with clip ≤~0.05, there's **no signal-based reason to run past ~90** — it's bouncing on
   a ceiling. If pass@4 keeps sliding (s40 0.924 → s80 0.861) while length grows, that's mild
   over-training and argues for stopping at 80–90 over the full 112.
3. **Concept-vs-template is still the gate** for "depth-0 done." A plateaued held-out is necessary, not
   sufficient — Michael's by-framing analysis owns that verdict, and a noisy plateau makes it *more*
   important, not less.
