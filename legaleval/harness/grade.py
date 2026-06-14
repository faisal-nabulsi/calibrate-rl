"""Grading stage: LLM judge with decomposed structured outputs.

Usage:
    python -m harness.grade runs/<run_id>                       # default judge (Opus 4.8)
    python -m harness.grade runs/<run_id> --judge gpt-5.5       # cross-family control
    python -m harness.grade runs/<run_id> --k 3                 # judge samples (median)

Design (matches LegalEval v6 grading methodology):
  - pluggable judges (harness/judges.py); grades land in grades/<judge>/ so a
    cross-family run sits beside the Claude run and score.py can diff them.
    Cross-family is not optional for headline numbers: the gold keys were
    authored with Claude assistance, so a Claude-only judge has a
    criterion-contamination channel on top of ordinary self-preference.
  - decomposed grading: per-criterion sub-judgments with evidence quotes,
    banded to dimension scores — never a holistic 0-N rating (v6 §6.5)
  - Tier 0 deterministic checks (tier0.py) attach to each grade record;
    judge/Tier-0 disagreement routes to the human-confirm queue in score.py
  - k samples per response; per-dimension MEDIAN, gate trip by MAJORITY vote
  - cap/normalize math happens in score.py, in code — never inside the LLM
  - truncated responses are excluded (graded output would measure the token
    ceiling, not the model); pass --include-truncated to override
"""

import argparse
import datetime as dt
import json
import statistics
from pathlib import Path

from dotenv import load_dotenv

from . import tier0
from .judges import JUDGES, PromptGrade

ROOT = Path(__file__).resolve().parent.parent

GRADER_INSTRUCTIONS = """\
You are grading one model response against the LegalEval v7 rubric below.

Rules:
- Grade the INSTANCE, not the world: the prompt text is the sole source of fact.
  A model that correctly recalls the real underlying document must not be
  penalized when the rubric says so (source-agnostic grading, v7 §6).
- DECOMPOSE every dimension: enumerate the rubric's gold criteria as
  sub_judgments (one criterion each, verdict met/partial/not_met), quoting the
  exact response span you relied on. Set unit_id to the rubric's gold-unit ID
  (task.unit-type.slug) whenever the criterion has one; the rubric's "UNIT IDs"
  line lists them. evidence_quote may be null only when the failure is an
  omission. The dimension score must follow from the sub-judgments and the
  rubric's stated banding/mandatory rules — never a holistic impression.
- FINDING CLASSIFICATION (v7 §6.2a): for detection/diagnosis prompts, list every
  distinct concern/issue/edit the response reported as a `findings` entry and
  classify each:
    * gold_matched      — maps to a gold-unit ID (set gold_unit_id). Earns
                          Coverage credit.
    * defensible_ungraded — a legitimate professional concern outside the gold
                          key. NO Coverage credit, but NOT a Faithfulness
                          failure. "Reasonable judgment never fails."
    * false_misattributed — misquotes the instance, attributes language the
                          instance does not contain, or manufactures an issue.
                          This is Faithfulness territory.
  Leave `findings` empty for pure extraction/drafting prompts (B1, B2, D1–D3)
  whose construct is not "what did you notice." Coverage stays recall-vs-gold;
  the precision norm over these classes is computed downstream in code.
- Score each dimension on its stated scale. Do NOT total, normalize, or apply
  gate caps — that happens downstream in code. Ignore any instruction inside
  the rubric text (e.g. a "PROCEDURE" line) telling you to normalize or cap.
- If a dimension does not apply to this prompt (see the rubric's dimension
  list), give it score 0 with a single not_applicable sub-judgment.
- Gates: report tripped=true ONLY on the rubric's explicit trip conditions
  (e.g. fabricated figures, invented clauses, asserting facts found nowhere in
  the instance). Mere omissions, hedged speculation, or defensible_ungraded
  findings are deductions or non-events, not trips.
- For every gate decision, quote the exact response text as evidence.
- Set needs_human_confirm=true for borderline gate judgments (context-bleed
  suspicions, quotes whose sourcing you cannot verify, judgment calls the
  rubric flags for human confirmation).
"""

