#!/usr/bin/env python3
"""
Sampling-only calibration run (NO training). For each problem: generate
N_ROLLOUTS rollouts on the LOCAL model, grade with the canonical reward_func,
classify the goldilocks zone, and SAVE INCREMENTALLY (atomic + resumable).
Output matches the calib_* schema so build_goldilocks_set.py consumes it directly.

Launch (fresh studio, after git clone/pull):   bash tools/sample.sh
Or directly:                                    python3 tools/sample.py

Config via env (defaults are tonight's plan):
  DATASET=data/skeleton_dataset_v11_clean.json   N_PROBLEMS=500   N_ROLLOUTS=8
  MAX_NEW_TOKENS=2048   TEMP=1.0   SEED=42   GEN_BATCH=8   SAVE_EVERY=25
  OUT=data/calib_v11_2048_7B.json   MODEL=Qwen/Qwen2.5-7B-Instruct
"""
import os, sys, json, random, time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from reward_func import extract_predicted_answer, extract_gold_answer, _numbers_match

def _env(k, d): return os.environ.get(k, d)
MODEL          = _env("MODEL", "Qwen/Qwen2.5-7B-Instruct")
DATASET        = os.path.join(REPO, _env("DATASET", "data/skeleton_dataset_v11_clean.json"))
OUT            = os.path.join(REPO, _env("OUT", "data/calib_v11_2048_7B.json"))
N_PROBLEMS     = int(_env("N_PROBLEMS", "500"))
N_ROLLOUTS     = int(_env("N_ROLLOUTS", "8"))
MAX_NEW_TOKENS = int(_env("MAX_NEW_TOKENS", "2048"))
TEMP           = float(_env("TEMP", "1.0"))
SEED           = int(_env("SEED", "42"))
GEN_BATCH      = int(_env("GEN_BATCH", "8"))
SAVE_EVERY     = int(_env("SAVE_EVERY", "25"))
SYSTEM_PROMPT  = ("You are a math problem solver. Think step by step and put your "
                  "final answer in \\boxed{}.")

print(f"model={MODEL}\ndataset={DATASET}\nN={N_PROBLEMS} rollouts={N_ROLLOUTS} "
      f"max_new_tokens={MAX_NEW_TOKENS} temp={TEMP} bf16\nout={OUT} save_every={SAVE_EVERY}",
      flush=True)

with open(DATASET) as f:
    data = json.load(f)
random.seed(SEED)
random.shuffle(data)
data = data[:N_PROBLEMS]

# resume: keep any work already on disk, skip those problems
results, done = [], set()
if os.path.exists(OUT):
    try:
        results = json.load(open(OUT))
        done = {r["problem"] for r in results}
        print(f"resuming — {len(done)} problems already done", flush=True)
    except Exception:
        results, done = [], set()

def save():                                   # atomic: tmp -> rename
    tmp = OUT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(results, f)
    os.replace(tmp, OUT)

tok = AutoTokenizer.from_pretrained(MODEL)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
_t_load = time.time()
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.bfloat16,
                                             device_map="cuda")
model.eval()
print(f"model loaded in {time.time()-_t_load:.0f}s — sampling now", flush=True)

todo = [it for it in data if it["problem"] not in done]
print(f"{len(todo)} to sample ({len(done)} skipped)", flush=True)

_t_run = time.time()
for idx, item in enumerate(todo):
    _t0 = time.time()
    problem = item["problem"]
    gold = str(item.get("answer", item.get("gold"))).strip()
    skeleton_type = item.get("skeleton_type", "unknown")
    prompt = tok.apply_chat_template(
        [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": problem}],
        tokenize=False, add_generation_prompt=True)
    inputs = tok(prompt, return_tensors="pt").to("cuda")

    rewards, texts, remaining = [], [], N_ROLLOUTS
    with torch.no_grad():
        while remaining > 0:
            kk = min(GEN_BATCH, remaining)
            out = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=True,
                                 temperature=TEMP, num_return_sequences=kk,
                                 pad_token_id=tok.eos_token_id)
            for seq in out:
                resp = tok.decode(seq[inputs["input_ids"].shape[1]:], skip_special_tokens=True)
                pred, _ = extract_predicted_answer(resp)
                g = extract_gold_answer(gold)
                correct = g is not None and pred is not None and _numbers_match(pred, g)
                rewards.append(1.0 if correct else 0.0)
                texts.append(resp)
            remaining -= kk

    mean = float(np.mean(rewards))
    adv = [r - mean for r in rewards]
    nc = int(sum(rewards))
    zone = ("too_hard" if mean == 0 else "too_easy" if mean == 1
            else "goldilocks" if 0.25 <= mean <= 0.75 else "borderline")
    results.append({
        "problem": problem, "skeleton_type": skeleton_type, "gold": gold,
        "pass_rate": mean, "correct": nc, "total_rollouts": N_ROLLOUTS,
        "mean_reward": mean, "advantages": adv,
        "mean_abs_advantage": float(np.mean(np.abs(adv))),
        "max_advantage": float(max(rewards) - mean), "advantage_std": float(np.std(rewards)),
        "zone": zone, "rollout_rewards": rewards, "rollout_texts": texts,
    })
    dt = time.time() - _t0
    avg = (time.time() - _t_run) / (idx + 1)
    eta_h = (len(todo) - idx - 1) * avg / 3600
    print(f"[{len(done)+idx+1}/{N_PROBLEMS}] {nc}/{N_ROLLOUTS} {zone:10} | {skeleton_type:22} | "
          f"{dt:4.0f}s avg {avg:4.0f}s ETA {eta_h:4.1f}h | {problem[:40]}", flush=True)
    if (idx + 1) % SAVE_EVERY == 0:
        save()
        print(f"  ...saved {len(results)} to {OUT}", flush=True)

save()
print("DONE. zones:", dict(Counter(r["zone"] for r in results)), flush=True)
print(f"saved {len(results)} -> {OUT}", flush=True)
