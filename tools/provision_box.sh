#!/usr/bin/env bash
# provision_box.sh — build the rl-venv SAMPLING stack on an L4 sampling box, idempotently.
#
# WHY THIS EXISTS: the L4 samplers (sam/sadie/sage) are queue-only — no SSM agent, no
# inbound SSH (different VPC from the t3, SG-locked), reachable ONLY by polling the S3
# job queue outbound. So a fresh/bare L4 (e.g. sadie: `ModuleNotFoundError: numpy`) can't
# be provisioned by hand — it's provisioned by dispatching a `setup` job (run_sample_job.sh
# type=setup runs THIS), which the box's poller executes on boot. Safe to re-run.
#
# The venv persists on the box's EBS volume across stop/start, so this is a one-time cost
# per box. Sampling only needs torch/transformers/peft/numpy (trl/wandb are training-only).
set -uo pipefail
echo "== provision_box on $(hostname) — $(date -u) =="
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>/dev/null || echo "(no nvidia-smi)"

[ -d "$HOME/rl-venv" ] || python3 -m venv "$HOME/rl-venv"
source "$HOME/rl-venv/bin/activate"
pip install --upgrade pip

# torch must come from the cu124 index (matches the L4 driver); the rest from PyPI.
pip install "torch==2.6.0" --index-url https://download.pytorch.org/whl/cu124
pip install transformers peft numpy accelerate sympy

python3 - <<'PY'
import torch, transformers, peft, numpy
print("PROVISION OK | torch", torch.__version__, "| transformers", transformers.__version__,
      "| cuda", torch.cuda.is_available())
PY
echo "== provision_box done =="