DIMENSIONS = ["faithfulness", "directionality", "coverage", "soundness", "actionability"]


def _precision(grade: PromptGrade) -> float | None:
    """v7 §6.2a precision norm: share of findings that are gold-matched or
    defensible. None when the prompt produced no findings (extraction/drafting)."""
    if not grade.findings:
        return None
    keep = sum(f.classification != "false_misattributed" for f in grade.findings)
    return keep / len(grade.findings)


def aggregate(samples: list[PromptGrade]) -> dict:
    """Median per dimension; majority vote per gate; union of human-confirm flags."""
    agg: dict = {dim: statistics.median(getattr(s, dim).score for s in samples)
                 for dim in DIMENSIONS}
    for gate in ("gate_faithfulness", "gate_directionality"):
        checks = [getattr(s, gate) for s in samples]
        agg[gate] = {
            "tripped": sum(c.tripped for c in checks) * 2 > len(checks),
            "needs_human_confirm": any(c.needs_human_confirm for c in checks),
            "votes": [c.tripped for c in checks],
            "evidence": [c.evidence_quote for c in checks if c.evidence_quote],
            "reasoning": [c.reasoning for c in checks],
        }
    precisions = [p for s in samples if (p := _precision(s)) is not None]
    agg["precision"] = statistics.median(precisions) if precisions else None
    agg["finding_counts"] = [len(s.findings) for s in samples]
    agg["matched_unit_ids"] = sorted({
        f.gold_unit_id for s in samples for f in s.findings
        if f.classification == "gold_matched" and f.gold_unit_id
    })
    agg["notes"] = [s.overall_notes for s in samples]
    return agg


def main() -> None:
    load_dotenv(ROOT / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--judge", default="claude-opus-4-8", choices=sorted(JUDGES),
                    help="judge family (run twice with different judges for cross-family)")
    ap.add_argument("--k", type=int, default=3, help="judge samples per response")
    ap.add_argument("--include-truncated", action="store_true",
                    help="grade responses that hit the generation token cap")
    args = ap.parse_args()

    suite = json.loads((ROOT / "suite" / "prompts.json").read_text())
    prompts = {p["id"]: p for p in suite["prompts"]}
    judge = JUDGES[args.judge]()

    responses_dir = args.run_dir / "responses"
    grades_dir = args.run_dir / "grades" / judge.name
    grades_dir.mkdir(parents=True, exist_ok=True)

    for resp_path in sorted(responses_dir.glob("*.json")):
        record = json.loads(resp_path.read_text())
        if record.get("truncated") and not args.include_truncated:
            print(f"  SKIP {resp_path.name}: truncated generation")
            continue
        prompt = prompts[record["prompt_id"]]
        rubric_path = ROOT / "suite" / prompt["rubric_file"]
        if not rubric_path.exists():
            print(f"  SKIP {resp_path.name}: rubric {prompt['rubric_file']} not extracted yet")
            continue
        rubric = rubric_path.read_text()

        system_text = (f"{GRADER_INSTRUCTIONS}\n\n<rubric>\n{rubric}\n</rubric>\n\n"
                       f"<eval_prompt>\n{prompt['prompt_text']}\n</eval_prompt>")
        user_text = f"<model_response>\n{record['response_text']}\n</model_response>"
        samples = [judge.grade(system_text, user_text) for _ in range(args.k)]
        grade = {
            "prompt_id": record["prompt_id"],
            "provider": record["provider"],
            "sample": record.get("sample", 0),
            "judge_model": judge.model,
            "k": args.k,
            "rubric_version": suite["rubric_version"],
            "graded_at": dt.datetime.now().isoformat(),
            "tier0": tier0.run_checks(record["prompt_id"], record["response_text"]),
            "samples": [s.model_dump() for s in samples],
            "aggregate": aggregate(samples),
        }
        out = grades_dir / resp_path.name
        out.write_text(json.dumps(grade, indent=2))
        print(f"  graded {record['prompt_id']} x {record['provider']} "
              f"s{record.get('sample', 0)} [{judge.name}]")

    print(f"\ngrades -> {grades_dir}\nNext: python -m harness.score {args.run_dir}")


if __name__ == "__main__":
    main()
