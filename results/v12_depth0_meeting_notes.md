# v12 Final Depth-0 Run — Meeting Notes (Faisal × Zaid)
**2026-06-15 · prepared by kathryne · status: RUN IN PROGRESS (~step 19/56, 34%)**

W&B run: https://wandb.ai/rl-intro/tiny-math-solver/runs/1pf2vi1c

## TL;DR
- v12 "final depth-0" GRPO+LoRA run is **live on the L40S** — first run on **vLLM**. Clean so far.
- Early held-out: base **0.454 → 0.535 @ step 14** (+0.081, +17.8% rel), frozen 79-problem set.
- Load-bearing question (unchanged): is the gain **concept learning** or **template/wording reliability** (Zaid's 06-11 reframe)? Michael's concept-transfer by-framing analysis is the discriminator (pending).
- Gates: (a) does the run "count" as the depth-0 model; (b) does depth-1 chaining proceed — it's curriculum-gated on *this* checkpoint.

> ⚠️ **FLAG:** TODO says *"HOLD the big final depth-0 run until the concept-transfer eval result is in."* This run launched 06-14 23:44. Confirm at the top whether that gate cleared or this is a preliminary run.

## Config
- Qwen2.5-7B-Instruct + LoRA, GRPO. vLLM colocate ON (USE_VLLM=1, gpu_util 0.5).
- Train 449 (302 goldilocks + 147 borderline), 27 concepts (log_laws dropped), mean base pass 0.488.
- Holdout 79 (frozen, disjoint, seed 42, 3/concept), 63 gold + 16 borderline, mean base pass 0.517.
- Reserve 90 too_hard; 127 too_easy dropped. 2 epochs, 56 steps, ctx 2048, eval every 14.

## Key stats (live)
| metric | value |
|---|---|
| held-out mean_pass_rate, base (step 0) | **0.4541** (pass@16 1.0, boxed 0.995) |
| held-out mean_pass_rate, step 14 | **0.5348** (pass@16 0.987, boxed 0.994) |
| Δ so far | **+0.081 abs / +17.8% rel** — only 1 periodic eval yet; step-28 is next |
| correctness reward (steps 1–19) | noisy ~0.34–0.57, peak 0.57 @ step 11, now ~0.41 |
| ghost batches (frac_reward_zero_std) | 0–0.31, mostly ≤0.12 → **healthy** (v3 was 77.8%) |
| KL | 0.0002 → 0.017 blip → ~0.0016 (stable) |
| ISR mean | 0.87 → 0.43 = **vLLM logprob mismatch, expected/TRL-handled**, not a bug |

## The debate to settle
1. Is the held-out trajectory (watch step-28/42/56) strong enough to call depth-0 a success on its own terms?
2. Does the concept-transfer result change the interpretation — and is it a blocker for declaring depth-0 done?
3. Green-light depth-1 calibration against this checkpoint once it lands, or hold for the transfer verdict?

Context: base diagnostic (06-12) already showed the AMC ceiling is **composition, not atom knowledge** (gaps +0.19→+0.61 across 3 chains) → depth-1 is queued but curriculum-gated on this depth-0 model.

## W&B walkthrough (Faisal, do it live with Zaid)
Scroll: `train/reward` + `correctness_reward/mean` (noisy, health only) · `frac_reward_zero_std` (ghost — point out it's low) · `kl`/`entropy` (stable) · `completions/mean_length`+`clipped_ratio` (2048 not truncating) · `importance_sampling_ratio` (pre-empt: drift = vLLM, expected).
**Held-out is NOT in the charts** (W&B rejects out-of-order steps) — it's stdout-banner only; use the table above.

## Transcripts (if Zaid asks)
- **Live rollouts (this run):** `ssh ec2-user@34.226.11.242` → `~/calibrate-rl/checkpoint/run_20260614_234419/completions/completions_*.parquet` (one/step). Read: `pandas.read_parquet(f)[['prompt','completion','reward']]`.
- **Base-vs-trained held-out (qualitative):** `results/holdout_resp_base__abl3_holdout.json` + `..._checkpoint-108__...` + `results/holdout_compare.html` viewer (PR #21).
- **Concept-transfer responses (the discriminator):** `results/holdout_resp_{base,checkpoint-108}__concept_transfer_eval.json` (5 same-task framings, #61).

PDF: `results/v12_depth0_meeting_brief.pdf`
