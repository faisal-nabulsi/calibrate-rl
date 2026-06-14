"""Manual-run workflow for models under test that have no API access.

Two subcommands:

  export — write a paste worksheet for one model:
      python tools/manual_run.py export --model muse-spark
      python tools/manual_run.py export --model muse-spark --prompts A1,B2

  ingest — parse the filled-in worksheet into harness response records:
      python tools/manual_run.py ingest manual/muse-spark_sheet.md
      python tools/manual_run.py ingest manual/muse-spark_sheet.md --run-id 2026-06-11T09-00-00

After ingest, grade and score exactly like an API run:
      python -m harness.grade runs/<run_id>
      python -m harness.score runs/<run_id>

Records match harness/generate.py's shape, except isolation is stamped
"manual-incognito" (web UI, not a bare API call) so the weaker isolation is
auditable in every downstream artifact. Pass --run-id to ingest into the same
run directory as an API-generated run (or another model's sheet) so all five
models grade and score together.
"""

import argparse
import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUITE = ROOT / "suite" / "prompts.json"
SHEETS = ROOT / "manual"
RUNS = ROOT / "runs"

# Models under test with no implemented provider (see harness/providers/__init__.py).
KNOWN_MODELS = ["gpt-5.5", "gemini-3.1-flash", "qwen-3.7-plus", "muse-spark"]

ISOLATION = ("manual-incognito (web UI: temp/incognito chat, memory+personalization off, "
             "tools/web search off, one fresh chat per prompt)")

# Sentinel markers chosen so no model response will ever contain them.
PROMPT_MARK = "<<<<< LEGALEVAL PROMPT {pid} — copy everything below into ONE fresh temp chat >>>>>"
RESPONSE_MARK = "<<<<< LEGALEVAL RESPONSE {pid} — paste the model's FULL raw reply below this line >>>>>"
MARK_RE = re.compile(r"^<<<<< LEGALEVAL (PROMPT|RESPONSE) ([A-E][123]) [^>]*>>>>>\s*$")

CHECKLIST = """\
INCOGNITO CHECKLIST — do this BEFORE every prompt (v6 design rule: incognito generation)

  [ ] Temporary / incognito chat mode ON (no history, no training)
  [ ] Memory & personalization OFF (and no custom instructions / profile facts)
  [ ] Web search, tools, file upload, connectors all OFF
  [ ] ONE FRESH CHAT PER PROMPT — never reuse a conversation
  [ ] No edits, no regenerate, no follow-ups: keep the FIRST complete reply
  [ ] Copy the ENTIRE raw response (use the UI's copy button if it has one)

Then paste each reply under its RESPONSE marker below. Leave a section blank to
skip that prompt (ingest will ignore it). Do not edit the marker lines.
"""


def load_suite() -> dict:
    return json.loads(SUITE.read_text())


def cmd_export(args: argparse.Namespace) -> None:
    suite = load_suite()
    prompts = suite["prompts"]
    if args.prompts:
        wanted = set(args.prompts.upper().split(","))
        missing = wanted - {p["id"] for p in prompts}
        if missing:
            raise SystemExit(f"unknown prompt ids: {', '.join(sorted(missing))}")
        prompts = [p for p in prompts if p["id"] in wanted]
    prompts = [p for p in prompts if p.get("prompt_text")]

    lines = [
        "<!-- legaleval-manual-sheet",
        f"model: {args.model}",
        f"rubric_version: {suite['rubric_version']}",
        f"exported: {dt.datetime.now().isoformat()}",
        "-->",
        "",
        f"LegalEval v6 manual run sheet — model under test: {args.model}",
        "",
        CHECKLIST,
    ]
    for p in prompts:
        lines += [
            "",
            PROMPT_MARK.format(pid=p["id"]),
            "",
            p["prompt_text"],
            "",
            RESPONSE_MARK.format(pid=p["id"]),
            "",
            "",
        ]

    SHEETS.mkdir(exist_ok=True)
    out = SHEETS / f"{args.model}_sheet.md"
    if out.exists() and not args.force:
        raise SystemExit(f"{out} already exists (it may hold pasted work) — use --force to overwrite")
    out.write_text("\n".join(lines))
    print(f"{len(prompts)} prompts -> {out}")
    print("Fill in the RESPONSE sections, then:")
    print(f"  python tools/manual_run.py ingest {out.relative_to(ROOT)}")


