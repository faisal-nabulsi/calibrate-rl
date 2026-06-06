"""
Held-out evaluation for the depth-0 GRPO run.

WHY THIS EXISTS
GRPO maximizes the training reward. The training reward alone cannot tell you
whether the model is *learning math* or *learning to satisfy the grader on the
training templates*. The only way to separate those is to score weights that
were never trained on, with the SAME grader and prompt, at a fixed cadence.

This module provides:
  - make_skeleton_split(): deterministic, deduped, DISJOINT train/held-out split
    of a skeleton dataset (held-out = unseen number-instances of the SAME
    concepts -> measures in-distribution generalization, not memorization).
  - load_amc(): the real AMC eval (AI-MO/aimo-validation-amc). Never trained on
    -> measures transfer to the actual target.
  - evaluate(): pass@k with the canonical reward_func grader, plus two
    reward-hacking tripwires (boxed-rate and mean completion length).
  - HeldoutEvalCallback: runs evaluate() on both sets every N steps (and at
    step 0 for an attributable baseline), logging to console + W&B.

CONSISTENCY GUARANTEES (all three were violated by the old eval_*.py scripts):
  - same grader        -> imports extract_predicted_answer/_numbers_match from reward_func
  - same system prompt -> SYSTEM_PROMPT below == train_grpo.py / measure_v10_full.py
  - same gen length    -> max_new_tokens default 1024 == training completion length

DESIGN TRADE-OFFS (documented for review; all are knobs, not hard-coded):
  1. Held-out sets, split BY ROLE and BY CADENCE:
       - v10 held-out skeleton slice -> per-step TRAINING-HEALTH MONITOR
         (in-distribution: same concepts, unseen numbers). Watched every N steps
         because acting on it can't bias the capability claim (it only measures
         "got good at skeletons"). It does NOT prove transfer.
       - AMC -> the CAPABILITY CLAIM. Evaluated ONLY before + after, so it is
         never steered on (no adaptive overfitting / test-set peeking). The
         transfer curve, if wanted, is reconstructed post-hoc from saved
         checkpoints. NOTE: AMC is external; absolute number is contamination-
         confounded, so the before->after DELTA is the signal.
  2. Integration = in-training TrainerCallback.
       Simplest "every N steps", logs alongside training reward, single process.
       Cost: eval pauses training (adds wall-clock). A separate checkpoint-
       watcher would decouple it at the price of more moving parts / a 2nd GPU.
  3. Metric = pass@1 greedy (EVAL_K=1, EVAL_TEMP=0.0).
       Deterministic, cheap, clean curve, comparable to a greedy baseline.
       pass@k sampled (set EVAL_K=8, EVAL_TEMP=1.0) matches the 8-rollout
       calibration framing but costs ~Kx per eval. Left configurable.

NOTE: the absolute AMC number is confounded by possible pretraining
contamination of Qwen on AMC; the *delta* from the step-0 baseline is the
signal, which is why we always eval at step 0.
"""
from __future__ import annotations
import json
import torch

from reward_func import extract_predicted_answer, extract_gold_answer, _numbers_match

# Must match train_grpo.py / measure_v10_full.py exactly.
SYSTEM_PROMPT = ("You are a math problem solver. Think step by step and put your "
                 "final answer in \\boxed{}.")


