f = "measure_environment.py"
s = open(f).read()

old_prompt = 'prompt = f"Solve this math problem step by step.\\n\\nProblem: {problem}\\n\\nSolution:"'
new_prompt = ('messages = [\n'
              '        {"role": "system", "content": "You are a math problem solver. Think step by step and put your final answer in \\\\boxed{}."},\n'
              '        {"role": "user", "content": problem},\n'
              '    ]\n'
              '    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)')
assert old_prompt in s, "prompt anchor not found"
s = s.replace(old_prompt, new_prompt)

assert "max_new_tokens=256" in s, "token anchor not found"
s = s.replace("max_new_tokens=256", "max_new_tokens=1024")
assert "temperature=0.9" in s, "temp anchor not found"
s = s.replace("temperature=0.9", "temperature=1.0")
s = s.replace("< 0.01", "< 1e-6")
s = s.replace("/teamspace/studios/this_studio/rl-intro/main/data/", "data/")
s = s.replace("skeleton_dataset_v3.json", "skeleton_dataset_v4.json")
s = s.replace("environment_quality_v3.json", "environment_quality_v4.json")
s = s.replace("N_PROBLEMS = 100", "N_PROBLEMS = 300")

open(f, "w").write(s)
print("F1 patched:", f)
