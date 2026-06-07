#!/usr/bin/env bash
# One-line sampling launcher for a fresh Lightning studio (after git clone/pull):
#     bash tools/sample.sh
# Assumes Lightning's pre-installed PyTorch+CUDA. Installs transformers/accelerate,
# then runs the 2048-token, 500-problem, 8-rollout sampling in the background
# (survives terminal close), saving incrementally + resumably.
set -u
cd "$(dirname "$0")/.."                       # repo root
pip install -q transformers accelerate numpy 2>&1 | tail -1 || true
mkdir -p data
echo "launching sampling (nohup, background)…"
nohup python3 tools/sample.py > sample.log 2>&1 &
PID=$!
echo "PID $PID  |  log: sample.log  |  output: data/calib_v11_2048_7B.json"
echo "watch:   tail -f sample.log"
echo "count:   python3 -c \"import json;print(len(json.load(open('data/calib_v11_2048_7B.json'))))\""
echo "(crashed? just re-run  bash tools/sample.sh  — it resumes where it left off)"
