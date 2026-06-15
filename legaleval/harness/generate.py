"""Generation stage: run every model under test against every suite prompt.

Usage:
    python -m harness.generate                      # all registered models, n=3 samples
    python -m harness.generate --models claude-sonnet-4-6
    python -m harness.generate --prompts A1,A2 --n 1

Writes one JSON per (prompt, model, sample) under runs/<timestamp>/responses/.
Responses are the durable artifact — grading replays from these files.

n>1 samples per (prompt, model) cell because generation variance is the
dominant noise source with a 14-prompt suite: a single draw per cell makes
model-level means move run to run. score.py reports per-cell spread.
"""

import argparse
import datetime as dt
import json
from pathlib import Path

from dotenv import load_dotenv

from .providers import REGISTRY

ROOT = Path(__file__).resolve().parent.parent
SUITE = ROOT / "suite" / "prompts.json"
RUNS = ROOT / "runs"


def load_suite() -> dict:
    return json.loads(SUITE.read_text())


def resolve_variant(prompt: dict, variant: str) -> tuple[str | None, str]:
    """Return (prompt_text, variant_label) for the requested instruction variant.

    'headline' is always the paste block (OPEN for A1/A2/C2, instructed for B3).
    'directed'/'uninstructed' pull alt phrasing from the prompt's 'variants';
    a prompt with no such variant falls back to headline so a full-suite run on
    --variant directed still grades every prompt, labelling fallbacks honestly.
    """
    base = prompt.get("prompt_text")
    v = prompt.get("variants") or {}
    if variant == "headline" or not base:
        return base, "headline"
    if variant == "directed" and v.get("directed_text"):
        # swap only the leading instruction sentence(s); contract text is unchanged
        body = base.split("\n", 1)[1] if "\n" in base else ""
        return f"{v['directed_text']}\n{body}", "directed"
    if variant == "uninstructed" and v.get("uninstructed_text"):
        return v["uninstructed_text"], "uninstructed"
    return base, "headline"  # no such variant for this prompt


def main() -> None:
    load_dotenv(ROOT / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=None, help="comma-separated provider names")
    ap.add_argument("--prompts", default=None, help="comma-separated prompt ids, e.g. A1,B2")
    ap.add_argument("--n", type=int, default=3,
                    help="generation samples per (prompt, model) cell")
    ap.add_argument("--variant", default="headline",
                    choices=["headline", "directed", "uninstructed"],
                    help="instruction variant (v7 §6.2a): headline = OPEN/instructed "
                         "paste block; directed/uninstructed pull the alt text from "
                         "each prompt's 'variants' (falls back to headline if none)")
    args = ap.parse_args()

    suite = load_suite()
    prompts = suite["prompts"]
    if args.prompts:
        wanted = set(args.prompts.split(","))
        prompts = [p for p in prompts if p["id"] in wanted]

    model_names = args.models.split(",") if args.models else list(REGISTRY)
    providers = {name: REGISTRY[name]() for name in model_names}

    run_id = dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    out_dir = RUNS / run_id / "responses"
    out_dir.mkdir(parents=True)

    skipped, truncated, failed, done = [], [], [], 0
    for prompt in prompts:
        prompt_text, variant_used = resolve_variant(prompt, args.variant)
        if not prompt_text:
            skipped.append(prompt["id"])
            continue
        for name, provider in providers.items():
            for sample in range(args.n):
                # One model erroring (bad key, wrong endpoint, rate limit) must not
                # abort the whole multi-model run — record it and keep going.
                try:
                    result = provider.generate(prompt_text)
                except Exception as exc:  # noqa: BLE001 — surface any provider failure
                    cell = f"{prompt['id']} x {name} s{sample}"
                    failed.append(f"{cell}: {type(exc).__name__}: {exc}")
                    print(f"  {cell}: FAILED — {type(exc).__name__}: {exc}")
                    continue
                record = {
                    "run_id": run_id,
                    "prompt_id": prompt["id"],
                    "provider": name,
                    "model_id": result.model_id,
                    "sample": sample,
                    "variant": variant_used,
                    "isolation": "incognito",
                    "rubric_version": suite["rubric_version"],
                    "timestamp": dt.datetime.now().isoformat(),
                    "params": result.params,
                    "stop_reason": result.stop_reason,
                    "truncated": result.truncated,
                    "usage": {"input": result.input_tokens, "output": result.output_tokens},
                    "response_text": result.response_text,
                }
                path = out_dir / f"{prompt['id']}_{name}_s{sample}.json"
                path.write_text(json.dumps(record, indent=2))
                done += 1
                flag = "  [TRUNCATED]" if result.truncated else ""
                print(f"  {prompt['id']} x {name} s{sample}: "
                      f"{len(result.response_text)} chars{flag}")
                if result.truncated:
                    truncated.append(path.name)

    print(f"\nrun {run_id}: {done} generations -> {out_dir}")
    if skipped:
        print(f"skipped (no prompt_text yet): {', '.join(skipped)}")
    if truncated:
        print(f"WARNING — {len(truncated)} truncated response(s); grade.py will "
              f"exclude them by default:\n  " + "\n  ".join(truncated))
    if failed:
        print(f"FAILED — {len(failed)} generation(s) errored (run continued):\n  "
              + "\n  ".join(failed))


if __name__ == "__main__":
    main()
