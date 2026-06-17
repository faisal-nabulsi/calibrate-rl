# Depth-0 verdict + depth-1 calibration iter-1 — analysis (2026-06-17)

Three jobs landed overnight, all sampled @2048 against the depth-1 base
**ckpt-40** (`runs/v12_depth0_run2/checkpoint-40`). This reads them as a set.

| job | box | what it is | output |
|---|---|---|---|
| `chain_depth1_ckpt40_diag` | sam | composition-gap diagnostic on ckpt-40 (re-run of the 06-12 base diag) | `runs/chain_depth1_ckpt40_diag/calib.json`, 300 rows |
| `concept_transfer_ckpt40` | sage | by-framing eval — is the held-out gain wording-robust (concept) or template-bound? | `runs/concept_transfer_ckpt40/calib.json`, 180 rows |
| `depth1_calib_iter1` | sadie | first calibration iteration of the 47-chain pool vs ckpt-40 | `runs/depth1_calib_iter1/calib.json`, 250 rows |

Reproduce: `python analysis/chain_composition_gap.py /path/to/chain_ckpt40.json`.

---

## TL;DR

1. **Depth-0 training did not close the composition gap.** ckpt-40 fails to chain
   exactly as much as base did — same gap, same near-zero pass when the atom is
   missed, overall calibration on the 3 composites unchanged (mean pass
   0.498→0.475, goldilocks 154→147 / 300). Consistent with the AMC-capped finding
   (#89). The deficit depth-1 training targets is real and still wide open.
2. **By-framing is suggestive but not conclusive.** ckpt-40 shows moderate wording
   sensitivity (per-concept spread 0.12–0.29); two of three concepts drop ~0.13–0.15
   from the canonical wording to paraphrases, one improves. On the 14 problems shared
   with the base run, ckpt-40 is +0.40 over base and the gain holds on a non-canonical
   framing — leaning "partly concept, not pure template." **No base run exists on the
   full 180-row v2 set, so the discriminator is not fully settled.**
3. **Depth-1 calibration iter-1 skews hard.** Against ckpt-40 the 47-chain pool is
   32% in-band (81/250), mean pass 0.308; **21/47 chains are too hard (mean <0.20),
   only ~5 sit in the goldilocks band, 6 are too easy.** Compositions skew hard exactly
   as predicted. The loop must ease the hard chains and tighten the easy value-producers.
   **iter-2 is re-sampling an identical pool — no chain-layer edit has been applied yet.**

---

## 1. Composition-gap diagnostic — ckpt-40 vs base

**What it measures.** For each rollout, did the model's text compute the *feeder
atom* (step A) correctly — the `intermediate_hit_rate` — and did it pass the *full
composite*? If hit-rate is high but pass-rate is low, the model can do the steps but
can't chain them. That "gap" is what depth-1 training is supposed to fix. This is the
identical 3-composite pool sampled against base on 06-12, now re-run against ckpt-40,
so it is a clean base→ckpt-40 delta.

| composite | n | mean pass (base→ckpt40) | intermediate-hit, loose (base→ckpt40) | gap | P(pass\|hit) | P(pass\|miss) |
|---|---|---|---|---|---|---|
| cdc→modexp (#55) | 104 | 0.463 → **0.474** (+0.01) | 0.856 → 0.903 | +0.39 → +0.43 | 0.534 → 0.523 | 0.04 → 0.01 |
| log_laws→otc (pilot) | 96 | 0.372 → **0.342** (−0.03) | 0.983 → 0.987 | +0.61 → +0.65 | 0.379 → 0.347 | 0.00 → 0.00 |
| ppd→cdc (#75) | 100 | 0.655 → **0.603** (−0.05) | 0.844 → 0.800 | +0.19 → +0.20 | 0.721 → 0.708 | 0.30 → 0.18 |

**Reading.**
- **The gap did not close; if anything it widened slightly.** On every composite the
  gap (hit − pass) is the same or larger after depth-0 training. P(pass | atom missed)
  stays ~0 on two of three — getting the atom right is still near-necessary and far from
  sufficient.
- **The atoms were not strengthened for chaining.** Feeder-hit moved +0.05 (#55), flat
  (pilot, already saturated at 0.99), and −0.04 (#75) — mixed and within noise. ckpt-40
  is not noticeably better at the standalone step-A computation than base.
- **Overall calibration on these composites is unchanged**: mean pass 0.498→0.475,
  goldilocks 154→147 / 300. The strict detector for #55 (a^e usage, guards against
  incidental matches on the small intermediates) gives hit 0.858 / gap +0.385 — same
  conclusion as loose.

**Verdict.** Depth-0 (ckpt-40) is not the lever for composition — it does not transfer to
chaining, matching #89's AMC-capped result. The flip side is that the precondition for
depth-1 training is re-confirmed *against the actual depth-1 base*: there is a genuine
chaining deficit to train against, not an atom deficit.

---

## 2. Concept-transfer by-framing — ckpt-40

**What it measures.** Three depth-0 concepts (cdc, cmp, ie3) each rendered in 5
surface framings — `A_original` (canonical generator wording), plus `B_wordproblem`,
`C_setbuilder`, `D_scenario`, `E_paraphrase`. If ckpt-40 truly learned the *concept*,
pass rate should be roughly flat across framings; if it learned a *template*, the
canonical wording should beat the paraphrases. This is the discriminator for "is the
+0.22/+0.08 held-out gain real skill or memorized wording."

**ckpt-40, mean pass per concept × framing (n=12 each):**

| concept | A_original | B_wordprob | C_setbuilder | D_scenario | E_paraphrase | spread |
|---|---|---|---|---|---|---|
| cdc | 0.417 | 0.219 | 0.365 | 0.177 | 0.396 | 0.240 |
| cmp | 0.604 | 0.312 | 0.521 | 0.438 | 0.552 | 0.292 |
| ie3 | 0.354 | 0.479 | 0.417 | 0.375 | 0.354 | 0.125 |

Canonical vs the mean of the 4 novel framings: cdc **+0.13**, cmp **+0.15**, ie3 **−0.05**.

**Reading.**
- There is real wording sensitivity (spread 0.12–0.29), but **no clean template
  collapse.** Two concepts lose ~0.13–0.15 going from the canonical wording to
  paraphrases; ie3 actually does slightly *better* on novel wordings. A purely
  template-bound model would drop uniformly and sharply on every paraphrase — it does not.
- The weakest framings are `B_wordproblem` and `D_scenario` (narrative embeddings),
  not paraphrase-as-such — the model loses accuracy when the problem is wrapped in a
  story, less so when it's merely reworded.

**The 14-problem base anchor (weak, directional).** The new v2 set has no base run, but
14 of its problems (12 ie3, 2 cmp) are textually identical to the old base
concept-transfer set, so a small base→ckpt-40 delta is computable:

| framing | n | base | ckpt-40 | Δ |
|---|---|---|---|---|
| ie3 A_original | 6 | 0.208 | 0.562 | +0.354 |
| ie3 B_wordproblem | 6 | 0.125 | 0.625 | **+0.500** |
| cmp A/B | 2 | 0.000 | 0.250 | +0.250 |
| all 14 | | 0.143 | 0.545 | +0.402 |

The gain is large and — crucially — **at least as large on the non-canonical
`B_wordproblem` framing (+0.50) as on the canonical one (+0.35).** That points toward
the held-out gain being partly concept-level, not pure template memorization. But n=14
(almost all ie3) is far too small to settle it.

**Verdict.** Leans "partly real concept skill," contradicting a strict
template-memorization story, but it is not a clean win and the sample is thin.
**To actually settle the discriminator, run base on the full `concept_transfer_eval_v2.json`
(180 rows) so the by-framing delta is measured at full power.** Until then the "final
depth-0 run" decision should stay held — though #89 likely makes it moot, since even if
the gain is concept-level on held-out, it does not reach AMC.

---

## 3. Depth-1 calibration — iter-1 (sadie, vs ckpt-40)

**What it measures.** First pass of the autonomous campaign: sample the 47-chain pool
(250 problems, ~5–6 per chain, 8 rollouts each) against ckpt-40 and see where each chain
lands relative to the goldilocks 45–55% pass band. Out-of-band chains are what the
campaign's headless-edit step then adjusts.

**Aggregate:** mean pass **0.308**, in-band **81/250 (32%)**. Zone counts:
too_hard 93, borderline 53, goldilocks 81, too_easy 23. **The pool skews hard** — exactly
the "compositions skew hard" prediction.

**Per-chain bands** (mean pass over each chain's ~5 samples — *noisy per chain, robust in
aggregate*): **21 too hard (<0.20), 15 hard-ish (0.20–0.45), 5 goldilocks (0.45–0.55),
6 too easy (>0.80).**

The 5 already near-band (leave alone): `geo_first_exceed__equalization_fraction` 0.48,
`count_pythagorean__algebraic_system_2eq` 0.50, `point_rotation__modular_exponent` 0.50,
`arith_term_filter__constrained_digit_count` 0.52, `mean_removal__modular_exponent` 0.53.

The 6 too easy (tighten — mostly value-producer→easy-target chains the model aces):
`trapezoid_area__algebraic_system_2eq` 0.81, `unit_conversion_area__perfect_square_divisible`
0.86, `percent_compound__algebraic_system_2eq` 0.88, `custom_binary_op__perfect_square_divisible`
0.93, `log_laws__complement_prob_mn` 0.95, `three_number_system__inclusion_exclusion_3set` 1.00.

The hardest (need the most easing) — 5 chains with **zero** in-band samples and mean ~0:
`alternating_cubes__multi_constraint_square`, `inclusion_exclusion_3set__modular_exponent`,
`perfect_square_divisible__telescoping_mn`, `vieta_sumcubes__inclusion_exclusion_3set`,
`divisor_sum_filter__modular_exponent`. The too-hard cluster concentrates on a few hard
*targets* — `telescoping_mn`, `inclusion_exclusion_3set`, `modular_exponent`,
`algebraic_system_2eq` — suggesting the difficulty is target-driven, not feeder-driven.

**Margin-check chain (kathryne's catch).** `box_diagonal_sq__perfect_square_divisible`
lands at mean 0.21 (3 samples: 0.0, 0.0, 0.625). The TODO requires its goldilocks fraction
≥ 0.71 to clear the in-band-yield ≥150 bar (ceiling ≈210). At this difficulty it is well
short. The fix must be **target-side** (widen `perfect_square_divisible` / quota-shrink /
reassign), never the `box_diagonal_sq` feeder (desyncs v12 calib + run-2). Needs more
samples to estimate the fraction reliably — read it off a later converged iteration.

**Flag — iter-2 is re-sampling an identical pool.** `depth1_calib_iter2/pool.json` is
byte-identical to iter-1's (md5 match), and iter-2 is currently sampling (~7/250, ETA ~6h).
That means **no chain-layer edit was applied between iter-1 and iter-2** — the calibration
loop has not yet acted on iter-1's hard skew. Either the headless-edit step produced no
changes or the campaign restarted the iteration without editing (cf. the known
SAMPLE_TIMEOUT_MIN self-kill / no-resume issue). Worth confirming the edit step is firing
before burning another ~6h L4 iteration on the same pool.

---

## What to change

1. **Commit to depth-1; stop spending on depth-0 as a composition lever.** The diagnostic
   confirms ckpt-40 does not chain better than base — depth-0 is capped on AMC (#89) *and*
   on composition. The depth-1 plan stands; ckpt-40 is the right base precisely because the
   gap is intact in it.
2. **Settle the by-framing discriminator properly:** dispatch base on
   `concept_transfer_eval_v2.json` (180 rows) so the gain is measured at full power instead
   of off 14 mostly-ie3 problems. Low priority — likely moot given #89, but it closes the
   open "concept vs template" question cleanly.
3. **Calibration loop:** the pool skews hard (21/47 too hard, only 5 in-band). The campaign
   should ease the hard chains (fewer/smaller steps on the hard *targets* — telescoping_mn,
   ie3, modexp, algebraic_system_2eq) and tighten the 6 too-easy value-producer chains.
   First **verify the headless-edit step is actually running** — iter-2 is sampling an
   unchanged pool.
4. **box_diagonal_sq__perfect_square_divisible** is the one margin-check risk; fix
   target-side once the campaign produces a stable goldilocks fraction for it.

— [gilbert]
