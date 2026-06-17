# CalibrateRL — Full-Program Retrospective (transcript-grounded)

> Synthesis across every experiment run to date, grounded in the actual rollout
> transcripts (not just summary stats). Compiled 2026-06-16 [faisal]. Data lives in
> `s3://calibrate-rl-agent/runs/` + `results/`; this doc is the unified read.

## The one finding everything agrees on

**The model's wall is composition + final-step execution — NOT atomic concept
knowledge.** Five independent experiments, each from a different angle, converge on the
same place. Depth-0 training bought real *execution reliability on methods the model
already knew*, but none of it transfers to what AMC actually requires (chaining steps).
That is the entire case for the depth-1 pivot, and it now holds on transcripts, not just
aggregate metrics.

---

## 1. Depth-0 → AMC: capped, and half the "gain" is an artifact

Binary AMC (per-problem JSON, n=83): **base 32 / v10 ckpt-120 34 / v12 ckpt-40 35.**
The +3 looks like progress until you read the flips (8 up, 5 down; net +3):

- **4 of 8 UP flips (#42, #47, #66, #82) are pure termination fixes** — base *computed
  the right answer* but hit the 2048-token wall before boxing it. None-preds: base
  **21/83 → ckpt-40 1/83**. Not new capability.
- The other 4 up-flips (#21, #32, #55, #68) are genuine, all on depth-0-*covered*
  concepts.
- **All 5 DOWN flips are late-stage execution regressions** on problems base had right —
  #69 derives `√29/2` then boxes `31` (transcription failure); #60 factors to `243×10¹⁵`
  then miscounts it as a 17-digit number.

By-coverage mean_pass (#89) moves within ±0.05 noise on every subset. Net = ~4 real
concept gains offset by ~5 execution regressions.

**Verdict: depth-0 is capped, no broad AMC transfer.** The real, measurable effect was
answer-termination reliability — off-target for AMC. The remaining 43 both-wrong problems
are dominated by wrong-method and compositional failures that atomic training doesn't touch.

## 2. Composition gap: real, and *intact* (slightly wider) in ckpt-40

The load-bearing result. Feeder atom computed correctly 80–99% of rollouts; full composite
pass flat-to-down:

| composite | base pass | ckpt-40 pass | gap (base→ckpt-40) |
|---|---|---|---|
| cdc→modexp (#55) | 0.463 | 0.474 | +0.39 → **+0.43** |
| log_laws→otc (pilot) | 0.372 | 0.342 | +0.61 → **+0.65** |
| ppd→cdc (#75) | 0.655 | 0.603 | +0.19 → **+0.20** |
| **overall** | **0.498** | **0.475** | gap widened on all 3 |

`P(pass | atom-miss) ≈ 0` on two chains — atom knowledge necessary, nowhere near
sufficient. Chaining-failure taxonomy from transcripts:

- **Botched second-leg arithmetic** — correct exponent `e=8`, then `62×105 = 6470` (=6510).
- **Dropped the chained constraint** — correct `log = 21`, then stars-and-bars ignoring
  the `a<b<c` ordering → 253 instead of 37.
- **Off-by-one in the second count** — correct `N = 720`, divisor list right, miscount.

**Base and ckpt-40 fail identically.** Depth-0 nudged feeder-hit up (0.856→0.903) without
touching the hand-off; P(pass|hit) unchanged. "Can do the steps, can't chain them" is
literally what the transcripts show. **Depth-1 is justified.**

## 3. By-framing: "partly concept, mostly reliable-execution — not pure template"

Moderate confidence (~65%). Both signals present (ckpt-40, 180 rows):

| concept | A_orig | B_word | C_setbld | D_scen | E_para | spread |
|---|---|---|---|---|---|---|
| cdc | 0.417 | 0.219 | 0.365 | 0.177 | 0.396 | 0.240 |
| cmp | 0.604 | 0.312 | 0.521 | 0.438 | 0.552 | 0.292 |
| ie3 | 0.354 | 0.479 | 0.417 | 0.375 | 0.354 | 0.125 |

- **Concept signal:** paraphrase-E ≈ canonical-A; hard problems fail ~0.00 and easy ones
  pass ~1.0 *uniformly across all 5 framings* (difficulty dominates the tails, not wording).
- **Template signal:** cdc/cmp spread 0.24–0.29; deep recasts (word-problem, scenario) cost
  ~0.15; the *same* divisors-of-5280 problem is solved by three different (all wrong) methods
  in three framings — wording-conditioned method selection, not a stable procedure.
- ckpt-108 base-vs-trained: the +0.03 gain is cdc execution reliability (switches to the
  cleaner complement method, fewer enumeration slips) — Zaid's reframe confirmed.

**Not fully settled** — the base-180 run (dispatched 06-16, `runs/concept_transfer_base/`)
is the decisive test: if training *flattens* the per-concept spread vs base → concept
consolidation; if spread is equal-or-wider → canonical-form memorization. Final depth-0-run
decision stays on hold until that lands.

## 4. Depth-1 calibration campaign: chains sound, convergence partial

iter-1 (250×8 vs ckpt-40): **32% goldilocks, 37% too-hard, 0/47 in the strict 0.45–0.55
band; overall mean pass 0.308.** But the chains are *high quality* — every gold recomputed
was exact, nothing ill-posed or ungradeable. The two causes of the too-hard chains are telling:

- **Feeder-step bottleneck** — the composition gap *again* (on
  `divisor_sum_filter__modular_exponent` only 2/8 rollouts produce the right intermediate).
- **Arithmetic explosion** — telescoping chains where the fed term-count makes `m+n` blow up
  (V=13 → 166331); tedium, the §5 anti-pattern. Curable by capping the fed value.

The campaign's committed edits are correct calibration moves: **all target-side, depth-0
feeders frozen by the equivalence test, 5 dedupe-breaking edits auto-reverted.** iter-2
re-sampled on the eased generators (06-16).

**Outlook:** most of the 21 too-hard chains should pull into [0.25,0.75], but ~6 chains fail
dedupe from *feeder-limited intermediate diversity* — outside the chain-layer edit lane, so a
manual feeder-diversity pass will be needed to finish.

---

## Two cross-cutting observations

1. **The composition gap is recursive.** It's not only an AMC story — it reappears *inside*
   the depth-1 chains (the hardest chains are hard because the feeder atom is unreliable). So
   depth-1 training must lift both the chaining hand-off *and* the harder feeders' execution —
   which is exactly what training on composites (exercising both) should do.

2. **Repo-hygiene gaps found during the sweep** (conclusions sound but not reproducibly banked):
   - `results/depth1_ckpt40_trifecta.md` — the #107 trifecta write-up is **not in the repo or
     git history**.
   - `results/amc_coverage_base_vs_ckpt40.md` + `results_amc_coverage_ckpt40.json` — the #89
     *ckpt-40* coverage numbers aren't banked (only the BASE baseline is).
   - Several `results/*.json` show as deleted (`D`) in the working tree.

   Raw data survives in S3, so analyses are recoverable, but the write-ups should be committed.

## Bottom line

Every experiment points one way: **atom knowledge is solved; the ceiling is composition and
final-step execution.** ckpt-40 is the right depth-1 base (atoms reliable, gap intact), the
47-chain set is calibratable, and the autonomous campaign is tuning it toward goldilocks. The
one open empirical question is concept-vs-template, which the in-flight base-180 by-framing run
will close.
