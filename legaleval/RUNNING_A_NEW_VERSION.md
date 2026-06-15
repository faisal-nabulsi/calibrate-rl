# Running a new LegalEval version

The harness runs off two **machine-readable** files: `suite/prompts.json` and
`suite/rubrics/*.json`. A new spec version (vN) ships as a Google Doc / `.docx`,
so the first job is always **extraction** — turn the doc into those JSON files —
*then* generate / grade / score. Don't point the runner at a `.docx`; it only
reads the JSON.

```
LegalEval_Complete_vN_clean.docx
        │  (1) EXTRACT  — LLM-assisted, human-checked
        ▼
suite/prompts.json  +  suite/rubrics/<ID>.json   ← source of truth the harness reads
        │  (2) generate → (3) grade → (4) score
        ▼
runs/<id>/responses → runs/<id>/grades → results/<id>.csv
```

## 1. Extract prompts + rubrics from the new spec  (do this FIRST)

1. Drop the new doc in `suite/source/` (e.g. `LegalEval_Complete_vN_clean.docx`,
   plus a `*_raw.md` text dump for diffing).
2. Have a model read the doc and produce, for **every** prompt:

   **`suite/prompts.json`** — top-level keys `suite`, `rubric_version` (set to
   `"vN.0"`), `total_points`, `stage_totals`, `stage_weights`, `notes`, and
   `prompts: [...]`. Each prompt object needs:
   `id`, `stage`, `name`, `max_points`, `gates` (e.g. `["faithfulness",
   "directionality"]`), `source_type`, `source_contract`, `rubric_file`
   (`rubrics/<ID>.json`), `prompt_text` (the exact paste block the model sees —
   headline/OPEN variant), `status`, `extracted_from`, `gold_unit_ids`
   (stable `task.unit-type.slug` IDs), `rubric_version`, and `variants`
   (`directed_text` / `uninstructed_text` where the spec defines them).

   **`suite/rubrics/<ID>.json`** — one per prompt: `id`, `max_points`, `gates`,
   `rubric_version`, `provenance`, `gold_unit_ids`, `source`, and
   `rubric_markdown` (the full per-criterion gold key the judge reads).

3. **Human-check the extraction** — gold criteria, gates, point totals, and
   `gold_unit_ids` are load-bearing (a bad gold key silently corrupts every
   score). Confirm `total_points` and `stage_totals` match the spec.
4. Bump `rubric_version` consistently in `prompts.json` and every rubric — it's
   stamped into every run record for replayability.

> Tip: the canonical spec lives on Google Drive (`LegalEval_Complete_vN_clean.docx`
> + the Prompt-Authoring & Grading Guidelines). Pull the latest before extracting.

## 2. Keys

`cp .env.example .env` and fill in the five model keys (+ optional `*_MODEL` /
`*_BASE_URL` overrides). See `.env.example` for which key drives which model and
the grader. `.env` is gitignored — never commit it.

## 3. Generate → grade → score

```sh
pip install -r requirements.txt

# generate: every registered model x every prompt (incognito; one stateless call each)
python -m harness.generate                 # add --models / --prompts / --n to scope
                                           # --variant directed|uninstructed for alt phrasing

python -m harness.grade  runs/<run_id>     # default judge = Opus 4.8 (claude-opus-4-8)
python -m harness.grade  runs/<run_id> --judge gpt-5.5   # cross-family control (run both)

python -m harness.score  runs/<run_id>     # score matrix + human-confirm queue
```

A run aborts nothing on a single model's failure — `generate.py` records the
error per cell and continues, then prints a `FAILED — …` summary at the end.

## 4. Validate

Re-grade the prior version's hand-scored prompts and confirm the harness
reproduces them before trusting new numbers. For small (1–3 prompt) changes,
compare per-dimension `mean_pass`/gate rates, not just totals.
