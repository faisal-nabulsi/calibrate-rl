import os
import re
import logging
from datetime import datetime, timezone

RUN_TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
LOG_DIR = "./logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"skeleton_run_{RUN_TIMESTAMP}.log")

_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
_file_handler = logging.FileHandler(LOG_FILE)
_file_handler.setFormatter(_formatter)
_file_handler.setLevel(logging.INFO)
_root_logger = logging.getLogger()
_root_logger.setLevel(logging.INFO)
_root_logger.addHandler(_file_handler)
logger = logging.getLogger("skeleton_trainer")

from datasets import load_dataset
from peft import LoraConfig
from trl import GRPOTrainer, GRPOConfig

logger.info(f"=== Skeleton Training Run: {RUN_TIMESTAMP} ===")

# ── Reward Function ──────────────────────────────────────────────────────────
def extract_answer(text):
    # Look for boxed answer first
    match = re.search(r'\\boxed\{([^}]+)\}', text)
    if match:
        return match.group(1).strip()
    # Look for "answer is X"
    match = re.search(r'answer is[:\s]+([0-9/\.\-]+)', text.lower())
    if match:
        return match.group(1).strip()
    # Last number in response
    numbers = re.findall(r'-?\d+\.?\d*', text)
    return numbers[-1] if numbers else None

def correctness_reward(prompts, completions, answer, **kwargs):
    rewards = []
    for completion, gold in zip(completions, answer):
        text = completion[0]["content"] if isinstance(completion, list) else completion
        predicted = extract_answer(text)
        # Handle fractions
        try:
            if "/" in str(gold):
                from fractions import Fraction
                gold_val = float(Fraction(gold))
                pred_val = float(Fraction(predicted)) if predicted and "/" in predicted else float(predicted) if predicted else None
                correct = pred_val is not None and abs(pred_val - gold_val) < 0.01
            else:
                correct = predicted is not None and str(predicted).strip() == str(gold).strip()
        except:
            correct = False
        rewards.append(1.0 if correct else 0.0)
    return rewards

# ── Dataset ──────────────────────────────────────────────────────────────────
logger.info("Loading skeleton dataset...")
dataset = load_dataset(
    "parquet",
    data_files={"train": "main/data/skeleton_grpo_train.parquet"},
    split="train"
)
logger.info(f"Loaded {len(dataset)} skeleton problems")

# ── LoRA ─────────────────────────────────────────────────────────────────────
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    bias="none",
    task_type="CAUSAL_LM",
)

# ── Training Config ───────────────────────────────────────────────────────────
training_args = GRPOConfig(
    output_dir="./checkpoint/skeleton",

    num_train_epochs=1,
    max_steps=100,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,
    num_generations=4,
    max_completion_length=512,
    learning_rate=1e-4,
    beta=0.001,
    temperature=0.9,
    logging_steps=5,
    save_steps=50,
    report_to="none",
)

# ── Trainer ───────────────────────────────────────────────────────────────────
trainer = GRPOTrainer(
    model="Qwen/Qwen2.5-1.5B-Instruct",
    args=training_args,
    train_dataset=dataset,
    reward_funcs=correctness_reward,
    peft_config=peft_config,
)

logger.info("Starting training...")
trainer.train()
logger.info("Training complete!")
trainer.save_model("./checkpoint/skeleton/final")
logger.info("Model saved to ./checkpoint/skeleton/final")
