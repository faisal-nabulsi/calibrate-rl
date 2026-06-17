# v12 Depth-0 **Run-2** — Step-90 Eval Review
**2026-06-16 · prepared by kathryne · status: RUN IN PROGRESS (step 90/112, ~80%, epoch 0.804)**

W&B: https://wandb.ai/rl-intro/tiny-math-solver/runs/6rtzxaks
Box: L40S `i-07455ba55e473769d` · output `run_20260615_212515` · S3 `runs/v12_depth0_run2/`
(checkpoint-90 + `holdout_step90_periodic.jsonl` written 04:13 UTC; step-100 expected ~04:55, final 112 ~05:35.)

## TL;DR — this is the decision point the step-80 note set up, and both stop-conditions fired.
- mean_pass_rate (K=4, 79 frozen problems):
  **0.475 → 0.497 → 0.541 → 0.532 → 0.554 → 0.554 → 0.554 → 0.589 → 0.557 → 0.554** (step 0/10/.../90).
- Step-90 = **+0.079 abs / +17% rel vs base** — landed *exactly* back on the step-40/50/60 plateau
  value (0.5538). The step-70 high (0.589) is now clearly the top of the noise band, not a trend.
  Held-out has not made a real net move since step ~20.
- **pass@4 kept sliding: 0.835** (Δ base +0.038) — a **new low since the climb**, continuing
  s40 0.924 → s70 0.873 → s80 0.861 → **s90 0.835**. The mean/pass@4 split I've flagged since s70
  is widening: probability mass concentrating on already-solved problems while a few are lost
  entirely. mean_pass flat + pass@4 falling = mild over-training, not new learning.
- **Step-80's two stop-conditions BOTH met:** (1) "90 prints in-band (~0.53–0.59) with clip ≤~0.05"
  → 0.554 in-band, clip last = 0.0; (2) "pass@4 keeps sliding" → it did (0.861 → 0.835).
  **Signal-based read: no reason to run past ~90.** Stop at 90 (or let it coast to 112 only for a
  clean round number — there's nothing to gain).
- One honesty correction to the s70/s80 worry: **completion length did NOT run away.** It's bouncing
  ~700–900 (late mean 848, last 832), clip receded to 0 in the last 4 steps. So the over-training
  signal is purely the pass@4 concentration, **not** verbosity blow-up. 2048 ctx is fine.
- **Load-bearing question unchanged:** held-out level does NOT settle concept-vs-template (Zaid 06-11 /
  Michael's by-framing eval). A plateau-that-now-erodes-on-pass@4 is *less* of a "depth-0 done"
  argument than a clean plateau, not more.

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
| 90 | 0.5538 | +0.079 | **0.8354** | +0.038 |

mean_pass: sat in **0.53–0.59** for eight straight evals (step 20–90) — a flat band, 0.589 the high
edge. pass@4: **monotone decline from its s40 0.924 peak** (0.924→0.886→0.873→0.873→0.861→0.835).
That divergence is the only thing actually moving, and it moves the wrong way.

## Per-concept, base → step 90 (12 up / 10 down / 5 flat — still net positive, but the spread is narrowing)
*(n=2–3 per concept at K=4 — directional only, heavy noise; up-count was 18 at s70, 14 at s80, 12 now.)*
- **Big gainers:** inclusion_exclusion_3set **+0.50** (0.08→0.58), count_pythagorean **+0.42**,
  perfect_square_divisible **+0.42** (0.58→**1.00**), lattice_points_circle +0.38, continued_fraction /
  complex_eq_solcount **+0.33**.
- **Regressors:** custom_binary_op **−0.33** (0.58→0.25), constrained_divisor_count / poly_remainder
  **−0.17**, then a cluster at −0.08 (alternating_cubes, telescoping_mn, polynomial_sign_intervals,
  modular_exponent, roots_of_unity_sum, prime_power_divisors, complement_prob_mn).
- **Don't trust the s80→s90 deltas** — pure K=4 noise (custom_binary_op 0.58→0.25 this step alone;
  at n=3 one rollout flip = ±0.17–0.33). Read the base→s90 column, not adjacent-step swings.
- **Depth-1 feeder watch (curriculum-gated on this ckpt):** **prime_power_divisors still −0.08** —
  now soft at s30/s70/s80/s90, the persistent one. **modular_exponent −0.08** again (never held its
  s70 recovery). **constrained_divisor_count −0.17** joins them. Three of the chain feeders are
  flat-to-down vs base; thin data, but worth a note before depth-1 calibrates on this checkpoint.

## Training internals through step 90 (`checkpoint-90/trainer_state.json`)
| metric | reading | verdict |
|---|---|---|
| reward (total) | mean 0.605, early(≤20) 0.560 → late(≥70) 0.585; last5 noisy [0.69, 0.48, 0.73, 0.85, 0.51] | uptrend flattened; late ≈ s80, confounded as ever |
| ghost (`frac_reward_zero_std`) | mean **0.153**, last5 [0,0,0,0,**0.25**] | healthy band; one ghosty final step, not a trend (v3 was 77.8%) |
| KL | mean 0.0024, last 0.0018 | stable, no divergence |
| grad_norm | last 0.036 (range 0.028–0.111) | tiny, no instability |
| entropy | mean 0.114, **last 0.084** (drifting down a touch) | mild concentration — consistent with the pass@4 slide, not a collapse |
| completions length | late(≥70) mean **848**, last 832; **NOT climbing** (bounces 700–900) | length creep I flagged at s70 **did not materialize** — plateaued |
| clipped_ratio | mean 0.011, last5 [0.031, 0, 0, 0, **0**] | truncation receded to 0; 2048 holding comfortably |

## Calls
1. **Stop at ~90 — both step-80 stop-conditions fired.** Held-out is in-band (0.554, on the s40–60
   plateau), pass@4 is declining (0.861→0.835), entropy easing, clip at 0. There is **no signal-based
   reason to spend the last 22 steps** — it's bouncing on a ceiling and the only moving metric
   (pass@4) is mild over-training. Useful checkpoint is anywhere in **40–90**; nothing past ~70 buys
   real held-out gain.
2. **Best honest summary of run-2:** depth-0 RL gave a **clean, broad +0.08 mean_pass / +17% rel**
   (12–18 concepts up across the run), plateaued by step ~20–40, and has sat in the 0.55 band since.
   pass@4 peaked early (s40) and erodes — the model gets *more reliable* on what it already knows and
   slowly *narrower*, exactly the "execution reliability on a known method, not new concept skill"
   read from v10 / Zaid's 06-11 reframe. **Same shape as v10** (which peaked ~step 81 then declined).
3. **Concept-vs-template is still THE gate** for "depth-0 done." A plateaued-and-eroding held-out is
   necessary, not sufficient — Michael's by-framing analysis owns that verdict, and this run makes it
   *more* important: the held-out number is no longer climbing, so it can't carry the argument alone.
4. **Heads-up for depth-1 (curriculum-gated on this ckpt):** prime_power_divisors / modular_exponent /
   constrained_divisor_count are flat-to-down vs base here. If depth-1 calibrates against this
   checkpoint, those three chain feeders are the ones to sanity-check first.
