# Review — Faisal's depth-0 training-run approval (CalibrateRL v10)

Reviewer: Michael · Date: 2026-06-04 · Scope: repo `calibrate-rl` @ `03cc2db`, plus uploaded writeups/transcripts.

**Recommendation: DON'T TRAIN YET — approve after the 2 blocking fixes below.**
Neither blocker is deep; they're ~1 hour of config work. But as the launch script stands today, the run would train the *wrong dataset* at the *wrong temperature*, so it must not be kicked off as-is. The science is solid; the wiring isn't.

> **Update (per Michael, 2026-06-04):** the goldilocks band is intentionally **2–6/8** (the rule was updated from 1–3/8). That's no longer a discrepancy — former blocker #3 is resolved and removed. Two blockers remain.

---

## What looks solid ✅

- **The key sanity check passes.** Stronger model scores higher: 1.5B mean reward **0.165** vs 7B **0.508** (3.1×) on the same v10 set (`Training_Approval` p3/p14). This is the single most important Step-7 check and it holds at the aggregate level. The 1.5B piling into too-hard while the 7B spreads into goldilocks is the right qualitative signature.
- **No reward hacking in the actual data.** I re-graded all 112 rollouts in the verbatim transcript dump with Faisal's own `reward_func`. My re-grade matches his recorded grades **100% (0 disagreements)**, **every one of the 53 correct grades came from a real `\boxed{}`** (zero won via a fallback), and the lone multi-`\boxed` case just repeated the same value. The model is committing to single boxed answers (87% of rollouts), not listing candidates. Step-8 "no gaming" conclusion is supported *for the current model*.
- **Calibration uses the same correctness function training uses** (`measure_v10_full.py` imports `extract_predicted_answer`/`_numbers_match` from `reward_func.py`). Good discipline — the measured difficulty is computed with the real grader.
- **Genuine reasoning in transcripts.** Reading the rollouts, wrong answers are honest math/search-length errors (e.g. dropping the "ends-in-8" root case, running out of token budget mid-enumeration), not formatting artifacts. The difficulty is real.
- **The iteration story is honest** — v3→v10 trades blunt range-tweaks for transcript-driven fixes, and the deck flags its own open items (14B tier skipped, v11 projected-not-run).

## Blocking concerns 🔴 (must fix before kicking off)

1. **The training script trains the WRONG dataset.** `train_grpo.py:90` loads `data/skeleton_dataset_v3.json`. The approval is for **v10**. Per your own Update deck, v3 is "Attempt 1 — easy∘easy, 78% zero-gradient, ZERO signal." If Faisal runs this file as committed, he burns a multi-hour run on the worst set you ever built, not the calibrated one. → change to `skeleton_dataset_v10.json` (and confirm the file is actually on the box).

2. **Calibration temperature ≠ training temperature.** Goldilocks pass-rates were measured at **temp 1.0** (`measure_v10_full.py:71`). Training samples at **temp 1.2 annealing → 0.7** (`train_grpo.py:116,234`). The entire thesis is "difficulty calibrated to the model" — and sampling temperature is part of that calibration. The carefully-tuned 40%-goldilocks distribution does not transfer to a different temperature; you'd be training against an uncalibrated difficulty profile. → either calibrate at the training temperature, or train at 1.0. Pick one and make them match.

## Resolved (was a concern, now confirmed intentional) ✅

- **Goldilocks band = 2–6/8.** The code defines goldilocks as `0.25 ≤ pass_rate ≤ 0.75` = **2–6 of 8** (`measure_v10_full.py:98`). Confirmed by Michael that the rule was updated from 1–3/8 to 2–6/8, so the code and the "40% dead-center" headline are correct. No action.

## Non-blocking concerns 🟡 (fix soon / know the risk)

