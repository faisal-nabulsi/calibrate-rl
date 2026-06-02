import json
import random
import pandas as pd
from datasets import Dataset

SYSTEM_PROMPT = (
    "Think step by step inside <think> tags before answering. "
    "Show your work clearly and give a single numerical answer at the end."
)

def build_prompt(problem, reasoning):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": problem},
    ]

# Load skeleton dataset
with open('/teamspace/studios/this_studio/rl-intro/main/data/skeleton_dataset.json') as f:
    data = json.load(f)

print(f"Total skeleton problems: {len(data)}")

# Sample 300 for quick training run
random.shuffle(data)
sample = data[:300]

# Convert to GRPO format
rows = []
for item in sample:
    rows.append({
        "prompt": build_prompt(item["problem"], item["reasoning"]),
        "answer": item["answer"],
        "question": item["problem"],
    })

# Save as parquet
df = pd.DataFrame(rows)
output_path = "/teamspace/studios/this_studio/rl-intro/main/data/skeleton_grpo_train.parquet"
df.to_parquet(output_path, index=False)
print(f"Saved {len(rows)} problems to {output_path}")
print(f"\nExample:")
print(f"Question: {rows[0]['question']}")
print(f"Answer: {rows[0]['answer']}")
print(f"Prompt format: {rows[0]['prompt'][0]}")
