"""
prep_calibration.py — one-time prep of measure_environment.py for a protocol-compliant
sampling run. Idempotent: safe to run more than once; only applies what's missing.
Run it from ~/src:  python3 prep_calibration.py
"""
f = "measure_environment.py"
s = open(f).read()
changes = []

if "import os" not in s:
    s = s.replace("import json", "import os, json", 1); changes.append("os import")

# deterministic problem subset so every model/run sees the SAME problems (fair comparison)
if "random.seed" not in s:
    s = s.replace("random.shuffle(data)", "random.seed(42)\nrandom.shuffle(data)"); changes.append("seed")

# model selectable via env var MODEL (no editing the file between runs)
if 'os.environ.get("MODEL"' not in s and 'BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"' in s:
    s = s.replace('BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"',
                  'BASE_MODEL = os.environ.get("MODEL", "Qwen/Qwen2.5-7B-Instruct")'); changes.append("env model")

# 100 problems for the quick capability check (no-op if already 100; raise to 300 for the full run)
if "N_PROBLEMS = 300" in s:
    s = s.replace("N_PROBLEMS = 300", "N_PROBLEMS = 100"); changes.append("N_PROBLEMS=100")

# capture the concept label -> enables per-concept goldilocks rate (Step 7 / your eval philosophy)
if "skeleton_type =" not in s:
    s = s.replace("problem = item['problem']",
                  "problem = item['problem']\n    skeleton_type = item.get('skeleton_type', 'unknown')"); changes.append("skeleton_type")

# the two advantage metrics the protocol Step 7 names by hand
if "mean_abs_advantage" not in s:
    s = s.replace("pass_rate = mean_reward",
                  "pass_rate = mean_reward\n"
                  "    mean_abs_advantage = float(np.mean(np.abs(advantages)))\n"
                  "    max_advantage = float(max(rollout_rewards) - mean_reward)"); changes.append("advantage metrics")

# SAVE the transcripts (Step 8 must read them) + the concept + the new metrics
if '"rollout_texts": rollout_texts' not in s:
    old = (
'    results.append({\n'
'        "problem": problem,\n'
'        "gold": gold,\n'
'        "pass_rate": pass_rate,\n'
'        "correct": int(sum(rollout_rewards)),\n'
'        "total_rollouts": N_ROLLOUTS,\n'
'        "mean_reward": mean_reward,\n'
'        "advantages": advantages,\n'
'        "advantage_std": advantage_std,\n'
'        "zone": zone,\n'
'        "rollout_rewards": rollout_rewards,\n'
'    })')
    new = (
'    results.append({\n'
'        "problem": problem,\n'
'        "skeleton_type": skeleton_type,\n'
'        "gold": gold,\n'
'        "pass_rate": pass_rate,\n'
'        "correct": int(sum(rollout_rewards)),\n'
'        "total_rollouts": N_ROLLOUTS,\n'
'        "mean_reward": mean_reward,\n'
'        "mean_abs_advantage": mean_abs_advantage,\n'
'        "max_advantage": max_advantage,\n'
'        "advantage_std": advantage_std,\n'
'        "zone": zone,\n'
'        "rollout_rewards": rollout_rewards,\n'
'        "rollout_texts": rollout_texts,\n'
'    })')
    assert old in s, "results.append block not found verbatim - check the file"
    s = s.replace(old, new); changes.append("save transcripts + fields")

open(f, "w").write(s)
print("applied:", ", ".join(changes) if changes else "nothing (already prepped)")
