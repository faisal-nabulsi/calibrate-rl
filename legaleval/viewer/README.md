# LegalEval viewer

A local web UI to browse **prompts → all five model responses → grades**, with an
overview of the eval and inline editing of prompts/rubrics.

## Run

```sh
cd legaleval
pip install -r requirements.txt        # needs flask + markdown (tooling deps)
python -m viewer.app                    # → http://127.0.0.1:5000
```

- **Overview** (sidebar top): what LegalEval is + the overall results ranking.
- **Pick a prompt** (sidebar, grouped by stage A–E): the prompt-centric view —
  a per-prompt score table, then **all five models' responses together**, each
  rendered markdown card showing its score badge, gate status, and the judge's note.
- **Edit** (the "✎ Edit prompt & rubric" disclosure on any prompt page): change the
  prompt text or rubric and **Save** → writes back to `suite/prompts.json` and
  `suite/rubrics/<ID>.json`. Responses/grades are run outputs and are view-only.

## Which run it shows

Auto-detects the newest dir under `runs/` that has both `responses/` and
`grades/claude-opus-4-8/`. Override with `LEGALEVAL_RUN=runs/<id>`. Scores come from
`results/<run>_claude-opus-4-8.csv`; narratives from the per-cell grade JSONs.

> Note: saving re-serializes `suite/prompts.json` with 2-space indent, so an edit
> shows as a whole-file diff. That's expected — review the content diff, not the
> reformat.

## Static exports

`python -m tools.export_docx runs/<run_id> --out ~/Desktop` writes readable
`LegalEval_v7_Grading.docx` and `LegalEval_v7_Prompts_and_Responses.docx`.
