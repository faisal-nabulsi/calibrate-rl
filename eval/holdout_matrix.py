import json, torch, gc
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from holdout_eval import evaluate

BASE = "Qwen/Qwen2.5-7B-Instruct"
RUN  = "checkpoint/run_20260607_033330"
CKPTS = [("base", None),
         ("27",  f"{RUN}/checkpoint-27"),
         ("54",  f"{RUN}/checkpoint-54"),
         ("81",  f"{RUN}/checkpoint-81"),
         ("108", f"{RUN}/checkpoint-108"),
         ("120", f"{RUN}/checkpoint-120")]
K, TEMP = 16, 1.0

problems = json.load(open("data/goldilocks_holdout_v10.json"))
concepts = [p.get("skeleton_type", f"p{i}") for i,p in enumerate(problems)]
print(f"{len(problems)} holdout problems; concepts: {concepts}\n", flush=True)

tok = AutoTokenizer.from_pretrained(BASE)
matrix = {i: {} for i in range(len(problems))}

for label, ckpt in CKPTS:
    print(f"=== loading {label} ===", flush=True)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="auto")
    if ckpt:
        model = PeftModel.from_pretrained(model, ckpt).merge_and_unload()
    model.eval()
    for i, p in enumerate(problems):
        m = evaluate(model, tok, [p], k=K, temperature=TEMP, max_new_tokens=1024, batch_size=2)
        matrix[i][label] = m["mean_pass_rate"]
    agg = evaluate(model, tok, problems, k=K, temperature=TEMP, max_new_tokens=1024, batch_size=2)
    print(f"  {label}: aggregate mean_pass_rate={agg['mean_pass_rate']}  (curve check)", flush=True)
    del model; gc.collect(); torch.cuda.empty_cache()

labels = [l for l,_ in CKPTS]
print("\n" + "="*100)
print(f"{'concept':24s} " + " ".join(f"{l:>6s}" for l in labels) + "   trend")
print("-"*100)
for i in range(len(problems)):
    row = matrix[i]
    cells = " ".join(f"{row[l]:6.3f}" for l in labels)
    trend = row["120"] - row["base"]
    print(f"{concepts[i][:24]:24s} {cells}  {trend:+.3f}")
print("="*100)

json.dump({concepts[i]: matrix[i] for i in range(len(problems))}, open("holdout_matrix.json","w"), indent=2)
print("saved holdout_matrix.json")
