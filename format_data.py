import json
import pandas as pd
from datasets import Dataset

# Path to your combined 3,924 problems
input_path = '/teamspace/studios/this_studio/rl-intro/main/data/skeleton_dataset.json'
output_path = '/teamspace/studios/this_studio/rl-intro/main/data/grpo_train_set.parquet'

with open(input_path, 'r') as f:
    data = json.load(f)

# GRPO needs the 'prompt' (input) and 'answer' (for the reward function)
formatted = []
for item in data:
    formatted.append({
        "prompt": [
            {"role": "user", "content": item["problem"]}
        ],
        "answer": item["answer"]
    })

df = pd.DataFrame(formatted)
ds = Dataset.from_pandas(df)
ds.to_parquet(output_path)

print(f"✅ Created GRPO dataset with {len(ds)} samples at {output_path}")
