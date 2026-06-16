# AMC-by-coverage: BASE vs v12 depth-0 ckpt-40 — the depth-0-capped test

**Question (TODO gate):** does depth-0 training transfer to external AMC, and is it
"capped" (helps only the concepts it trained) or "general"? Run AMC `mean_pass_rate`
on BASE and on **v12 depth-0 run2 checkpoint-40** (the depth-1 base), split by
`@concept` coverage subset. k=8, temp 1.0, max_new_tokens 2048, n=83.

Data: `results/results_amc_coverage_BASE.json`, `results/results_amc_coverage_ckpt40.json`
(sam, `runs/v12_depth0_run2/amc_coverage/`). BASE banked in #85.

| subset | n | BASE mean | ckpt-40 | Δ mean | BASE pass@8 | ckpt-40 | Δ pass@8 |
|---|---|---|---|---|---|---|---|
| overall | 83 | 0.425 | 0.435 | +0.010 | 0.711 | 0.699 | −0.012 |
| **covered** | 37 | 0.429 | **0.372** | **−0.057** | 0.784 | 0.703 | **−0.081** |
| partner_only | 23 | 0.647 | 0.668 | +0.022 | 0.870 | 0.957 | +0.087 |
| uncovered | 23 | 0.234 | 0.272 | +0.038 | 0.435 | 0.478 | +0.043 |

## Finding: depth-0 does NOT transfer to AMC — it is capped
The expected "capped" signature is a **gain on `covered`** (the concepts depth-0 trained),
flat elsewhere. Instead **`covered` went down** (−0.057 mean, −0.081 pass@8), while the
*untrained* subsets (partner_only, uncovered) ticked slightly up. So it is **neither
"capped-with-gains" nor "general"** — it is **no AMC transfer at all, with a mild
regression on the trained concepts.**

This pairs with the in-distribution signal: **held-out went UP (+0.08)** over the same
run while **external AMC is flat-to-down on covered**. That is the signature of
**learning the synthetic templates/wording reliably, not transferable concept skill**
(Zaid's reframe — now measured on AMC by coverage, not just held-out).

## Noise caveat (so we don't over-read it)
Small subsets (n=23–37), k=8; the eval noise floor is ~±0.05 mean (cf. the step-90
banner-vs-recompute spread). So:
- `partner_only` (+0.02) and `uncovered` (+0.04) are **within noise** — not real gains.
- `covered` −0.057 is ~1σ — **suggestive** of mild over-specialization, not conclusive alone.

Rigorous read: **no AMC gain on any subset, including the concepts depth-0 trained.**

## Verdict
**Depth-0 is capped — it does not transfer to AMC.** The held-out gains were
in-distribution execution, not concept skill that reaches AMC. → **Commit to depth-1
(composition).** The depth-1 calibration campaign (on ckpt-40) is the right lever; the
composition-gap diagnostic on ckpt-40 (running) and the concept-transfer by-framing eval
complete the picture (did depth-0 at least strengthen the atoms / is the held-out gain
wording-robust).
