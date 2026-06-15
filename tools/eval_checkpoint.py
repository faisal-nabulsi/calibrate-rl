"""Post-hoc held-out eval of a LoRA checkpoint on the EXACT v12 held-out set, at K=8.

The in-run monitor logs K=4 (cheap). This is the accurate K=8 "headline" re-eval used to
pick the held-out-best checkpoint after a run. It evaluates on the same fixed
data/v12_holdout.json (NOT a re-split, unlike holdout_eval.py's __main__).

Usage:
  python tools/eval_checkpoint.py                                   # BASE
  python tools/eval_checkpoint.py --checkpoint checkpoint-20        # a LoRA adapter dir
Compare BASE vs each top checkpoint; the headline is mean_pass_rate.
"""
import os, sys, json, argparse

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "eval")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from holdout_eval import evaluate

ap = argparse.ArgumentParser()
ap.add_argument("--base", default="Qwen/Qwen2.5-7B-Instruct")
ap.add_argument("--checkpoint", default=None, help="LoRA adapter dir (omit -> base model)")
ap.add_argument("--holdout", default="data/v12_holdout.json")
ap.add_argument("--k", type=int, default=8)
ap.add_argument("--temperature", type=float, default=1.0)
ap.add_argument("--max-new-tokens", type=int, default=2048)
a = ap.parse_args()

probs = json.load(open(a.holdout))
tok = AutoTokenizer.from_pretrained(a.base)
model = AutoModelForCausalLM.from_pretrained(a.base, torch_dtype=torch.bfloat16, device_map="cuda")
if a.checkpoint:
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, a.checkpoint).merge_and_unload()

m = evaluate(model, tok, probs, k=a.k, temperature=a.temperature, max_new_tokens=a.max_new_tokens)
print(json.dumps({"checkpoint": a.checkpoint or "BASE", "holdout_n": len(probs), "k": a.k, **m}))
