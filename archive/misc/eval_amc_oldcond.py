# eval_amc_oldcond.py — base model under OLD conditions to confirm the 16-18 was a harness artifact.
# Toggle each factor via env vars to isolate which one caused the gap.
#   SYS=0/1      include system prompt (old=0, new=1)
#   MAXTOK=512   max_new_tokens (old=512, new=1024)
#   GRADER=str/num   string-equality (old) vs numeric (new)
# Default = OLD harness reproduction (SYS=0, MAXTOK=512, GRADER=str).

import os, json, re, sys, torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from reward_func import extract_predicted_answer, extract_gold_answer, _numbers_match

SYS    = os.environ.get("SYS", "0") == "1"
MAXTOK = int(os.environ.get("MAXTOK", "512"))
GRADER = os.environ.get("GRADER", "str")
BASE   = "Qwen/Qwen2.5-7B-Instruct"
print(f"COND: sys_prompt={SYS} max_new_tokens={MAXTOK} grader={GRADER}", flush=True)

tok = AutoTokenizer.from_pretrained(BASE)
model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16, device_map="auto")
model.eval()

# OLD extractor (string-equality path): boxed -> int-normalize; else 'answer is'; else last number
def old_extract(text):
    m = re.search(r"\\boxed\{(-?[\d,\.]+)\}", text)
    if m:
        val = m.group(1).replace(",", "")
        try: return str(int(float(val)))
        except: return val
    m = re.search(r"[Tt]he\s+(?:final\s+)?answer\s+is\s*:?\s*(-?[\d,\.]+)", text)
    if m: return m.group(1).replace(",", "")
    nums = re.findall(r"-?\d+\.?\d*", text)
    return nums[-1] if nums else None

ds = list(load_dataset("AI-MO/aimo-validation-amc", split="train"))
correct = 0
for i, p in enumerate(ds):
    q = p["problem"]; gold_raw = str(p["answer"]).strip()
    msgs = ([{"role":"system","content":"You are a math problem solver. Think step by step and put your final answer in \\boxed{}."}] if SYS else []) + [{"role":"user","content":q}]
    ids = tok(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True), return_tensors="pt").input_ids.to(model.device)
    with torch.no_grad():
        out = model.generate(ids, max_new_tokens=MAXTOK, do_sample=False, pad_token_id=tok.eos_token_id)
    resp = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
    if GRADER == "num":
        pred,_ = extract_predicted_answer(resp); g = extract_gold_answer(gold_raw)
        ok = g is not None and pred is not None and _numbers_match(pred, g)
    else:
        pred = old_extract(resp); gold = str(int(float(gold_raw)))
        ok = pred is not None and pred.strip() == gold.strip()
    correct += ok
    print(f"[{i+1}/{len(ds)}] {'V' if ok else 'X'} gold={gold_raw} pred={pred}", flush=True)
print(f"\nACCURACY ({'sys' if SYS else 'nosys'}/{MAXTOK}tok/{GRADER}): {correct}/{len(ds)}")
