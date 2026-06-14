# LegalEval Harness

Automated runner + grader for the **LegalEval v7** benchmark: 14 prompts across 5
stages (A: issue-spotting, B: summarization/extraction, C: redlining,
D: drafting, E: negotiation), 189 points total, graded against per-prompt rubrics
with Faithfulness/Directionality gates.

Spec lives in Google Drive (`LegalEval_Complete_v7_clean.docx` + companion docs,
incl. `LegalEval_Prompt_Authoring_and_Grading_Guidelines_v7`).
**This repo's `suite/prompts.json` + `suite/rubrics/` are the machine-readable
source of truth** — rubric fixes land here and are version-stamped into every run.

## Pipeline

```
suite/prompts.json ─▶ harness/generate.py ─▶ runs/<id>/responses/   (models under test, INCOGNITO)
                      harness/grade.py    ─▶ runs/<id>/grades/      (Opus 4.8 judge, k=3, structured outputs)
                      harness/score.py    ─▶ results/<id>.csv       (normalize + 0.40 gate cap, pure python)
                                            results/<id>_confirm_queue.json  (gate trips for human review)
```

```sh
pip install -r requirements.txt
cp .env.example .env   # fill in keys
python -m harness.generate                 # all models x all prompts
python -m harness.grade runs/<run_id>      # judge
python -m harness.score runs/<run_id>      # score matrix + confirm queue
```

## Design rules

- **Incognito generation.** Models under test get the bare prompt: no system
  prompt, no tools, no memory, single stateless turn. Identical treatment for all
  5 models. (Closes the context-bleed channel that tripped Muse Spark on A1.)
- **The judge is not incognito.** Opus 4.8 grader sees rubric + gold key.
- **Grade the instance, not the world** (v6 §6 source-agnostic grading) — baked
  into the grader instructions.
- **LLM scores dimensions; code does math.** Normalization and the 0.40 gate cap
  live in `score.py`, never in the judge.
- **k=3 judge samples**, median per dimension, majority vote per gate; borderline
  gate calls go to the human-confirm queue instead of silently capping.
- **Replayable.** `runs/` artifacts are committed; re-grade old responses after a
  rubric fix or judge swap without regenerating.
- **Self-grading caveat.** A Claude-family judge scores Claude Sonnet 4.6 —
  cross-check by re-running `grade.py` with a second judge on the same responses.

## v7 notes

- **Prompts + rubrics are extracted from `LegalEval_Complete_v7_clean.docx`.**
  A1/A2/C2 `prompt_text` is the v7 OPEN (existence-neutral) variant — the
  headline score. The DIRECTED (v6) phrasing and B3's uninstructed A/B live in
  each prompt's `variants`; run them with `generate.py --variant directed`
  (or `uninstructed`) for the spontaneous-vs-prompted delta.
- **Finding classification (§6.2a).** Detection/diagnosis responses get each
  reported concern tagged GOLD-MATCHED / DEFENSIBLE-UNGRADED / FALSE-MISATTRIBUTED
  keyed to a gold-unit ID. Coverage counts only gold-matched; Faithfulness
  penalizes only false-misattributed; `score.py` reports the precision norm so
  shotgunning concerns costs something.
- **Stable gold-unit IDs** (`task.unit-type.slug`, ~93 across the suite) live in
  `gold_unit_ids` on every prompt and rubric; the judge keys findings to them.

## Status / TODO

- [ ] Implement remaining providers: GPT 5.5, Gemini 3.1 Flash, Qwen 3.7 Plus,
      Muse Spark (`harness/providers/`)
- [ ] Cross-family grading: run `grade.py --judge gpt-5.5` beside the Opus run;
      `score.py` flags gate disagreements. Compute κ on the calibration set.
- [ ] Validate: re-grade the June 9 manual A1/A2 runs and confirm the harness
      reproduces the hand scores
- [ ] Clean-instance siblings (§3 of the Guidelines) for A1/A2/C2
- [ ] Optional: Batches API path for grading (50% cost), HTML report
