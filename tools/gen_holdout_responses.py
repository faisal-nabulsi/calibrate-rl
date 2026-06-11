#!/usr/bin/env python3
"""
Generate held-out responses for a base model OR a trained LoRA checkpoint, so we
can read base-vs-trained side by side (did the reasoning actually get smarter?).

Run once per model state (base, then each checkpoint), same machine/serving:
    # base:
    HELDOUT=data/goldilocks_holdout_v10.json OUT=results/holdout_resp_base.json \
        python3 tools/gen_holdout_responses.py
    # trained (LoRA adapter dir from the run, e.g. checkpoint-81 / checkpoint-120 / abl3 ckpt-162):
    HELDOUT=data/goldilocks_holdout_v10.json CHECKPOINT=./checkpoint/run_.../checkpoint-81 \
        OUT=results/holdout_resp_ckpt81.json python3 tools/gen_holdout_responses.py

Each output row: {problem, skeleton_type, gold, correct, pass_rate, responses[], rewards[]}.
gen_holdout_compare.py then reads two of these and builds the side-by-side viewer.
NOTE: needs the SAME base model + temp + max_new_tokens as calibration/training.
"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
import numpy as np, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from core.reward_func import extract_predicted_answer, extract_gold_answer, _numbers_match

def env(k, d): return os.environ.get(k, d)
BASE = env("MODEL", "Qwen/Qwen2.5-7B-Instruct")
CHECKPOINT = env("CHECKPOINT", "")              # LoRA adapter dir; empty = base model
HELDOUT = os.path.join(REPO, env("HELDOUT", "data/goldilocks_holdout_v10.json"))
OUT = os.path.join(REPO, env("OUT", "results/holdout_resp.json"))
N_ROLLOUTS = int(env("N_ROLLOUTS", "8"))
MAX_NEW_TOKENS = int(env("MAX_NEW_TOKENS", "1024"))   # match the run (v10=1024, v12=2048)
TEMP = float(env("TEMP", "1.0"))
SYSTEM = "You are a math problem solver. Think step by step and put your final answer in \\boxed{}."

data = json.load(open(HELDOUT))
print(f"base={BASE} checkpoint={CHECKPOINT or '(none/base)'}\nheld-out={HELDOUT} ({len(data)} Q) "
      f"rollouts={N_ROLLOUTS} max_new={MAX_NEW_TOKENS} temp={TEMP}\nout={OUT}", flush=True)

tok = AutoTokenizer.from_pretrained(BASE)
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="cuda")
if CHECKPOINT:
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, CHECKPOINT)
    model = model.merge_and_unload()   # merge LoRA so generation uses the trained weights
model.eval()

results = []
t0 = time.time()
for i, item in enumerate(data):
    problem = item["problem"]; gold = str(item.get("answer", item.get("gold"))).strip()
    concept = item.get("skeleton_type", "unknown")
    prompt = tok.apply_chat_template(
        [{"role": "system", "content": SYSTEM}, {"role": "user", "content": problem}],
        tokenize=False, add_generation_prompt=True)
    inputs = tok(prompt, return_tensors="pt").to("cuda")
    rewards, texts = [], []
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=True,
                             temperature=TEMP, num_return_sequences=N_ROLLOUTS,
                             pad_token_id=tok.eos_token_id)
    for seq in out:
        resp = tok.decode(seq[inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        pred, _ = extract_predicted_answer(resp); g = extract_gold_answer(gold)
        ok = g is not None and pred is not None and _numbers_match(pred, g)
        rewards.append(1.0 if ok else 0.0); texts.append(resp)
    nc = int(sum(rewards))
    results.append({"problem": problem, "skeleton_type": concept, "gold": gold,
                    "correct": nc, "pass_rate": nc / N_ROLLOUTS,
                    "responses": texts, "rewards": rewards})
    done = i + 1; el = time.time() - t0
    print(f"[{done}/{len(data)}] {nc}/{N_ROLLOUTS} | {el/60:.1f}m elapsed, ~{el/done*(len(data)-done)/60:.0f}m left "
          f"| {concept} | {problem[:42]}", flush=True)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(results, open(OUT, "w"))
print(f"\nmean pass-rate {np.mean([r['pass_rate'] for r in results]):.3f}  -> {OUT}")