# ── dataset prep ──────────────────────────────────────────────────────────────
def make_skeleton_split(path, n_holdout=100, seed=42, stratified=True):
    """Deterministic, deduped, disjoint split of a skeleton dataset.

    Dedupe is on the problem string so a held-out instance can never be a
    byte-identical copy of a training instance (skeleton generators can emit
    duplicates). Returns (train_rows, holdout_rows) as plain dicts.

    stratified=True (default): spread the held-out set as evenly as possible
    across skeleton_type concepts, so the per-step monitor can't miss a
    per-concept regression hiding in a concept a random draw happened to skip.
    Held-out = unseen number-instances of the SAME concepts (in-distribution).
    """
    import random
    from collections import defaultdict
    with open(path) as f:
        rows = json.load(f)
    seen, deduped = set(), []
    for r in rows:
        if r["problem"] not in seen:
            seen.add(r["problem"])
            deduped.append(r)
    n_holdout = min(n_holdout, len(deduped) // 5)   # never hold out >20%
    rng = random.Random(seed)

    if not stratified:
        order = deduped[:]
        rng.shuffle(order)
        hold = order[:n_holdout]
    else:
        groups = defaultdict(list)
        for r in deduped:
            groups[r.get("skeleton_type", "unknown")].append(r)
        concepts = sorted(groups)                   # sorted -> deterministic
        base, extra = divmod(n_holdout, len(concepts))
        hold = []
        for i, c in enumerate(concepts):
            insts = groups[c][:]
            rng.shuffle(insts)
            k = min(len(insts), base + (1 if i < extra else 0))
            hold += insts[:k]
        if len(hold) < n_holdout:                   # a concept too small to fill its quota
            held = {r["problem"] for r in hold}
            leftover = [r for r in deduped if r["problem"] not in held]
            rng.shuffle(leftover)
            hold += leftover[:n_holdout - len(hold)]

    held = {r["problem"] for r in hold}
    train = [r for r in deduped if r["problem"] not in held]
    return train, hold


def load_amc(limit=None):
    """Real AMC eval — held out by construction (training is on skeletons)."""
    from datasets import load_dataset
    ds = load_dataset("AI-MO/aimo-validation-amc", split="train")
    rows = [{"problem": r["problem"], "answer": str(r["answer"]).strip()} for r in ds]
    return rows[:limit] if limit else rows


# ── core eval ─────────────────────────────────────────────────────────────────
@torch.no_grad()
def evaluate(model, tokenizer, problems, *, system_prompt=SYSTEM_PROMPT,
             max_new_tokens=1024, k=1, temperature=0.0, batch_size=8):
    """pass@k over `problems` (list of {problem, answer}) with the real grader.

    Returns a metrics dict: pass@k, n, boxed_rate, mean_completion_tokens.
    boxed_rate and mean_completion_tokens are reward-hacking tripwires: if
    training reward climbs while boxed_rate collapses or length explodes, the
    policy is gaming format/length rather than reasoning.
    """
    was_training = model.training
    model.eval()
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    greedy = (temperature is None) or (temperature <= 0)
    if greedy:
        k = 1

    n = len(problems)
    n_correct = 0
    n_boxed = 0
    total_tokens = 0
    total_samples = 0

    for start in range(0, n, batch_size):
        batch = problems[start:start + batch_size]
        prompts = [
            tokenizer.apply_chat_template(
                [{"role": "system", "content": system_prompt},
                 {"role": "user", "content": p["problem"]}],
                tokenize=False, add_generation_prompt=True)
            for p in batch
        ]
        enc = tokenizer(prompts, return_tensors="pt", padding=True).to(model.device)
        gen_kwargs = dict(max_new_tokens=max_new_tokens,
                          pad_token_id=tokenizer.eos_token_id,
                          num_return_sequences=k)
        if greedy:
            gen_kwargs.update(do_sample=False)
        else:
            gen_kwargs.update(do_sample=True, temperature=temperature, top_p=0.95)
        out = model.generate(**enc, **gen_kwargs)
        gen = out[:, enc["input_ids"].shape[1]:]             # new tokens only
        texts = tokenizer.batch_decode(gen, skip_special_tokens=True)

        for i, p in enumerate(batch):
            gold = extract_gold_answer(str(p["answer"]))
            samples = texts[i * k:(i + 1) * k]
            rows = gen[i * k:(i + 1) * k]
            hit = False
            for s, toks in zip(samples, rows):
                pred, method = extract_predicted_answer(s)
                if method == "boxed":
                    n_boxed += 1
                total_tokens += int((toks != tokenizer.eos_token_id).sum().item())
                total_samples += 1
                if gold is not None and pred is not None and _numbers_match(pred, gold):
                    hit = True
            n_correct += int(hit)

    if was_training:
        model.train()
    return {
        f"pass@{k}": round(n_correct / n, 4) if n else 0.0,
        "n": n,
        "boxed_rate": round(n_boxed / total_samples, 4) if total_samples else 0.0,
        "mean_completion_tokens": round(total_tokens / total_samples, 1) if total_samples else 0.0,
    }


# ── training callback ─────────────────────────────────────────────────────────
try:
    from transformers import TrainerCallback
except Exception:                                   # allows import without transformers
    TrainerCallback = object


class HeldoutEvalCallback(TrainerCallback):
    """Two cadences, two roles:

      per_step_sets  -> evaluated at step 0, every `eval_every` steps, and at the
                        end. This is the TRAINING-HEALTH MONITOR (the in-
                        distribution v10 held-out slice). Safe to watch often.

      endpoint_sets  -> evaluated ONLY at train-begin and train-end. This is the
                        CAPABILITY CLAIM (external AMC). Measured exactly twice so
                        it is never used to steer the run -> no adaptive
                        overfitting / test-set peeking. (You can still rebuild the
                        full AMC curve afterwards by retro-evaluating the saved
                        checkpoints, since no mid-run decision touched AMC.)
    """

    def __init__(self, tokenizer, per_step_sets=None, endpoint_sets=None,
                 eval_every=50, max_new_tokens=1024, k=1, temperature=0.0,
                 batch_size=8, logger=None):
        self.tok = tokenizer
        self.per_step = dict(per_step_sets or {})
        self.endpoint = dict(endpoint_sets or {})
        self.every = eval_every
        self.kw = dict(max_new_tokens=max_new_tokens, k=k,
                       temperature=temperature, batch_size=batch_size)
        self.log = logger
        self._began = False

    def _run(self, model, step, sets, when):
        for name, probs in sets.items():
            m = evaluate(model, self.tok, probs, **self.kw)
            line = f"[holdout-eval step {step} | {when}] {name}: " + \
                   "  ".join(f"{k}={v}" for k, v in m.items())
            print(line, flush=True)
            if self.log:
                self.log.info(line)
            try:
                import wandb
                if wandb.run is not None:
                    wandb.log({f"eval/{name}/{k}": v for k, v in m.items()}, step=step)
            except Exception:
                pass

    def on_train_begin(self, args, state, control, model=None, **kw):
        if model is not None and not self._began:   # baseline: monitor + AMC "before"
            self._began = True
            self._run(model, 0, {**self.per_step, **self.endpoint}, "begin")

    def on_step_end(self, args, state, control, model=None, **kw):
        if model is not None and state.global_step > 0 and state.global_step % self.every == 0:
            self._run(model, state.global_step, self.per_step, "periodic")  # monitor only

    def on_train_end(self, args, state, control, model=None, **kw):
        if model is not None:                       # final: monitor + AMC "after"
            self._run(model, state.global_step, {**self.per_step, **self.endpoint}, "end")


# ── standalone: eval base model or any checkpoint on both held-out sets ────────
if __name__ == "__main__":
    import argparse
    from transformers import AutoTokenizer, AutoModelForCausalLM

    ap = argparse.ArgumentParser(description="Held-out eval of base model or a LoRA checkpoint.")
    ap.add_argument("--base", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--checkpoint", default=None, help="LoRA adapter dir (omit for base)")
    ap.add_argument("--skeletons", default="data/skeleton_dataset_v10.json")
    ap.add_argument("--n-holdout", type=int, default=100)
    ap.add_argument("--amc-limit", type=int, default=None)
    ap.add_argument("--k", type=int, default=1)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-new-tokens", type=int, default=1024)
    ap.add_argument("--batch-size", type=int, default=8)
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(args.base)
    model = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=torch.bfloat16,
                                                 device_map="auto")
    if args.checkpoint:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.checkpoint).merge_and_unload()

    _, holdout = make_skeleton_split(args.skeletons, n_holdout=args.n_holdout)
    amc = load_amc(limit=args.amc_limit)
    kw = dict(k=args.k, temperature=args.temperature,
              max_new_tokens=args.max_new_tokens, batch_size=args.batch_size)
    tag = args.checkpoint or "BASE"
    print(f"=== {tag} ===")
    print("AMC          :", evaluate(model, tok, amc, **kw))
    print("held-out skel:", evaluate(model, tok, holdout, **kw))