4. **The grader is hackable in principle, even though the model isn't hacking it yet.** `extract_predicted_answer` (`reward_func.py:56`) falls through `\boxed` → `####` → "the answer is" → `**bold**` → **last number in the text**. My stress test confirms: *"Could be 10, 20, 30, or 42."* with gold 42 grades **CORRECT** via the last-number fallback (candidate-listing hack), and an answer with no commitment ("maybe 17 or 42") also passes. It doesn't matter for a static eval, but **GRPO optimizes against exactly this target** — if trailing-number or candidate-listing ever earns reward, the policy can drift into it. → Recommend hardening before/early in training: require a `\boxed{}` (drop the last-number fallback, or gate it), and if multiple `\boxed` appear, take the last and/or penalize. Cheap insurance for a training (not eval) reward.

5. **LaTeX fractions in `\boxed{}` are mis-graded.** `\boxed{\frac{1}{2}}` (gold `1/2`) → the regex grabs the denominator **"2"** → marked WRONG; `\boxed{\dfrac{3}{4}}` → grabs "4". The boxed regex only handles bare `a/b`, not `\frac{}{}`. This is **currently masked** because v10 answers appear to be integers (protocol Step 5 validates "integer answers"; all 112 transcript golds are integers) — but it's a landmine the moment any concept emits a fraction (and Qwen loves `\boxed{\frac{...}}`). The dead `extract_answer` in the measure scripts actually handles this case better, ironically. → Fix the regex; add a fraction case to a grader unit test.

6. **"100% parse rate (2400/2400)" is not evidence of output quality.** Because of the last-number fallback, the parser fires on essentially any text containing a digit — parse rate ≈100% is automatic and says nothing about whether the model produced a real answer. The meaningful metric is the **`method=='boxed'` rate** (87% in the transcripts), not parse rate. Don't lean on "100% parse" as a quality claim.

7. **"Monotonic across every concept" is asserted but not verified by the code.** `analyze_calibration.py:87-92` only checks that the *aggregate* mean reward of the bigger model is higher. The per-concept ordering isn't computed anywhere in the repo, and the `calib_*.json` files aren't included to check by hand. The 3.1× aggregate is real; the stronger "every concept" claim on p2 isn't backed by what's here. → Either run a per-concept ordering check or soften the claim.

8. **Calibration reward ≠ training reward (minor).** Calibration scores correctness only; training adds `format_reward` (`train_grpo.py:214`): +0.1 for boxed+30 words, −0.2 for no work. It's small and mostly cancels within a GRPO group, so low-risk, but it makes the "grades identically to training" claim (Step 4) imprecise. Worth a sentence of acknowledgment.

9. **Training data isn't filtered to the goldilocks zone.** The zone classification is diagnostic only; `train_grpo.py` trains on the full set. That may be intentional (rely on group-relative advantage to zero out saturated prompts), but if "environment quality is the binding constraint," consider actually filtering the train set to the productive band. At minimum, decide deliberately rather than by default.

10. **Hygiene (non-blocking):** `train_grpo.py` docstring/comments are stale copy-paste (GSM8K, entity-tracking, 1.5B, "beta=0.04" while the value is 0.1) — re-read the config before launch so nothing is accidental. And `os.system("sudo poweroff")` at the end (line 253) nukes the box after training — fine if intended, but you lose post-mortem access; consider gating it.

## Bottom line for chat

> Reviewed Faisal's v10 step-7 package. The science is good — capability ordering holds 3.1× (1.5B 0.165 → 7B 0.508), reasoning in transcripts is genuine, and I re-graded all 112 verbatim rollouts: zero grader-gaming, 100% grade agreement, every correct answer from a real `\boxed`. **But I can't approve kicking it off as-is.** `train_grpo.py` is wired to **v3 (the 78%-zero-gradient set), not v10**, and trains at **temp 1.2→0.7 while we calibrated at 1.0** — so the run wouldn't be the calibrated experiment we're approving. Also need to reconcile our "goldilocks = 1–3/8" rule with the code's 2–6/8 band before we call 40% "dead-center." (Goldilocks = 2–6/8 is confirmed correct, not a discrepancy.) Fix those two (≈1 hr) + I'd like the grader's last-number fallback hardened before GRPO optimizes against it, and we're good to go. **Verdict: don't train yet → approve after the 2 blocking fixes.**
