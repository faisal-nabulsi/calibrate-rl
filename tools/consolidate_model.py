#!/usr/bin/env python3
"""
consolidate_model.py — bake a base model + a chain of LoRA adapters into ONE merged
full model, saved + uploaded to S3. This collapses a growing adapter stack (base +
ckpt-500 + depth-1 + ...) into a single base checkpoint, so downstream training/eval
points at one MODEL with no N-way merge juggling (the curriculum-continuation path).

Usage:
  python tools/consolidate_model.py <adapter1_dir> [<adapter2_dir> ...] <s3_out_uri> [--base <hf_model>]

Adapters are merged in the given ORDER (so the earliest = closest to base). For the
depth-1 model:
  python tools/consolidate_model.py <ckpt-500_dir> <depth-1_dir> s3://.../models/depth1_consolidated/
= base Qwen -> merge ckpt-500 -> merge depth-1 -> one model. Use that S3 dir as MODEL
for depth-1.5 continuation training (a plain fresh LoRA on top, no stacking).
"""
import sys, os, subprocess, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

args = sys.argv[1:]
BASE = "Qwen/Qwen2.5-7B-Instruct"
if "--base" in args:
    i = args.index("--base"); BASE = args[i + 1]; del args[i:i + 2]
if len(args) < 2:
    sys.exit("usage: consolidate_model.py <adapter1> [<adapter2> ...] <s3_out_uri> [--base <hf>]")
*adapters, s3_out = args
# Write to the EBS volume (the repo cwd, where run_sample_job already stages 10s of GB of
# checkpoints), NOT /tmp — /tmp is tmpfs/small on these boxes, so a ~15GB save OOMs / disk-fulls
# the box and the process dies mid-write (both the L4 and L40S consolidation attempts died exactly
# there, leaving an orphaned .tmp). Fail LOUD if the target can't hold a 7B save rather than dying silently.
import shutil
OUT = os.environ.get("CONSOLIDATE_OUT", os.path.abspath("consolidated_model_out"))
_free_gb = shutil.disk_usage(os.path.dirname(OUT) or ".").free / 1e9
if _free_gb < 20:
    sys.exit(f"FATAL: only {_free_gb:.0f}GB free for the model save at {OUT} — need >=20GB for a 7B. "
             f"Set CONSOLIDATE_OUT to a bigger volume.")

print(f"base={BASE}\nadapters (in merge order)={adapters}\n-> {s3_out}", flush=True)
tok = AutoTokenizer.from_pretrained(BASE)
model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="cuda")
for a in adapters:
    model = PeftModel.from_pretrained(model, a).merge_and_unload()
    print(f"merged adapter: {a}", flush=True)

os.makedirs(OUT, exist_ok=True)
model.save_pretrained(OUT, safe_serialization=True)
tok.save_pretrained(OUT)
sz = subprocess.run(["du", "-sh", OUT], capture_output=True, text=True).stdout.split()[0]
print(f"saved consolidated model to {OUT} ({sz})", flush=True)

subprocess.run(["aws", "s3", "cp", "--recursive", "--quiet", OUT, s3_out.rstrip("/") + "/"], check=True)
print(f"uploaded consolidated model -> {s3_out}", flush=True)
with open("/tmp/consolidate_done.txt", "w") as f:
    f.write(f"consolidated {BASE} + {adapters} -> {s3_out} ({sz})\n")
