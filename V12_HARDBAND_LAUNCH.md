# v12 hard-band run — launch runbook

**Experiment:** identical to the v12 run-2 setup, with ONE change — the training set is pass-rate
pre-filtered to the harder band (base 8-rollout `calib_correct` ≤ 5/8), filtering out the
already-easy problems. Held-out set is **unchanged** (`data/v12_holdout.json`) to stay comparable.

**Training set:** `data/v12_hardband_0to5_train.json` — **413** problems, band `[0,5]/8`.
- Keeps the 90 `0/8` too-hard problems on purpose: with no dynamic re-filtering, they stay in so they
  can pick up gradient *as the policy improves mid-run* (once a group lands ≥1/8 they stop being ghost
  batches). Early on they contribute zero gradient; that's the accepted cost.
- 112 steps × 4 unique prompts/step ÷ 413 ≈ **1.08 epochs** (same ~1-epoch exposure as v12's 449).
- Alt available if wanted: `data/v12_hardband_1to5_train.json` (323, drops the `0/8`).

## Launch (run inside tmux `hardband`)

```sh
cd ~/calibrate-rl && git pull && \
export WANDB_API_KEY=$(awk '/api\.wandb\.ai/{f=1} f&&/password/{print $2; exit}' ~/.netrc) && \
TRAIN_DATA=data/v12_hardband_0to5_train.json \
HOLDOUT_DATA=data/v12_holdout.json \
MAX_COMPLETION_LENGTH=2048 \
SAVE_STEPS=10 EVAL_EVERY=10 EVAL_K=4 MAX_STEPS=112 \
PER_DEVICE_BATCH=2 GRAD_ACCUM=16 \
EARLY_STOP_PATIENCE=2 EARLY_STOP_MIN_DECLINE=0.02 \
SYNC_S3_URI=s3://calibrate-rl-agent/runs/v12_hardband_run1/ \
WANDB_ENTITY=rl-intro \
python train/train_grpo.py > logs/hardband_run1.log 2>&1
```

Everything except `TRAIN_DATA` and `SYNC_S3_URI` matches v12 run-2 (no vLLM, batch 2×16, 2048 ctx).
W&B key is read from the box's netrc at launch (never written to disk).

## Two things worth deciding for THIS experiment's goal

1. **Early-stop may cut it before the hard band comes online.** Early-stop watches the *full* held-out
   `mean_pass_rate`; the easy 24/79 saturate fast, so a plateau there could stop the run while the hard
   problems are still improving. If the point is to let the `0/8` bake, set
   **`EARLY_STOP_PATIENCE=999`** (effectively off → runs all 112 steps). Default above keeps `=2`
   (exact-same-as-v12).
2. **More epochs help the `0/8` crack.** At 1.08 epochs each hard problem is seen ~once. Raising
   `MAX_STEPS` gives them more chances to come online. Default keeps `112` (exact-same-as-v12).

## End-of-run metric (the actual point)

The held-out is fixed, so re-score it restricted to the hard band to filter out the already-easy stuff:

```sh
python tools/eval_hard_subset.py \
  --transcripts s3://calibrate-rl-agent/runs/v12_hardband_run1/holdout_transcripts/ --band-max 5
```

Reports `mpr_FULL` vs `mpr_HARD` per step (hard = 55/79 of the held-out). The headline is whether
`mpr_HARD` moves base→best. Optional K=8 headline re-eval on the best checkpoint via
`tools/eval_checkpoint.py` (pulls checkpoint from `s3://.../v12_hardband_run1/checkpoint-N/`).
