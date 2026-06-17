# v12 Depth-0 **Run-2** — Step-30 Progress Review
**2026-06-15 · prepared by kathryne · status: RUN IN PROGRESS (step 30/112, ~27%, epoch 0.27)**

W&B: https://wandb.ai/rl-intro/tiny-math-solver/runs/6rtzxaks
Box: L40S `i-07455ba55e473769d` (34.226.11.242) · output `run_20260615_212515` · S3 `runs/v12_depth0_run2/`

> **This is run-2, NOT the run in `v12_depth0_meeting_notes.md`.** That brief covered
> run-1 (`run_20260614_234419`, **vLLM**, 56 steps/2 epochs, W&B `1pf2vi1c`). Run-2 is a
> **fresh HF-generate** re-run on the config Michael pinned (batch 4 / ctx 2048 / 112 steps /
> 1 epoch / eval+save every 10 / K=4). First launch 20:58 logged nothing (missing
> `WANDB_API_KEY` → `report_to=none`); relaunched 21:25 clean with W&B live. Numbers below are
> run-2's own K=4 periodic stream and are **not** comparable 1:1 to run-1's K=16 banners.

## TL;DR
- Run-2 is **healthy** at step 30/112. Held-out climbs base → step-20, then **dips slightly at step-30**.
- Held-out mean_pass_rate (K=4, 79 frozen problems): **0.475 → 0.497 → 0.541 → 0.532** (step 0/10/20/30).
  Peak so far is **step 20 (+0.066 abs / +13.9% rel vs base)**; step-30 gave back **−0.009**.
- This is the **same shape as v10 and v12-run1** — held-out peaks early then fades. One eval point
  past peak at K=4 (noisy), so it's a **watch-flag, not a verdict**. Step-40 is the tell.
- Training internals all green: ghost batches low, KL stable, no truncation, no instability.
- **Load-bearing question unchanged** (Zaid's 06-11 reframe): is the gain *concept learning* or
  *template/wording reliability*? Held-out going up does NOT settle it — Michael's concept-transfer
  by-framing analysis is still the discriminator.

## Held-out trajectory (K=4, frozen 79-problem set, 3/concept)
| step | mean_pass_rate | Δ vs base | any_correct (pass@4) |
|---|---|---|---|
| 0 (base) | 0.4747 | — | 0.7975 |
| 10 | 0.4968 | +0.022 | 0.8734 |
| 20 | **0.5411** | **+0.066** | **0.8987** |
| 30 | 0.5316 | +0.057 | 0.8608 |

Both signals peak at step 20 and dip at step 30 (mean −0.009, pass@4 −0.038). The pass@4 drop
means the model isn't just shifting probability mass — it's **losing a few problems it had at step 20**.
Consistent with mild over-training past the peak, the recurring depth-0 ceiling pattern.

## Per-concept movement, base → step 30 (13 up / 9 down / 5 flat — net positive, broad)
Biggest gainers: perfect_square_divisible **+0.42**, inclusion_exclusion_3set **+0.33**,
divisor_sum_filter / polynomial_sign_intervals / equalization_fraction / complex_eq_solcount /
triangular_filter_count **+0.25**. Biggest givebacks: prime_power_divisors **−0.33**,
custom_binary_op / box_diagonal_sq / modular_exponent **−0.25**.
*(n=2–3 per concept at K=4 — per-concept deltas are directional only, heavy noise.)*
Note: two depth-1 chain ingredients (`prime_power_divisors`, `modular_exponent`) are among the
regressors — worth a glance given depth-1 is curriculum-gated on this checkpoint, but too thin to act on.

## Training internals through step 30 (from `checkpoint-30/trainer_state.json`)
| metric | reading | verdict |
|---|---|---|
| correctness reward | noisy ~0.34–0.66, no trend (s1–10 mean 0.509 ≈ s21–30 mean 0.503) | expected — GRPO reward is confounded; **held-out is the real signal** |
| ghost (`frac_reward_zero_std`) | mean **0.14**, mostly 0–0.25, a few 0.5 | **healthy** (v3 was 77.8%); 4 prompts/step so 0.25 = 1 ghost prompt |
| KL | 0.0 → ~0.003, monotone slow rise | stable, no divergence |
| grad_norm | ~0.03–0.11 | tiny, no instability |
| entropy | ~0.08–0.19, flat | stable, not collapsing |
| completions length / clipped | mean 545–1097 tok, clip ≈0 | **2048 not truncating** |
| format reward | flat ~0.10 | as designed |

## The debate to settle (unchanged from run-1 brief)
1. Is the held-out trajectory strong enough to call depth-0 a success on its own? **Watch step-40/50:**
   does it recover past 0.541 or confirm an early-peak-then-fade (then the useful checkpoint is ~step 20)?
2. Does the concept-transfer result change the interpretation — blocker for declaring depth-0 done?
3. Green-light depth-1 calibration against this checkpoint once it lands, or hold for the transfer verdict?

Context: the 06-12 base diagnostic already showed the AMC ceiling is **composition, not atom knowledge**
(gaps +0.19→+0.61 across 3 chains) → depth-1 is queued but curriculum-gated on this depth-0 model.

## Reproduce
- Held-out trajectory: pull `runs/v12_depth0_run2/holdout_transcripts/holdout_step{0,10,20,30}*.jsonl`;
  `mean_pass_rate = mean(n_correct_rollouts / k)` over the 79 records.
- Training metrics: `runs/v12_depth0_run2/checkpoint-30/trainer_state.json` → `log_history`.
- Live rollouts: `runs/v12_depth0_run2/completions/completions_*.parquet` (one per step).
