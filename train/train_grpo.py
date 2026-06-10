from datasets import load_dataset
"""
Tiny-Math-Solver — GRPO on GSM8K with TRL.

Trains Qwen2.5-1.5B-Instruct on a curated subset of GSM8K problems
requiring 3+ entity tracking, using <think> tags for structured reasoning.

Reward: binary correctness only (1.0 if final answer matches gold, 0.0
otherwise). No auxiliary rewards -- GRPO learns entirely from the contrast
between correct and incorrect completions within each group.

Run shape (depth-0 goldilocks hillclimb):
  Trains on 106 calibrated goldilocks problems (7B gets 2-6/8); 4 unique prompts
  per optimizer step (2 × 16 / 8 generations); 120 steps ≈ 4.5 epochs; held-out
  goldilocks pass@8 eval + checkpoint every 27 steps. Because the set is all
  goldilocks, ~every prompt produces gradient (no ghost-batching waste).
  KL penalty (beta) anchors the policy; DAPO loss normalizes across active tokens.

Generation: vanilla model.generate() -- no vLLM, no paged attention.
vLLM colocate has PEFT convergence bugs (trl#2856, vllm#14483).
Paged attention runs out of cache blocks at our batch size.
For 1.5B on L40S, vanilla generation is fast enough (~5GB KV cache).

Usage:
    bash setup.sh                        # install deps + build dataset (once)
    python src/train_grpo.py             # train
    accelerate launch src/train_grpo.py  # multi-GPU
"""

import os
import json
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import torch
import logging
from datetime import datetime, timezone

# ── Logging (set up BEFORE importing libraries that configure logging) ─────
RUN_TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
LOG_DIR = "./logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"run_{RUN_TIMESTAMP}.log")

# Explicitly add handlers to root logger (basicConfig is a no-op if
# any library has already configured logging, which transformers/trl do)
_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
_file_handler = logging.FileHandler(LOG_FILE)
_file_handler.setFormatter(_formatter)
_file_handler.setLevel(logging.INFO)

_root_logger = logging.getLogger()
_root_logger.setLevel(logging.INFO)
_root_logger.addHandler(_file_handler)

logger = logging.getLogger("tiny_math_solver")
logger.setLevel(logging.INFO)

from datasets import load_from_disk
from peft import LoraConfig
from trl import GRPOTrainer, GRPOConfig
from core.reward_func import correctness_reward, format_reward

logger.info(f"=== Run started: {RUN_TIMESTAMP} ===")
logger.info(f"Log file: {LOG_FILE}")


# ── Dataset ─────────────────────────────────────────────────────────────────
# Curated dataset (built by src/build_entity_dataset.py).
# Contains GSM8K problems with 3+ named entities (the model's weak spot).
# TRL expects a 'prompt' column.

ENTITY_TRACKING_PROMPT = (
    "Think step by step inside <think> tags before answering. "
    "Show your mathematical reasoning clearly, identify the right formula, "
    "compute each step, and put your final answer in \\boxed{}."
)


def build_prompt(example):
    """Convert math problem to chat format for GRPO training."""
    example["prompt"] = [
        {"role": "system", "content": "You are a math problem solver. Think step by step and put your final answer in \\boxed{}."},
        {"role": "user", "content": example["problem"]},
    ]
    return example


# GOLDILOCKS hillclimb: train ONLY on the calibrated goldilocks-zone problems
# (2-6/8 for the 7B), with a disjoint goldilocks held-out as the per-step monitor.
# Built by build_goldilocks_set.py from calib_v10_7B.json (re-graded with the
# current grader + corrected golds). AMC is intentionally OFF for this small
# hillclimb loop — we're optimizing the loop, not yet claiming transfer.
from datasets import Dataset
from holdout_eval import HeldoutEvalCallback

EVAL_EVERY = 27          # ~1 epoch over 106 train at 4 prompts/step
EVAL_K = 16               # pass@8 ...
EVAL_TEMP = 1.0          # ... temp 1.0 — measures the goldilocks pass-rate training should lift

logger.info("Loading goldilocks train + held-out sets ...")
train_rows = json.load(open(os.environ.get("TRAIN_DATA", "data/goldilocks_train_v10.json")))
holdout_skel = json.load(open(os.environ.get("HOLDOUT_DATA", "data/goldilocks_holdout_v10.json")))
dataset = Dataset.from_list(train_rows).map(build_prompt)
logger.info(f"Train (goldilocks): {len(dataset)} | held-out goldilocks: {len(holdout_skel)} "
            f"| AMC: OFF (small hillclimb loop)")


