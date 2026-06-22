"""AMC by-coverage eval — mean_pass_rate on the 83 AMC problems, split by
depth-0 @concept coverage (covered / partner-only / uncovered).

Decisive test for "depth-0 capped vs general reasoning" (CLAUDE.md TODO):
gains (vs base) concentrated on the COVERED subset => depth-0 is capped, commit
to depth-1; gains spread to UNCOVERED => general reasoning, depth-0 still has juice.

Reuses holdout_eval.evaluate() so grader + system prompt + gen length are
identical to held-out/calib (CLAUDE.md §9). Sampled mean_pass_rate (k>1,
temp 1.0), NOT greedy binary — §8: use mean_pass_rate on tagged AMC subsets.

Coverage split (validated == §7 counts: 37 / 23 / 23):
  covered      = AMC ids tagged by a depth-0 atomic @concept (not a partner, not a chain)
  partner-only = AMC ids tagged ONLY by a DEPTH1_PARTNERS concept
  uncovered    = the rest

Usage (one model per invocation; run for base, then each checkpoint):
  python eval/eval_amc_coverage.py                                  # BASE
  python eval/eval_amc_coverage.py --checkpoint runs/v12_depth0_run2/checkpoint-20
  python eval/eval_amc_coverage.py --checkpoint runs/v12_depth0_run2/checkpoint-30
"""
import os, sys, json, argparse, importlib.util

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "eval")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from holdout_eval import evaluate, load_amc


def coverage_split(injector="generate/skeleton_injector_v12.py"):
    """Return (covered, partner_only, uncovered) sets of AMC indices (0-82).

    Mirrors the generator's own 'AMC coverage (depth-0)' definition: a depth-0
    atomic concept is a REGISTRY entry that is neither a DEPTH1_PARTNERS member
    nor a chain_* composite.
    """
    spec = importlib.util.spec_from_file_location("inj_cov", os.path.join(_ROOT, injector))
    m = importlib.util.module_from_spec(spec)
    sys.modules["inj_cov"] = m
    spec.loader.exec_module(m)
    REG, PARTNERS = m.REGISTRY, m.DEPTH1_PARTNERS
    covered = set()
    for name, _fn, amc in REG:
        if name in PARTNERS or name.startswith("chain_"):
            continue
        covered.update(amc)
    partner = set()
    for name, _fn, amc in REG:
        if name in PARTNERS:
            partner.update(amc)
    partner_only = partner - covered
    uncovered = set(range(83)) - covered - partner_only
    return covered, partner_only, uncovered


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--checkpoint", default=None, help="LoRA adapter dir (omit -> base model)")
    ap.add_argument("--base-checkpoint", default=None, help="adapter merged into base BEFORE --checkpoint (e.g. ckpt-500 for a depth-1 eval)")
    ap.add_argument("--k", type=int, default=16)              # AMC standard EVAL_K (§0)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--max-new-tokens", type=int, default=2048)  # == calib/AMC gen length
    ap.add_argument("--batch-size", type=int, default=4)     # *k sequences/batch; 4*16=64
    ap.add_argument("--injector", default="generate/skeleton_injector_v12.py")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    covered, partner_only, uncovered = coverage_split(a.injector)
    subsets = {"covered": covered, "partner_only": partner_only, "uncovered": uncovered}
    print(f"Coverage split: covered={len(covered)} partner_only={len(partner_only)} "
          f"uncovered={len(uncovered)} (sum={len(covered)+len(partner_only)+len(uncovered)})",
          flush=True)

    amc = load_amc()                       # 83 problems, dataset (index) order
    assert len(amc) == 83, f"expected 83 AMC problems, got {len(amc)}"

    print(f"Loading base model: {a.base}", flush=True)
    tok = AutoTokenizer.from_pretrained(a.base)
    model = AutoModelForCausalLM.from_pretrained(a.base, dtype=torch.bfloat16, device_map="cuda")
    if a.base_checkpoint:
        from peft import PeftModel
        print(f"Loading BASE adapter: {a.base_checkpoint}", flush=True)
        model = PeftModel.from_pretrained(model, a.base_checkpoint).merge_and_unload()
    if a.checkpoint:
        from peft import PeftModel
        print(f"Loading LoRA adapter: {a.checkpoint}", flush=True)
        model = PeftModel.from_pretrained(model, a.checkpoint).merge_and_unload()
    model.eval()

    kw = dict(k=a.k, temperature=a.temperature, max_new_tokens=a.max_new_tokens,
              batch_size=a.batch_size)
    label = a.checkpoint.replace("/", "_") if a.checkpoint else "BASE"
    results = {"checkpoint": a.checkpoint or "BASE", "k": a.k,
               "temperature": a.temperature, "max_new_tokens": a.max_new_tokens,
               "subsets": {}}

    # whole-set first (so a crash still yields the headline), then per-subset
    for name in ["overall", "covered", "partner_only", "uncovered"]:
        if name == "overall":
            probs = amc
        else:
            idx = sorted(subsets[name])
            probs = [amc[i] for i in idx]
        print(f"\n=== {label} / {name} (n={len(probs)}) ===", flush=True)
        m = evaluate(model, tok, probs, **kw)
        print(json.dumps(m), flush=True)
        results["subsets"][name] = m

    out = a.out or f"results_amc_coverage_{label}.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to: {out}", flush=True)

    # one-line headline per subset
    print(f"\nHEADLINE [{label}]  mean_pass_rate:")
    for name in ["overall", "covered", "partner_only", "uncovered"]:
        s = results["subsets"][name]
        print(f"  {name:13s} n={s['n']:2d}  mpr={s['mean_pass_rate']:.4f}  pass@{a.k}={s.get(f'pass@{a.k}')}")


if __name__ == "__main__":
    main()