def parse_sheet(text: str) -> tuple[dict, dict]:
    """Return (header_meta, {prompt_id: response_text})."""
    meta = {}
    if m := re.match(r"<!-- legaleval-manual-sheet\n(.*?)\n-->", text, re.S):
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()

    lines = text.split("\n")
    marks = [(i, m.group(1), m.group(2)) for i, line in enumerate(lines)
             if (m := MARK_RE.match(line.strip()))]

    responses = {}
    for idx, (start, kind, pid) in enumerate(marks):
        if kind != "RESPONSE":
            continue
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        body = "\n".join(lines[start + 1:end]).strip()
        if body:
            responses[pid] = body
    return meta, responses


def cmd_ingest(args: argparse.Namespace) -> None:
    sheet_path = Path(args.sheet)
    meta, responses = parse_sheet(sheet_path.read_text())

    model = meta.get("model")
    if not model:
        raise SystemExit(f"{sheet_path}: missing 'model:' in sheet header — was this exported by this tool?")

    suite = load_suite()
    if meta.get("rubric_version") != suite["rubric_version"]:
        print(f"WARNING: sheet was exported under rubric_version {meta.get('rubric_version')!r}, "
              f"suite is now {suite['rubric_version']!r} — prompts may have changed since export.")

    if not responses:
        raise SystemExit("no filled-in RESPONSE sections found — paste replies below the RESPONSE markers")

    run_id = args.run_id or dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + "_manual"
    out_dir = RUNS / run_id / "responses"
    out_dir.mkdir(parents=True, exist_ok=True)

    for pid in sorted(responses):
        record = {
            "run_id": run_id,
            "prompt_id": pid,
            "provider": model,
            "model_id": f"{model} (web UI, manual capture)",
            "isolation": ISOLATION,
            "rubric_version": suite["rubric_version"],
            "timestamp": dt.datetime.now().isoformat(),
            "source": str(sheet_path),
            "usage": {"input": None, "output": None},
            "response_text": responses[pid],
        }
        path = out_dir / f"{pid}_{model}.json"
        status = "OVERWROTE" if path.exists() else "wrote"
        path.write_text(json.dumps(record, indent=2))
        print(f"  {status} {pid} x {model}: {len(responses[pid])} chars")

    all_ids = {p["id"] for p in suite["prompts"] if p.get("prompt_text")}
    if skipped := sorted(all_ids - set(responses)):
        print(f"blank (skipped): {', '.join(skipped)}")
    print(f"\nrun {run_id}: {len(responses)} responses -> {out_dir}")
    print(f"Next: python -m harness.grade runs/{run_id}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    ex = sub.add_parser("export", help="write a paste worksheet for one model")
    ex.add_argument("--model", required=True,
                    help=f"provider name for runs/results, e.g. {', '.join(KNOWN_MODELS)}")
    ex.add_argument("--prompts", default=None, help="comma-separated prompt ids, e.g. A1,B2")
    ex.add_argument("--force", action="store_true", help="overwrite an existing sheet")
    ex.set_defaults(func=cmd_export)

    ing = sub.add_parser("ingest", help="parse a filled-in worksheet into runs/<id>/responses/")
    ing.add_argument("sheet", help="path to the filled-in sheet")
    ing.add_argument("--run-id", default=None,
                     help="ingest into an existing run dir (to combine with API-run models)")
    ing.set_defaults(func=cmd_ingest)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
