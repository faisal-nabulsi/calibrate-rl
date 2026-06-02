f = "measure_environment.py"
s = open(f).read()

# 1. FAIRNESS: seed before shuffle so every model sees the SAME 100 problems
assert "random.shuffle(data)" in s, "shuffle anchor not found"
assert "random.seed" not in s, "a seed already exists - check the file"
s = s.replace("random.shuffle(data)", "random.seed(42)\nrandom.shuffle(data)")

# 2. make the model swappable via env var MODEL (no editing between runs)
if "import os" not in s:
    s = s.replace("import json", "import os, json", 1)
assert 'BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"' in s, "BASE_MODEL anchor not found"
s = s.replace('BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"',
              'BASE_MODEL = os.environ.get("MODEL", "Qwen/Qwen2.5-7B-Instruct")')

# 3. smaller sample for the quick capability check
s = s.replace("N_PROBLEMS = 300", "N_PROBLEMS = 100")

open(f, "w").write(s)
print("capability patch applied")
