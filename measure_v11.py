import os, json
import torch
import random
import numpy as np
import re
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from reward_func import extract_predicted_answer, extract_gold_answer, _numbers_match

BASE_MODEL = os.environ.get("MODEL", "Qwen/Qwen2.5-7B-Instruct")
_model_tag = BASE_MODEL.split("/")[-1].replace("Qwen2.5-","").replace("-Instruct","")
_OUT_PATH = f"/home/faisalnab25/data/calib_v11_{_model_tag}.json"
CHECKPOINT = "/teamspace/studios/this_studio/rl-intro/checkpoint/run_20260519_010402/checkpoint-300"
N_ROLLOUTS = 8
GEN_BATCH = 8  # L4 has 24GB; 8 per call fits with headroom
N_PROBLEMS = 300

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.float16, device_map="cuda")


model.eval()

with open('/home/faisalnab25/data/skeleton_dataset_v11.json') as f:
    data = json.load(f)

random.seed(42)
random.shuffle(data)
data = data[:N_PROBLEMS]
print(f"Sampling {N_PROBLEMS} problems, {N_ROLLOUTS} rollouts each = {N_PROBLEMS * N_ROLLOUTS} total transcripts")

def extract_answer(text):
    match = re.search(r'\\boxed\{([^}]+)\}', text)
    if match:
        val = match.group(1).strip()
        num = re.search(r'-?\d+\.?\d*', val)
        if num:
            return num.group(0)
        return val
    fractions = re.findall(r'\d+/\d+', text)
    if fractions:
        return fractions[-1]
    numbers = re.findall(r'-?\d+\.?\d*', text)
    return numbers[-1] if numbers else None

results = []

for i, item in enumerate(data):
    problem = item['problem']
    skeleton_type = item.get('skeleton_type', 'unknown')
    gold = str(item['answer']).strip()

    messages = [
        {"role": "system", "content": "You are a math problem solver. Think step by step and put your final answer in \\boxed{}."},
        {"role": "user", "content": problem},
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

    rollout_rewards = []
    rollout_texts = []

    remaining = N_ROLLOUTS
    while remaining > 0:
        k = min(GEN_BATCH, remaining)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=1.0,
                do_sample=True,
                num_return_sequences=k,
                pad_token_id=tokenizer.eos_token_id,
            )
        for seq in outputs:
            response = tokenizer.decode(seq[inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            predicted, _ = extract_predicted_answer(response)
            _gold = extract_gold_answer(gold)
            correct = _gold is not None and predicted is not None and _numbers_match(predicted, _gold)
            rollout_rewards.append(1.0 if correct else 0.0)
            rollout_texts.append(response)
        remaining -= k

    # GRPO metrics
    mean_reward = np.mean(rollout_rewards)
    advantages = [r - mean_reward for r in rollout_rewards]
    advantage_std = np.std(rollout_rewards)
    pass_rate = mean_reward
    mean_abs_advantage = float(np.mean(np.abs(advantages)))
    max_advantage = float(max(rollout_rewards) - mean_reward)

    # Goldilocks classification
    if pass_rate == 0.0:
        zone = "too_hard"
    elif pass_rate == 1.0:
        zone = "too_easy"
    elif 0.25 <= pass_rate <= 0.75:
        zone = "goldilocks"
    else:
        zone = "borderline"

    results.append({
        "problem": problem,
        "skeleton_type": skeleton_type,
        "gold": gold,
        "pass_rate": pass_rate,
        "correct": int(sum(rollout_rewards)),
        "total_rollouts": N_ROLLOUTS,
        "mean_reward": mean_reward,
        "advantages": advantages,
        "mean_abs_advantage": mean_abs_advantage,
        "max_advantage": max_advantage,
        "advantage_std": advantage_std,
        "zone": zone,
        "rollout_rewards": rollout_rewards,
        "rollout_texts": rollout_texts,
    })

    print(f"[{i+1}/{N_PROBLEMS}] pass={int(sum(rollout_rewards))}/{N_ROLLOUTS} zone={zone} adv_std={advantage_std:.3f} | {problem[:60]}", flush=True)

# Summary
zones = {}
for r in results:
    zones[r['zone']] = zones.get(r['zone'], 0) + 1

total = len(results)
avg_adv_std = np.mean([r['advantage_std'] for r in results])
goldilocks_adv_std = np.mean([r['advantage_std'] for r in results if r['zone'] == 'goldilocks']) if zones.get('goldilocks') else 0

print("\n" + "="*60)
print("ENVIRONMENT QUALITY REPORT — Simple Skeletons")
print("="*60)
print(f"Total problems analyzed:  {total}")
print(f"Total transcripts:        {total * N_ROLLOUTS}")
print(f"")
print(f"Zone breakdown:")
print(f"  Too easy  (8/8 correct): {zones.get('too_easy', 0):3d} ({zones.get('too_easy', 0)/total*100:.1f}%)")
print(f"  Too hard  (0/8 correct): {zones.get('too_hard', 0):3d} ({zones.get('too_hard', 0)/total*100:.1f}%)")
print(f"  Goldilocks (2-6/8):      {zones.get('goldilocks', 0):3d} ({zones.get('goldilocks', 0)/total*100:.1f}%)")
print(f"  Borderline:              {zones.get('borderline', 0):3d} ({zones.get('borderline', 0)/total*100:.1f}%)")
print(f"")
print(f"Useful signal:            {zones.get('goldilocks', 0) + zones.get('borderline', 0)}/{total} ({(zones.get('goldilocks', 0) + zones.get('borderline', 0))/total*100:.1f}%)")
print(f"Avg advantage std:        {avg_adv_std:.4f}")
print(f"Goldilocks adv std:       {goldilocks_adv_std:.4f}")
print("="*60)

with open(_OUT_PATH, 'w') as f:
    json.dump(results, f, indent=2)
print(f"Saved to {_OUT_PATH}")
