from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import torch, json, re, sys

BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
CHECKPOINT = sys.argv[1] if len(sys.argv) > 1 else None

print(f"Loading base model: {BASE_MODEL}")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, dtype=torch.bfloat16, device_map="auto")

if CHECKPOINT:
    print(f"Loading LoRA adapter: {CHECKPOINT}")
    model = PeftModel.from_pretrained(model, CHECKPOINT)
    model = model.merge_and_unload()

model.eval()

dataset = load_dataset("AI-MO/aimo-validation-amc", split="train")
problems = list(dataset)
print(f"Loaded {len(problems)} AMC problems")

def extract_answer(text):
    m = re.search(r"\\boxed\{(-?[\d,\.]+)\}", text)
    if m:
        val = m.group(1).replace(",", "")
        try: return str(int(float(val)))
        except: return val
    m = re.search(r"[Tt]he\s+(?:final\s+)?answer\s+is\s*:?\s*(-?[\d,\.]+)", text)
    if m: return m.group(1).replace(",", "")
    numbers = re.findall(r"-?\d+\.?\d*", text)
    return numbers[-1] if numbers else None

results = []
correct = 0

for i, problem in enumerate(problems):
    question = problem["problem"]
    gold_answer = str(int(float(str(problem["answer"]).strip())))
    text_input = tokenizer.apply_chat_template(
        [{"role": "user", "content": question}],
        tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(text_input, return_tensors="pt").input_ids.to(model.device)
    with torch.no_grad():
        output = model.generate(
            inputs, max_new_tokens=512,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    response = tokenizer.decode(output[0][inputs.shape[1]:], skip_special_tokens=True)
    predicted = extract_answer(response)
    try:
        is_correct = predicted is not None and abs(float(str(predicted).replace(",","")) - float(str(gold_answer).replace(",",""))) < 1e-6
    except (ValueError, TypeError):
        is_correct = False
    if is_correct:
        correct += 1
    results.append({"problem_id": i, "question": question, "gold_answer": gold_answer, "model_response": response, "predicted_answer": predicted, "correct": is_correct})
    print(f"[{i+1}/{len(problems)}] {'V' if is_correct else 'X'}  Gold: {gold_answer}  Pred: {predicted}", flush=True)

label = CHECKPOINT.replace("/","_") if CHECKPOINT else "base"
out_file = f"results_qwen7b_{label}.json"
with open(out_file, "w") as f:
    json.dump(results, f, indent=2)
print(f"Accuracy: {correct}/{len(problems)} = {100*correct//len(problems)}%")
print(f"Saved to: {out_file}")
