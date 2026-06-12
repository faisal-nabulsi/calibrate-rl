# Auto-calibrator — design

> Design home for the auto-calibration loop. The **Phase-0 design** (§2a knob
> externalization, §2b machine-readable calibration report, §2c CPU-only static
> checks) was agreed in the 2026-06-10 #calibrate-rl-agents thread and is
> documented in the descriptions of PRs #15 / #16 / #17; it is not duplicated
> here. This file was created to hold Addendum A (the Workstream-B instruction
> named it as the design home); the Phase-0 sections can be backfilled from the
> PR descriptions if anyone wants them in-repo.

---

## Addendum A — depth-1 chaining (Workstream B, 2026-06-12, gilbert)

Status: **design for review — no generator code until this is approved.**
Inputs: `generate/chain_skeletons_v2-v4.py` post-mortem (Slack, 2026-06-12),
`data/chain_compat_v1.json` (PR #37), `data/calib_v12_2048_7B.json`.

### A.1 Chain semantics: answers parameterize, oracles compose

A composite `A → B` is built by generating A normally, taking its **gold
answer** `g_A`, feeding `g_A` into one designated feedable param of B, then
generating B. Each concept's own oracle computes its gold, so the composite's
gold is B's oracle output — **exact by construction**. No math is re-derived
and no LLM touches the gold path. This replaces the v2–v4 approach of
hand-writing each pair's prose and re-implementing both concepts' math inline
(which drifted from the v12 generators and capped us at a handful of pairs).

- **Feed legality** comes from `data/chain_compat_v1.json`: an `(A, B, param)`
  edge is valid iff A's calib answer distribution lands in B's knob *envelope*
  with `frac_in_envelope ≥ 0.5` and `distinct_in_envelope ≥ 5` (the distinct
  floor guards the v2 intermediate-collapse failure: N∈4..7 = 4 memorizable
  intermediates). 16 of 102 edges qualify today.
- **Resample-on-incompatible:** when a drawn A yields `g_A` outside the fed
  param's envelope, resample A. The `frac ≥ 0.5` rule keeps this
  non-degenerate. Edges with semantic caveats (e.g.
  `constrained_divisor_count.num_pool` expects highly-composite numbers)
  additionally resample until the fed value satisfies the caveat predicate.
- **Surface text embeds, never announces** (v3's load-bearing fix): B's
  scenario refers to A's quantity descriptively ("...a threshold equal to the
  number of valid triples..."), with no "First find X. Then..." recipe — the
  model must *infer* that step 1 feeds step 2, which is the AMC skill.

### A.2 Every composite is a NEW concept in the loop

- Name and `skeleton_type`: `chain_<A>__<B>` (double underscore separates the
  components). `@concept`-style AMC tags ride on the composite.
- Knob file: `automation/calibrator/knobs/chain_<A>__<B>.json` = A's params
  (prefixed `a_`) ∪ B's params minus the fed one (prefixed `b_`), with each
  param's `envelope` / `knob_class` / `type` carried over **verbatim**. The
  existing `knob_loader` machinery then applies unchanged: envelope walls,
  num-class-no-widening, and `locked` are enforced mechanically on composites
  exactly as on atoms.
- The loop calibrates a composite like any concept. The §2c static gate also
  applies as-is — notably, v3's "second op collapses the answer space" failure
  mode (divisor-count/angle-sum chains with ≤20 distinct answers) is caught by
  the existing `answer_top3_share` / `answer_entropy` checks; no new mechanism
  needed.
- **Difficulty knob = number of steps / constraint count, never number size**
  (CLAUDE.md §4). Composites skew hard, so the loop's sanctioned easing moves
  are: narrow a C-class knob, drop a constraint, or fall back to the easier-A
  pairing — never shrink-then-rewiden numbers.

### A.3 First-pass pairing: easy-A × mid-B

Composites skew hard, and too-hard problems are ghost batches (zero GRPO
gradient). So the first wave pairs a **high-pass A** (the model reliably clears
step 1, difficulty comes from the composition itself) with a **mid-band B**.
From `calib_v12` mean pass rates: easy-A pool = `log_laws` (1.00 — the v11
representation bug is fixed in v12), `constrained_divisor_count` (0.80);
mid-B pool = `triangular_filter_count` (0.49), `ordered_triple_constraint`
(0.44), `inclusion_exclusion_3set` (0.33). `constrained_subset_count` (0.15)
is excluded as a B until the loop eases it.

Recommended first-wave composites (all edges valid in `chain_compat_v1`):

| composite | edge | A pass | B pass | why |
|---|---|---|---|---|
| `chain_log_laws__ordered_triple_constraint` | `→ N` (frac .90, 10 distinct) | 1.00 | 0.44 | cleanest easy×mid; both S/num well-behaved |
| `chain_constrained_divisor_count__ordered_triple_constraint` | `→ N` (frac .84, 9 distinct) | 0.80 | 0.44 | easy×mid AND exercises the #55/#75 ingredient as a chain component |
| `chain_complex_modulus_power__constrained_divisor_count` | `→ gt_thresholds` (frac 1.0, 14 distinct) | 0.60 | 0.80 | B is the #55/#75 ingredient; B's other knobs give the loop room to tighten |

### A.4 Intermediate-step logging; reward stays end-to-end

Each generated row stamps chain metadata:
`"chain": {"A": ..., "B": ..., "fed_param": ..., "intermediate_gold": g_A}`
(alongside the existing `knobs` stamp from PR-2 draw recording). At
sampling/calibration time we compute a per-problem `intermediate_hit_rate` —
whether each rollout's text contains `g_A` (same extraction discipline as the
grader, applied to the intermediate value; a heuristic, logged as such). This
separates "failed step A" from "failed the composition" in the report, which
is the diagnostic the depth-0 → depth-1 transition needs.

**The reward is end-to-end on the final gold ONLY.** No partial credit for a
correct intermediate: shaping on `g_A` would reward solving A without
composing — recreating depth-0 inside the depth-1 dataset.

### A.5 AMC transfer targets: #55 and #75

Recipes (§5/§6): **#55** = `modular_exponent` × `constrained_divisor_count` ×
`divisor_sum_filter`; **#75** = `constrained_divisor_count` ×
`prime_power_divisors`. Of these ingredients only `constrained_divisor_count`
is knob-wired today — which is also the compat map's best feed *target* (13 of
the 16 valid edges involve it, all tagged `amc_targets: [55, 75]` in the
artifact).

