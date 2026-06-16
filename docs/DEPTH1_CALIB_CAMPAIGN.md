# Depth-1 chain calibration campaign (autonomous)

Autonomous N-iteration loop that calibrates the 47 depth-1 chains toward the
goldilocks band (pass ~0.45–0.55) **against the depth-0 checkpoint (ckpt-40)**.
Runs on the **t3** (autocalib): builds the pool locally, dispatches each sample to
**sam (L4)**, analyzes, lets `claude` edit the chain generators, gates + reverts,
commits to a branch, posts to Slack. Nothing is pushed to `main`.

## Pieces
- `tools/depth1_calib_campaign.py` — the loop driver (this runs on the t3).
- `analysis/depth1_calib_analyze.py` — per-chain difficulty + diversity readout.
- `tools/sample.py` (`CKPT=`), `tools/run_sample_job.sh` (`checkpoint`, s3 `dataset`) — #81 plumbing.

## Per-iteration flow
1. build the 47-chain pool from the current (edited) generators  [t3, CPU]
2. **gate**: atom-equivalence (depth-0 frozen) + gold recompute + dedupe/top3 + smoke
3. upload pool → S3; write sample spec → `pending/sam/`; `start` sam; it samples
   ckpt-40 and self-stops; poll S3 for `calib.json`                 [sam, L4 GPU]
4. analyze → flagged chains
5. `claude` edits the **chain layer only** toward goldilocks (depth-0 atomics frozen)
6. **re-gate; auto-revert** any edit that breaks it
7. write `results/depth1_calib_iter<N>.md`; commit to the branch; Slack

## Safety
- **Depth-0 atomics are frozen** by the atom-equivalence test — any edit perturbing an
  atom's output is reverted (protects the ckpt-40 calibration target).
- Chain golds independently recomputed; difficulty via step/constraint count only (§4).
- **Branch-only** (`agent/depth1-calib-campaign`); a human reviews + opens the PR.

## Prerequisites
- **PR #81 merged** (CKPT sampling + s3 dataset + the gated pool) — sam samples from `origin/main`.
- autocalib has the Anthropic key + `SLACK_WEBHOOK_URL` (it does) and AWS creds for
  `ec2 start-instances` + S3 (it does).
- Confirm the box's headless `claude` invocation matches `CLAUDE_CMD` (default `claude -p`).

## Deploy + launch (on the t3, run by a human — agents don't deploy to prod)
```bash
aws ssm start-session --target i-09d247668650dad2d
sudo su - autocalib
cd ~/calibrate-rl && git fetch -q && git checkout agent/depth1-calib-campaign && git pull -q
# DRY RUN first (no GPU/edits/slack/s3 writes — exercises pool build + gate + analyze):
DRY_RUN=1 N_ITERS=1 python3 tools/depth1_calib_campaign.py
# real run (5 iterations) under nohup so it survives disconnects:
nohup python3 tools/depth1_calib_campaign.py > ~/depth1_campaign.log 2>&1 &
tail -f ~/depth1_campaign.log
```

## Tunables (env)
`N_ITERS=5 N=250 ROLLOUTS=8 MAX_TOKENS=2048 POOL_N_PER_CHAIN=40 SAMPLE_TIMEOUT_MIN=300`
`CKPT_S3=… SAMPLER=sadie BUCKET=calibrate-rl-agent CLAUDE_CMD="claude -p"`

## Needs first-run validation (can't be tested off-box)
- The headless `claude` edit invocation (CLI flags/version on the box). The gate +
  auto-revert make a flaky edit step *safe* (worst case: no edit that iteration), but
  validate it produces real edits on iteration 1.
- sam's boot poller picking up `pending/sam/<job>.json` and self-stopping.