# ── LoRA config ─────────────────────────────────────────────────────────────
peft_config = LoraConfig(
    r=32,
    lora_alpha=64,
    lora_dropout=0.05,
    target_modules="all-linear",
    task_type="CAUSAL_LM",
)


# ── Training config ─────────────────────────────────────────────────────────
training_args = GRPOConfig(
    output_dir=os.environ.get("RESUME_OUTPUT_DIR", f"./checkpoint/run_{RUN_TIMESTAMP}"),
    run_name=f"grpo_{RUN_TIMESTAMP}",

    # GRPO sampling
    # - 8 completions per prompt at temp=1.0 for diverse reasoning paths
    # - 1024 completion length for <think> section + answer
    num_generations=8,
    max_completion_length=int(os.environ.get("MAX_COMPLETION_LENGTH", "1024")),  # v12 runs set 2048 to match calibration
    # Held constant at 1.0 to MATCH the v10 calibration sampling temperature
    # (measure_v10_full.py samples at temp=1.0). Calibrating difficulty at one
    # temperature and training at another invalidates the goldilocks zone
    # measurement. Annealing callback removed below for the same reason.
    temperature=1.0,

    # ── Generation ──────────────────────────────────────────────────────
    # Plain model.generate() -- no vLLM, no paged attention.
    # vLLM colocate: PEFT + vLLM has known convergence bugs (trl#2856).
    # Paged attention: runs out of cache blocks at our batch size (128
    # sequences × 1024 tokens exceeds the default block pool).
    # For 1.5B on L40S (48GB), vanilla generation is fast enough and
    # the KV cache (~5GB for 128 sequences) fits easily.
    use_vllm=False,

    # ── Batch sizing ───────────────────────────────────────────────────
    # Effective batch per optimizer step = per_device_train_batch_size ×
    # gradient_accumulation_steps = 2 × 16 = 32 completions = 32 / 8 generations
    # = 4 UNIQUE PROMPTS per step. Over 120 steps that's 480 prompt-instances,
    # ~4.5 epochs over the 106-problem goldilocks train set. Because the train
    # set is all-goldilocks, ~all of those prompts produce gradient (no
    # ghost-batching / zero-gradient waste, unlike training the full set).
    per_device_train_batch_size=2,
    gradient_accumulation_steps=16,  # 2 × 16 = 32 completions = 4 unique prompts/step

    # Training schedule
    num_train_epochs=1,
    max_steps=int(os.environ.get("MAX_STEPS", "120")),   # override per run (e.g. 250 for the 400-problem 3-concept pilot)
    learning_rate=5e-5,              # halved from 1e-4 for stability
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    bf16=True,
    gradient_checkpointing=True,

    # ── Stability: KL penalty ──────────────────────────────────────────
    # Prevents policy drift from noisy updates. Without this, a few
    # outlier batches (all sweet-spot problems with extreme advantages)
    # can push the model too far from the base policy.
    # DeepSeek-R1 uses 0.001; we use 0.04 because our effective signal
    # is noisier (ghost batching) so we need a stronger anchor.
    beta=0.1,

    # ── DAPO loss + truncation masking ─────────────────────────────────
    # loss_type="dapo" (default): normalizes by active tokens in global
    # batch, eliminating length bias.
    # mask_truncated_completions: excludes cut-off completions from loss
    # so they don't get incorrectly penalized (DAPO paper recommendation).
    mask_truncated_completions=True,

    # Logging & saving
    logging_steps=1,
    save_steps=27,
    log_completions=True,            # log (prompt, completion) pairs to W&B
    num_completions_to_print=2,      # only print 2 examples to terminal
    report_to="wandb" if (os.environ.get("WANDB_API_KEY") or os.environ.get("WANDB_TOKEN")) else "none",

    # Misc
    seed=42,
)


# ── Log config ──────────────────────────────────────────────────────────────
eff_batch = (training_args.per_device_train_batch_size
             * training_args.gradient_accumulation_steps)
unique_prompts_per_step = eff_batch // training_args.num_generations

