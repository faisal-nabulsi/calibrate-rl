"""Build runs/2026-06-09_baseline/ from the June 9 initial-tests doc.

The doc (suite/source/2026-06-09_initial_tests_raw.md) contains the five
models' raw responses for A1, A2, A3, B1, B2 — captured manually on June 9
(pre-harness). This script converts them into harness response records so
grade.py can re-grade them and we can diff against the June 9 hand grades.

    python tools/build_baseline_run.py
"""

import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "suite" / "source" / "2026-06-09_initial_tests_raw.md"
RUN_ID = "2026-06-09_baseline"

MODEL_MAP = {
    "Claude Sonnet 4.6": "claude-sonnet-4-6",
    "Gemini 3.1 Flash": "gemini-3.1-flash",
    "GPT 5.5": "gpt-5.5",
    "Muse Spark": "muse-spark",
    "Qwen 3.7 Plus": "qwen-3.7-plus",
}


def unescape(t: str) -> str:
    return re.sub(r"\\([.\-()\[\]*_#&$>|{}+])", r"\1", t)


def main() -> None:
    lines = SRC.read_text().split("\n")
    prompt_hdr = re.compile(r"^#+ +([AB][123])( grading)?\s*$", re.I)
    model_hdr = re.compile(r"^#+ +(" + "|".join(re.escape(m) for m in MODEL_MAP) + r")\s*$")

    # mark every boundary: prompt header / grading header / model header
    marks = []
    for i, line in enumerate(lines):
        s = line.strip()
        if m := prompt_hdr.match(s):
            marks.append((i, "grading" if m.group(2) else "prompt", m.group(1).upper()))
        elif m := model_hdr.match(s):
            marks.append((i, "model", m.group(1)))

    out_dir = ROOT / "runs" / RUN_ID / "responses"
    out_dir.mkdir(parents=True, exist_ok=True)

    current_prompt, n = None, 0
    for idx, (start, kind, name) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        if kind == "prompt":
            current_prompt = name
        elif kind == "grading":
            current_prompt = None  # don't scoop model names inside grading tables
        elif kind == "model" and current_prompt:
            provider = MODEL_MAP[name]
            text = unescape("\n".join(lines[start + 1:end]).strip())
            record = {
                "run_id": RUN_ID,
                "prompt_id": current_prompt,
                "provider": provider,
                "model_id": provider,
                "isolation": "unknown (June 9 manual run, pre-harness)",
                "rubric_version": "v6.0",
                "timestamp": dt.datetime.now().isoformat(),
                "source": "suite/source/2026-06-09_initial_tests_raw.md",
                "usage": {"input": None, "output": None},
                "response_text": text,
            }
            (out_dir / f"{current_prompt}_{provider}.json").write_text(
                json.dumps(record, indent=2))
            n += 1
            print(f"  {current_prompt} x {provider}: {len(text)} chars")

    print(f"\n{n} baseline responses -> {out_dir}")


if __name__ == "__main__":
    main()
