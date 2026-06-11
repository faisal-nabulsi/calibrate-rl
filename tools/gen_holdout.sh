#!/usr/bin/env bash
# base-vs-trained held-out generation (an L4 is plenty). Run once per checkpoint;
# the BASE pass is cached per held-out set so you don't regenerate it each time.
#   bash tools/gen_holdout.sh <CHECKPOINT_DIR> [HELDOUT_JSON] [MAX_NEW_TOKENS] [N_ROLLOUTS]
#
# v10 over-training demo (12 Q, ctx 1024):
#   bash tools/gen_holdout.sh checkpoint/run_20260607_033330/checkpoint-81  data/goldilocks_holdout_v10.json 1024
#   bash tools/gen_holdout.sh checkpoint/run_20260607_033330/checkpoint-120 data/goldilocks_holdout_v10.json 1024
# 3-concept (15 Q, ctx 2048):
#   bash tools/gen_holdout.sh checkpoint/abl3_v12_200/checkpoint-108 data/abl3_holdout.json 2048
#
# Then: git add results/holdout_resp_*.json && git commit -m 'held-out responses' && git push
set -u
cd "$(dirname "$0")/.."
CKPT="${1:?usage: bash tools/gen_holdout.sh <checkpoint_dir> [heldout_json] [max_new_tokens] [n_rollouts]}"
HELDOUT="${2:-data/abl3_holdout.json}"
MAXNEW="${3:-2048}"
ROLLS="${4:-8}"
HOTAG=$(basename "$HELDOUT" .json)
CKTAG=$(basename "$CKPT")
BASE_OUT="results/holdout_resp_base__${HOTAG}.json"
TR_OUT="results/holdout_resp_${CKTAG}__${HOTAG}.json"

[ -f "$CKPT/adapter_config.json" ] || echo "WARN: no adapter_config.json in $CKPT — is that the LoRA dir?"
pip install -q transformers peft accelerate numpy 2>&1 | tail -1 || true

if [ -f "$BASE_OUT" ]; then
  echo ">>> BASE cached ($BASE_OUT) — skipping"
else
  echo ">>> BASE (no checkpoint)"
  HELDOUT="$HELDOUT" MAX_NEW_TOKENS="$MAXNEW" N_ROLLOUTS="$ROLLS" OUT="$BASE_OUT" python3 tools/gen_holdout_responses.py
fi
echo ">>> TRAINED $CKTAG"
CHECKPOINT="$CKPT" HELDOUT="$HELDOUT" MAX_NEW_TOKENS="$MAXNEW" N_ROLLOUTS="$ROLLS" OUT="$TR_OUT" python3 tools/gen_holdout_responses.py
echo "DONE -> $BASE_OUT + $TR_OUT  (re-run for the next checkpoint, then commit+push results/holdout_resp_*.json)"
