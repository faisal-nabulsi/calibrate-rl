f = "measure_environment.py"   # <-- on your box, same name
s = open(f).read()

if "num_return_sequences" in s:
    print("already batched - nothing to do"); raise SystemExit

# 1. add a batch-size knob next to N_ROLLOUTS (defaults to all rollouts in one call)
assert "N_ROLLOUTS = " in s, "N_ROLLOUTS anchor not found"
import re
s = re.sub(r"(N_ROLLOUTS = \d+)",
           r"\1\nGEN_BATCH = N_ROLLOUTS  # rollouts generated per GPU call; lower (e.g. 8) only if you hit OOM",
           s, count=1)

# 2. replace the one-at-a-time loop with a single batched call (chunked by GEN_BATCH)
old = '''    for r in range(N_ROLLOUTS):
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=1.0,
                do_sample=True,
            )
        response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        predicted = extract_answer(response)

        try:
            correct = predicted is not None and abs(float(predicted) - float(gold)) < 1e-6
        except:
            correct = predicted is not None and predicted.strip() == gold.strip()

        reward = 1.0 if correct else 0.0
        rollout_rewards.append(reward)
        rollout_texts.append(response)'''

new = '''    remaining = N_ROLLOUTS
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
            predicted = extract_answer(response)
            try:
                correct = predicted is not None and abs(float(predicted) - float(gold)) < 1e-6
            except:
                correct = predicted is not None and predicted.strip() == gold.strip()
            rollout_rewards.append(1.0 if correct else 0.0)
            rollout_texts.append(response)
        remaining -= k'''

assert old in s, "generation loop not found verbatim - check the file state"
s = s.replace(old, new)
open(f, "w").write(s)
print("batching patch applied")
