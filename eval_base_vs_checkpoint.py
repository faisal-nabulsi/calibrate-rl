"""
Base vs. trained checkpoint on the held-out goldilocks set.
Reports mean_pass_rate (the metric that can move) + pass@k + tripwires.
Same grader, same system prompt, same temp/k as the training callback.
"""
import json, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from holdout_eval import evaluate

BASE = "Qwen/Qwen2.5-7B-Instruct"
ADAPTER = "checkpoint/run_20260606_225007/checkpoint-27"
HOLDOUT = "data/goldilocks_holdout_v10.json"
K = 16
TEMP = 1.0
MAX_NEW = 1024

problems = json.load(open(HOLDOUT))
print(f"Held-out problems: {len(problems)}")

tok = AutoTokenizer.from_pretrained(BASE)

def run(model, label):
    m = evaluate(model, tok, problems, k=K, temperature=TEMP, max_new_tokens=MAX_NEW)
    print(f"\n=== {label} ===")
    for key, val in m.items():
        print(f"  {key}: {val}")
    return m

# 1) BASE
print("\nLoading base model ...")
base = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="cuda")
base_m = run(base, "BASE (untrained)")
del base
torch.cuda.empty_cache()

# 2) BASE + LoRA adapter
print("\nLoading base + LoRA adapter ...")
m2 = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="cuda")
m2 = PeftModel.from_pretrained(m2, ADAPTER)
m2 = m2.merge_and_unload()
trained_m = run(m2, "TRAINED (checkpoint-27)")

# 3) DELTA
print("\n" + "="*50)
print("RESULT — mean_pass_rate (the movable metric):")
b = base_m.get("mean_pass_rate", 0.0)
t = trained_m.get("mean_pass_rate", 0.0)
print(f"  base    : {b}")
print(f"  trained : {t}")
print(f"  delta   : {t - b:+.4f}")
print("="*50)
