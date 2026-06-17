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

**Confirmed at scale on the 47 diverse chains** (base on sage vs ckpt-40 iter-2, *same pool*):
mean pass **0.290 → 0.299** (Δ +0.009, nothing), feeder-hit 0.896 → 0.924, gap **+0.606 →
+0.625** (intact, slightly wider), `P(pass|atom-miss) ≈ 0.01 → 0.00`; per-chain 9 up / 10 down
/ 28 flat. The exact 3-composite pattern now holds on 47 diverse chains — depth-0 does not
chain on the full set either, and ckpt-40 is the right base *because* the gap survives in it.

## 3. By-framing: SETTLED — execution reliability, NOT concept consolidation

The base-180 run landed (`runs/concept_transfer_base/`), so the decisive test ran: *does
training flatten the per-concept framing-spread (→ concept consolidation) or leave it
(→ execution/template reliability)?*

| concept | base mean → ckpt-40 | base spread → ckpt-40 spread | read |
|---|---|---|---|
| cdc | 0.221 → 0.315 (**+0.094**) | 0.240 → 0.240 (**Δ 0.00**) | lifted *uniformly*, spread unchanged |
| cmp | 0.510 → 0.485 (−0.025) | 0.323 → 0.292 (−0.031) | mild flatten + slight regression |
| ie3 | 0.373 → 0.396 (+0.023) | 0.104 → 0.125 (+0.021) | slight widen |
| **overall** | **0.368 → 0.399 (+0.031)** | net ~unchanged | — |

**Verdict (settled): the gain is execution reliability on a known method, NOT concept
consolidation.** Training raised the level a touch (+0.031 overall; cdc +0.094 across *all
five* framings equally) but left the wording-sensitivity profile intact — spreads moved
−0.03 / 0.00 / +0.02, i.e. net zero. If the model had genuinely consolidated the concept,
canonical-vs-paraphrase would have converged; it didn't. This is Zaid's reframe (held-out up,
external flat = template/execution reliability) now proven against base, and it closes the
last open trifecta axis. ⇒ **depth-0 is capped on all four axes** (AMC binary, AMC coverage,
composition gap, concept-vs-template).

## 4. Depth-1 calibration campaign: chains sound, convergence partial

Trajectory vs ckpt-40 (target: mean→0.5, goldilocks↑, too-hard↓):

| iter | mean | goldilocks% | too_hard% |
|---|---|---|---|
| 1 | 0.308 | 32.4 | 37.2 |
| 2 | 0.299 | 26.8 | 46.0 |
| 3 | **0.374** | **38.4** | **30.8** |

Noisy (iter-2 dipped) but **iter-3 is the best yet and climbing toward goldilocks** as iter-2's
easing edits land; iter-4 sampling. On this slope it should reach ~0.45 mean / ~45% in-band by
iter-5. The chains are *high quality* — every gold recomputed was exact, nothing ill-posed or
ungradeable. The two causes of the too-hard chains are telling:

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
47-chain set is calibratable, and the autonomous campaign is tuning it toward goldilocks. With
the base-180 by-framing run in (depth-0 = execution reliability, not concept consolidation) and
the composition gap confirmed intact on all 47 chains, **every diagnostic question is now
answered and depth-0 is fully capped on four axes.** The only thing left before the payoff is
the calibration converging — then build the depth-1 train set, train ~300 steps off ckpt-40,
and re-run the gap diagnostic to see if depth-1 closes what depth-0 couldn't.