logger.info("Config:")
logger.info(f"  Model:            Qwen/Qwen2.5-7B-Instruct")
logger.info(f"  Mode:             GRPO (correctness + format reward)")
logger.info(f"  System prompt:    {ENTITY_TRACKING_PROMPT[:60]}...")
logger.info(f"  LoRA rank:        {peft_config.r}")
logger.info(f"  Num generations:  {training_args.num_generations}")
logger.info(f"  Batch size:       {training_args.per_device_train_batch_size}")
logger.info(f"  Grad accum steps: {training_args.gradient_accumulation_steps}")
logger.info(f"  Effective batch:  {eff_batch} sequences = {unique_prompts_per_step} unique prompts")
logger.info(f"  Learning rate:    {training_args.learning_rate}")
logger.info(f"  Beta (KL pen.):   {training_args.beta}")
logger.info(f"  Temperature:      {training_args.temperature}")
logger.info(f"  Max compl len:    {training_args.max_completion_length}")
logger.info(f"  Max steps:        {training_args.max_steps}")
logger.info(f"  Mask truncated:   {training_args.mask_truncated_completions}")
logger.info(f"  Generation:       model.generate() (no vLLM, no paged attn)")
logger.info(f"  Output dir:       {training_args.output_dir}")
logger.info(f"  W&B:              {training_args.report_to}")


# ── Trainer ─────────────────────────────────────────────────────────────────
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    torch_dtype=torch.bfloat16,
    device_map="cuda"
)
eval_tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
trainer = GRPOTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    reward_funcs=[correctness_reward, format_reward],
    peft_config=peft_config,
)

# Held-out eval. SAME grader (reward_func) + system prompt as training.
# Per-step monitor: held-out goldilocks, pass@8 @ temp 1.0 (the goldilocks
# pass-rate training should lift) + boxed_rate / mean_completion_tokens tripwires,
# at step 0, every EVAL_EVERY steps, and end. AMC is OFF for this hillclimb loop.
trainer.add_callback(HeldoutEvalCallback(
    eval_tokenizer,
    per_step_sets={"holdout_gold": holdout_skel},
    endpoint_sets=None,
    eval_every=EVAL_EVERY, k=EVAL_K, temperature=EVAL_TEMP,
    max_new_tokens=training_args.max_completion_length, logger=logger,
))


# ── Train ───────────────────────────────────────────────────────────────────
if os.environ.get("WANDB_API_KEY") or os.environ.get("WANDB_TOKEN"):
    import wandb
    wandb.login(key=os.environ.get("WANDB_API_KEY") or os.environ.get("WANDB_TOKEN"))
    # If your W&B account requires a team entity, set WANDB_ENTITY env var
    if os.environ.get("WANDB_ENTITY"):
        os.environ["WANDB_ENTITY"] = os.environ["WANDB_ENTITY"]
        wandb.init(project="tiny-math-solver", entity=os.environ["WANDB_ENTITY"])

logger.info("Starting training ...")

# Temperature annealing REMOVED: we hold temperature constant at 1.0 to match
# the calibration sampling temperature (measure_v10_full.py). Annealing 1.2->0.7
# meant the model trained against a difficulty profile that drifted away from the
# measured goldilocks zone (high temp early -> more too-hard, low temp late ->
# more too-easy), so the validated 40% goldilocks snapshot never held during the
# run. If annealing is ever reintroduced, re-calibrate across the same schedule.
import sys
_resume = None
for _i, _a in enumerate(sys.argv):
    if _a == "--resume_from_checkpoint" and _i + 1 < len(sys.argv):
        _resume = sys.argv[_i + 1]
print(f"[resume] resume_from_checkpoint = {_resume}")
trainer.train(resume_from_checkpoint=_resume)
trainer.save_model()

logger.info(f"Training complete! Model saved to: {training_args.output_dir}")
logger.info(f"=== Run finished: {datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')} ===")
import time
# INTENTIONAL: powers off the cloud GPU VM after the run to stop billing. Runs
# only after train + final held-out eval + save_model complete and a 60s disk
# flush. Keep this if launching on a billed VM; remove only if running somewhere
# you don't want auto-shutdown (e.g. a local/persistent machine).
logger.info("Waiting 60 seconds for disk flush before VM shutdown...")
time.sleep(60)
# os.system("sudo poweroff")  # gated on Lightning
