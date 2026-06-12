# Depth-1 base composition-gap diagnostic — findings (2026-06-12)

**Run:** combined depth-1 pool, n=300 (~104/96/100 across the 3 composites),
8 rollouts @2048, base Qwen2.5-7B-Instruct, sampled on sam →
`s3://calibrate-rl-agent/runs/chain_depth1_base_diag_300/` (copy:
`data/chain_depth1_base_diag_300.json`). Reproduce:
`python analysis/chain_composition_gap.py data/chain_depth1_base_diag_300.json`.

**Question (§6a):** does base do the atoms but fail to compose? If
`intermediate_hit_rate` (rollout text contains the step-A answer) is high while
final pass is low, the failure is chaining — exactly what depth-1 training
should fix. If both were low, the atoms themselves would be the problem and
depth-1 data could not help.

## Result: the composition gap is real in all three composites

| composite (AMC) | n | mean pass | intermediate hit | gap | P(pass\|hit) | P(pass\|miss) | hit-but-fail |
|---|---|---|---|---|---|---|---|
| cdc→modexp (#55) | 104 | 0.463 | 0.856 (strict 0.790) | +0.39 (+0.33) | 0.534 (0.578) | 0.042 (0.029) | 40% (33%) |
| log_laws→otc (pilot, #41) | 96 | 0.372 | 0.983 | +0.61 | 0.379 | 0.000 | 61% |
| ppd→cdc (#75) | 100 | 0.655 | 0.844 | +0.19 | 0.721 | 0.296 | 24% |

- **Base reliably computes the feeder atom (79–98%) but fails the composite
  much more often.** Between a quarter and 61% of all rollouts compute step A
  correctly and still get the final answer wrong.
- **Getting the atom right is near-necessary:** P(pass | intermediate miss) is
  0.00–0.04 for two composites. (#75's 0.296 is partly a detection artifact —
  some correct rollouts count divisors of N without ever writing N as a bare
  numeral.)
- **Failure modes are genuinely compositional** (spot-checked transcripts):
  correct e=12 then a botched CRT on 3^12 mod 147; correct log=24 then
  stars-and-bars that ignores 0≤a<b<c; correct N=840 then including 10 among
  divisors "less than 10". The model does the steps; it loses the chain.

## Measurement caveats

- Hit detection is text containment with numeric word boundaries. For #55 the
  intermediates are small (4–20), so incidental matches inflate the loose rate;
  a strict chain-aware detector (a^{e} usage or "e = <ig>") gives 0.790 vs
  0.856 and does not change the conclusion. Pilot and #75 intermediates were
  spot-checked as genuine computations.
- This is a **diagnostic against BASE**, per the sequential curriculum decision
  (Faisal): depth-1 training data must be calibrated against the depth-0-trained
  model, which does not exist yet. Nothing here is a train set.

## Incidental calibration read (base, indicative only)

Overall mean pass 0.498; 154/300 in the goldilocks zone. Pilot skews hard
(26 too_hard, mean 0.372); #75 skews easy (30 too_easy, mean 0.655); #55 is
nearly centered (63/104 goldilocks, mean 0.463). Knob direction if the depth-0
model shifts these the way v10 shifted atoms: ease the pilot, tighten #75.

## What this gates (next steps)

1. The make-or-break question (§6a.4) — *does training on compositions transfer
   to compositional AMC?* — now has its precondition confirmed: there is a real
   chaining deficit to train against, not an atom deficit.
2. Depth-1 training remains **curriculum-gated**: train depth-0 first, then
   calibrate these pools against that checkpoint. The depth-0 "final run"
   decision still waits on Michael's by-framing analysis of the
   concept-transfer eval.
3. If the first depth-1 run shows transfer: expand from the 76 feed-legal
   `chain_compat_v2` edges + the 3-way #55 (wire in divisor_sum_filter).