- **Prerequisite for the true target composites:** knob-wire
  `modular_exponent`, `divisor_sum_filter`, and `prime_power_divisors`
  (same PR-1 recipe — externalize literals, envelopes, equivalence test).
  Then the intended pairs are `chain_modular_exponent__constrained_divisor_count`
  (#55, two of its three ingredients) and
  `chain_constrained_divisor_count__prime_power_divisors` (#75, complete).
- **Available today** (plausibly compose toward the targets in the meantime):
  the `X → constrained_divisor_count.gt/lt_thresholds` edges
  (X ∈ log_laws, complex_modulus_power, ordered_triple_constraint,
  triangular_filter_count, constrained_subset_count) and
  `constrained_divisor_count → ordered_triple_constraint.N` /
  `log_laws.e1/e2` — these train the model to *use* divisor-count reasoning
  inside a larger problem, the composition skill #55/#75 test.
- Eval: `mean_pass_rate` on the tagged AMC subset (per §8), and confirm the
  depth-1-partner-only set doesn't regress (the v10 −2 watch item).

### A.6 Open questions for review

1. Depth-1 pilot: §6 names `constrained_subset_count` (already a composition)
   as the pilot. Its v12 pass is 0.15 (too-hard band) — pilot it as written,
   or ease it via the loop first?
2. 3-way chains (#55 wants three ingredients): out of scope for v1
   (pairs only), or design the metadata to allow `chain_A__B__C` now?
3. `intermediate_hit_rate` text-scan heuristic: acceptable as a diagnostic, or
   does someone want a stricter definition before it lands in the report?

**STOP point: the v1 chaining generator is not built until this addendum is
reviewed (Faisal's call).**
