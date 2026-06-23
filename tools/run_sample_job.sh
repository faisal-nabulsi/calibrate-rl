#!/usr/bin/env bash
# run_sample_job.sh — GPU-box job runner: pull an S3 job spec, run it from the
# repo root, sync the output back to S3, report to Slack, power the box off.
#
# Usage:
#   tools/run_sample_job.sh <s3-spec-uri> [--no-shutdown] [--dry-run]
#
#   --no-shutdown   leave the box running when the job ends (default: shutdown)
#   --dry-run       fetch + parse the spec and print exactly what would run;
#                   no GPU work, no S3 upload, no Slack posts, no shutdown
#
# job.json spec fields:
#   type        "sample" | "train" | "setup" | "eval" — sample/train route to tools/sample.py
#               or train/train_grpo.py; setup runs tools/provision_box.sh to build the box's
#               rl-venv (how the queue-only L4s sam/sadie/sage get provisioned — no SSH/SSM);
#               eval runs an arbitrary `cmd` (any one-off eval) then self-stops — so an eval is
#               a queue dispatch, not a manual SSM session (see the eval branch below)
#   cmd         (eval) the command to run, under bash + repo-root PYTHONPATH; `{ckpt}` → the
#               downloaded checkpoint dir
#   output_file (eval) local path/glob produced by cmd; synced (newest match) to output_uri
#   concepts    optional list — sample only: build the pool first with
#               prep/gen_clean.py (one call per concept, merged)
#   n           sample: N_PROBLEMS (problems to calibrate)
#               train:  MAX_STEPS
#   rollouts    sample: N_ROLLOUTS per problem
#   max_tokens  sample: MAX_NEW_TOKENS · train: MAX_COMPLETION_LENGTH
#   output_uri  s3://... destination (file copied there; train syncs the run dir
#               under it). Required.
#   dataset     optional repo-relative path — sample: pool to draw from (default
#               data/skeleton_dataset_v11_clean.json, ignored when concepts set);
#               train: TRAIN_DATA (REQUIRED for train jobs)
#   holdout     optional (train) — HOLDOUT_DATA for the held-out monitor
#   eval_every          optional (train) — EVAL_EVERY (held-out monitor cadence in steps)
#   early_stop_patience optional (train) — EARLY_STOP_PATIENCE (set high, e.g. 999, to disable
#                       early stop so a run always completes its full MAX_STEPS)
#   early_stop_min_decline optional (train) — EARLY_STOP_MIN_DECLINE
#   lora_rank           optional (train) — LORA_RANK (adapter rank; alpha auto-scales to 2x)
#   per_device_batch    optional (train) — PER_DEVICE_BATCH
#   grad_accum          optional (train) — GRAD_ACCUM  (prompts/step = per_device_batch*grad_accum/8)
#   checkpoint  optional (sample) — LoRA adapter dir or s3:// uri; merged into the
#               base model so calibration samples a TRAINED checkpoint, not base
#               (e.g. depth-1 calibrates vs v12_depth0 checkpoint-40)
#
# Reporting: start/done/fail posted to $SLACK_WEBHOOK_URL if set (best-effort —
# a dead webhook never fails the job). The job log is uploaded next to the output.
# Identity: $AGENT_NAME (from /etc/calibrate-rl-job.env via systemd) else hostname.

set -uo pipefail   # deliberately no -e: failures must reach the fail-post + shutdown path
cd "$(dirname "$0")/.."

# GPU deps live in the box's rl-venv (torch/transformers); systemd gives us bare PATH.
[ -f "$HOME/rl-venv/bin/activate" ] && source "$HOME/rl-venv/bin/activate"
# ...but `source activate` has fallen through to system python3 under systemd before (PATH/HOME),
# silently running sample.py/train on a venv-less python (the depth1_calib_iter1 numpy death).
# Belt-and-suspenders: invoke the venv's python EXPLICITLY when it exists — no PATH dependency.
PY="python3"; [ -x "$HOME/rl-venv/bin/python3" ] && PY="$HOME/rl-venv/bin/python3"
# AGENT_NAME / SLACK_WEBHOOK_URL / ESCALATE_SLACK_ID come from systemd's EnvironmentFile;
# source it for hand-runs too, so a direct invocation reports under the right identity and
# can still page on failure (instead of falling back to the hostname / silent webhooks).
[ -f /etc/calibrate-rl-job.env ] && { set -a; . /etc/calibrate-rl-job.env; set +a; }

SPEC_URI=""
NO_SHUTDOWN=0
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --no-shutdown) NO_SHUTDOWN=1 ;;
    --dry-run)     DRY_RUN=1; NO_SHUTDOWN=1 ;;
    s3://*)        SPEC_URI="$arg" ;;
    *) echo "ERROR: unknown argument '$arg'" >&2; exit 2 ;;
  esac
done
if [ -z "$SPEC_URI" ]; then
  echo "usage: tools/run_sample_job.sh <s3-spec-uri> [--no-shutdown] [--dry-run]" >&2
  exit 2
fi

AGENT="${AGENT_NAME:-$(hostname)}"
JOB_ID="$(basename "$SPEC_URI" .json)"
LOG="logs/job_${JOB_ID}.log"
mkdir -p logs data
# TRUNCATE the per-job log at start: job names repeat across campaign runs (depth1_calib_iter1,
# ...), so an appended log carried STALE tail from a prior run — which the S3 heartbeat streams,
# making a healthy job look like it was on the old N/progress (the [17/500] vs [2/250] scare).
: > "$LOG"
# Operator-halt flag: when set in S3, a non-zero exit is an INTENTIONAL kill (someone ran
# tools/kill_run.sh), so finish() posts a calm note instead of a FAILED + DIAGNOSE page.
CONTROL_HALT="s3://calibrate-rl-agent/control/halt"
# CLEAR it at the START of every job: the flag is meant to suppress the page for the jobs the
# operator just killed (which already started before the kill). A brand-new job starting means
# the kill is consumed — so reset the state now, else a stale flag from a kill-without-relaunch
# would mask a REAL failure of this fresh job (the gap all 3 reviewers flagged). kill_run.sh sets
# the flag AFTER this point, so the killed job's own finish() still reads it.
aws s3 rm "$CONTROL_HALT" >/dev/null 2>&1 || true

# Recipients rendered as <@id> mentions (mentions trigger mobile push; channel
# posts don't). Two tiers:
#   NOTIFY  — tagged on EVERY notification (start/done/fail), per Faisal's request.
#   DEFAULT — the wider escalation set, added on failure pages only (so gilbert/on-call
#             aren't pinged on every routine success). Configurable via ESCALATE_SLACK_IDS
#             (or the legacy single ESCALATE). All tiers are deduped before sending.
NOTIFY_SLACK_IDS="U0B9661M6J2 U0B9C6JP2MC"               # faisal, michael — every post
DEFAULT_SLACK_IDS="U0B9661M6J2 U0B9C6JP2MC U0B9C278VPW"  # faisal, michael, gilbert — pages

slack_post() {
  [ -n "${SLACK_WEBHOOK_URL:-}" ] || return 0
  [ "$DRY_RUN" -eq 1 ] && return 0
  # $2 (optional) = extra Slack IDs to @mention beyond the always-tagged NOTIFY pair.
  local mentions
  mentions="$(printf '%s\n' $NOTIFY_SLACK_IDS ${2:-} \
    | awk 'NF && !seen[$0]++ {printf "<@%s> ", $0}')"
  curl -sf -X POST -H 'Content-type: application/json' \
    --data "$(python3 -c 'import json,sys;print(json.dumps({"text":sys.argv[1]}))' "[$AGENT] $1 ${mentions}")" \
    "$SLACK_WEBHOOK_URL" >/dev/null || true
}

# Single exit path: report, optionally power off, exit. Shutdown happens on
# success AND failure — a failed job must not leave the box burning money.
finish() {
  local code="$1" msg="$2"
  [ -n "${HB_PID:-}" ] && kill "$HB_PID" 2>/dev/null || true   # stop the progress heartbeat (any exit path)
  if [ "$code" -eq 0 ]; then
    echo "job $JOB_ID done — $msg"
    slack_post ":white_check_mark: job \`$JOB_ID\` done — $msg"
  elif aws s3 ls "$CONTROL_HALT" >/dev/null 2>&1; then
    # Operator killed the run (halt flag set) — NOT a real failure. Calm note, NO DIAGNOSE
    # page, NO escalation mentions, so the bots/on-call don't investigate an intentional stop.
    echo "job $JOB_ID stopped by operator (halt flag) — $msg"
    slack_post ":octagonal_sign: job \`$JOB_ID\` stopped by operator (intentional — no action needed)"
  else
    echo "job $JOB_ID FAILED — $msg" >&2
    slack_post ":x: job \`$JOB_ID\` FAILED — $msg (log: $LOG_URI)
DIAGNOSE NEEDED — auto-triage exhausted or not applicable; box is self-stopping, logs are synced." \
      "${ESCALATE_SLACK_IDS:-${ESCALATE:-}} $DEFAULT_SLACK_IDS"
  fi
  if [ "$NO_SHUTDOWN" -eq 0 ]; then
    # Stop the box's resident Slack agent first so it dies gracefully (its
    # SIGINT handler disconnects Socket Mode) — a hard death with the box
    # counts against Slack's delivery-failure budget and can get the app's
    # events disabled. Best-effort: a missing pm2/process never blocks poweroff.
    if command -v pm2 >/dev/null 2>&1; then
      pm2 stop "${AGENT_PM2_NAME:-$AGENT}" >/dev/null 2>&1 || pm2 stop all >/dev/null 2>&1 || true
    fi
    echo "powering off in 1 minute (--no-shutdown to keep the box up)"
    sudo shutdown -h +1
  fi
  exit "$code"
}

# --- update the worker checkout to current main BEFORE running ----------------
# Pure worker boxes otherwise run whatever was checked out at their last boot —
# stale code AND data (a pool added in a PR merged after boot would be missing,
# and the job would fail on a not-found dataset). Fatal-on-failure: running on a
# stale checkout silently produces wrong/zero results. reset --hard touches no
# untracked files, so generated job outputs/logs survive.
if ! ( git fetch -q origin main && git reset --hard origin/main ); then
  LOG_URI="(none)"; finish 1 "git update to origin/main failed — refusing to run on a stale checkout"
fi
echo "checkout at $(git rev-parse --short HEAD): $(git log -1 --format=%s | cut -c1-60)"

# --- fetch + parse the spec --------------------------------------------------
SPEC_LOCAL="/tmp/job_${JOB_ID}.json"
if ! aws s3 cp "$SPEC_URI" "$SPEC_LOCAL" >/dev/null 2>&1; then
  LOG_URI="(none)"
  finish 1 "could not fetch spec $SPEC_URI"
fi

PARSED="$(python3 - "$SPEC_LOCAL" <<'PY'
import json, sys, shlex
j = json.load(open(sys.argv[1]))
q = lambda x: shlex.quote(str(x))
print(f"JOB_TYPE={q(j.get('type', ''))}")
print(f"JOB_N={q(j.get('n', ''))}")
print(f"JOB_ROLLOUTS={q(j.get('rollouts', ''))}")
print(f"JOB_MAX_TOKENS={q(j.get('max_tokens', ''))}")
print(f"OUTPUT_URI={q(j.get('output_uri', ''))}")
print(f"JOB_DATASET={q(j.get('dataset', ''))}")
print(f"JOB_HOLDOUT={q(j.get('holdout', ''))}")
print(f"JOB_CONCEPTS={q(','.join(j.get('concepts') or []))}")
print(f"JOB_CKPT={q(j.get('checkpoint', ''))}")
print(f"JOB_BASE_CKPT={q(j.get('base_checkpoint', ''))}")
print(f"JOB_CMD={q(j.get('cmd', ''))}")
print(f"JOB_OUTPUT_FILE={q(j.get('output_file', ''))}")
print(f"JOB_SHARD_IDX={q(j.get('shard_idx', ''))}")
print(f"JOB_SHARD_TOTAL={q(j.get('shard_total', ''))}")
print(f"JOB_EVAL_EVERY={q(j.get('eval_every', ''))}")
print(f"JOB_EARLY_STOP={q(j.get('early_stop_patience', ''))}")
print(f"JOB_EARLY_STOP_DECLINE={q(j.get('early_stop_min_decline', ''))}")
print(f"JOB_LORA_RANK={q(j.get('lora_rank', ''))}")
print(f"JOB_PER_DEVICE_BATCH={q(j.get('per_device_batch', ''))}")
print(f"JOB_GRAD_ACCUM={q(j.get('grad_accum', ''))}")
PY
)" || { LOG_URI="(none)"; finish 1 "spec $SPEC_URI is not valid JSON"; }
eval "$PARSED"

LOG_URI="${OUTPUT_URI%/}.log"
case "$JOB_TYPE" in sample|train|setup|eval) ;; *) finish 1 "spec 'type' must be sample|train|setup|eval, got '$JOB_TYPE'";; esac
case "$OUTPUT_URI" in s3://*) ;; *) finish 1 "spec 'output_uri' must be an s3:// uri";; esac

# --- build the command -------------------------------------------------------
declare -a RUN_ENV
declare -a PREP_CMDS
RUN_CMD=""
SYNC_CMD=""

if [ "$JOB_TYPE" = "setup" ]; then
  # Provision the box's rl-venv sampling stack (idempotent). The queue-only L4s
  # (sam/sadie/sage) have no SSM/SSH path, so a fresh box is provisioned by dispatching a
  # setup job that the poller runs on boot. output_uri is just the log destination; nothing
  # to sync. Reuses the poller + self-stop machinery as-is.
  RUN_CMD="bash tools/provision_box.sh"
  SYNC_CMD=""
elif [ "$JOB_TYPE" = "sample" ]; then
  POOL="${JOB_DATASET:-data/skeleton_dataset_v11_clean.json}"
  case "$POOL" in
    # An s3:// dataset lets an orchestrator hand a pool built off-box (e.g. the depth-1
    # campaign builds the EDITED pool on the t3 and uploads it) without the box needing
    # that branch — it stays on origin/main. Pull it down to a local file for sample.py.
    s3://*) POOL_LOCAL="data/job_${JOB_ID}_pool.json"
            PREP_CMDS+=("aws s3 cp $POOL $POOL_LOCAL"); POOL="$POOL_LOCAL" ;;
  esac
  if [ -n "$JOB_CONCEPTS" ]; then
    # Build a fresh pool: one gen_clean per concept, merged. Per-concept size
    # defaults to gen_clean's own default (200) when 'n' is absent.
    POOL="data/job_${JOB_ID}_pool.json"
    for c in ${JOB_CONCEPTS//,/ }; do
      PREP_CMDS+=("python3 prep/gen_clean.py --concept $c ${JOB_N:+--n $JOB_N} --out data/job_${JOB_ID}_pool_${c}.json")
    done
    PREP_CMDS+=("python3 -c \"import json,glob; rows=[r for f in sorted(glob.glob('data/job_${JOB_ID}_pool_*.json')) for r in json.load(open(f))]; json.dump(rows, open('$POOL','w'))\"")
  fi
  OUT="data/job_${JOB_ID}_calib.json"
  CKPT_ENV=""
  if [ -n "$JOB_CKPT" ]; then
    # Sample a TRAINED checkpoint (e.g. depth-1 vs ckpt-40), not base. Pull the LoRA
    # adapter from S3 if needed; sample.py merges it into base at load.
    case "$JOB_CKPT" in
      s3://*) CKPT_DIR="checkpoint/job_${JOB_ID}_ckpt"
              PREP_CMDS+=("aws s3 cp --recursive --quiet ${JOB_CKPT%/} $CKPT_DIR") ;;
      *)      CKPT_DIR="$JOB_CKPT" ;;
    esac
    CKPT_ENV="CKPT=$CKPT_DIR"
  fi
  BASE_CKPT_ENV=""
  if [ -n "$JOB_BASE_CKPT" ]; then
    # Two-stage merge: a BASE adapter (e.g. ckpt-500) baked in before CKPT — eval a
    # depth-1 ckpt (a LoRA trained on base+ckpt-500). sample.py merges BASE_CKPT then CKPT.
    case "$JOB_BASE_CKPT" in
      s3://*) BASE_CKPT_DIR="checkpoint/job_${JOB_ID}_baseckpt"
              PREP_CMDS+=("aws s3 cp --recursive --quiet ${JOB_BASE_CKPT%/} $BASE_CKPT_DIR") ;;
      *)      BASE_CKPT_DIR="$JOB_BASE_CKPT" ;;
    esac
    BASE_CKPT_ENV="BASE_CKPT=$BASE_CKPT_DIR"
  fi
  RUN_ENV=(DATASET="$POOL" OUT="$OUT" ${CKPT_ENV:+$CKPT_ENV} ${BASE_CKPT_ENV:+$BASE_CKPT_ENV}
           ${JOB_N:+N_PROBLEMS="$JOB_N"}
           ${JOB_ROLLOUTS:+N_ROLLOUTS="$JOB_ROLLOUTS"}
           ${JOB_MAX_TOKENS:+MAX_NEW_TOKENS="$JOB_MAX_TOKENS"}
           ${JOB_SHARD_IDX:+SHARD_IDX="$JOB_SHARD_IDX"}
           ${JOB_SHARD_TOTAL:+SHARD_TOTAL="$JOB_SHARD_TOTAL"})
  RUN_CMD="$PY tools/sample.py"
  SYNC_CMD="aws s3 cp $OUT $OUTPUT_URI"
elif [ "$JOB_TYPE" = "eval" ]; then
  # Run an ARBITRARY eval/command, then self-stop — so a one-off eval is a queue dispatch
  # (drop a spec → the box runs it) instead of a manual SSM session. `cmd` runs under bash
  # (pipes/&& OK) with the repo root on PYTHONPATH, so evals importing top-level pkgs like
  # core/ just work (the footgun that needed a manual PYTHONPATH=.). A `{ckpt}` token in cmd
  # is replaced with the downloaded LoRA-adapter dir; `output_file` (path or glob) is synced
  # to output_uri (newest match). Example spec:
  #   {"type":"eval","checkpoint":"s3://…/checkpoint-40",
  #    "cmd":"python eval/eval_amc_baseline.py {ckpt}",
  #    "output_file":"results_qwen7b__*.json","output_uri":"s3://…/amc_baseline_ckpt40.json"}
  [ -n "$JOB_CMD" ] || finish 1 "eval job needs a 'cmd' field"
  if [ -n "$JOB_CKPT" ]; then
    case "$JOB_CKPT" in
      s3://*) CKPT_DIR="checkpoint/job_${JOB_ID}_ckpt"
              PREP_CMDS+=("aws s3 cp --recursive --quiet ${JOB_CKPT%/} $CKPT_DIR") ;;
      *)      CKPT_DIR="$JOB_CKPT" ;;
    esac
    JOB_CMD="${JOB_CMD//\{ckpt\}/$CKPT_DIR}"
  fi
  if [ -n "$JOB_BASE_CKPT" ]; then
    # Two-stage merge for eval: download the BASE adapter (e.g. ckpt-500) and substitute
    # {base_ckpt} in the cmd (e.g. eval_amc_coverage.py --base-checkpoint {base_ckpt} --checkpoint {ckpt}).
    case "$JOB_BASE_CKPT" in
      s3://*) BASE_CKPT_DIR="checkpoint/job_${JOB_ID}_baseckpt"
              PREP_CMDS+=("aws s3 cp --recursive --quiet ${JOB_BASE_CKPT%/} $BASE_CKPT_DIR") ;;
      *)      BASE_CKPT_DIR="$JOB_BASE_CKPT" ;;
    esac
    JOB_CMD="${JOB_CMD//\{base_ckpt\}/$BASE_CKPT_DIR}"
  fi
  EVAL_SH="/tmp/eval_cmd_${JOB_ID}.sh"
  { echo 'set -e'
    echo 'export PYTHONPATH="${PYTHONPATH:-.}"'
    echo "$JOB_CMD"
    [ -n "$JOB_OUTPUT_FILE" ] && echo "aws s3 cp \"\$(ls -t $JOB_OUTPUT_FILE | head -1)\" $OUTPUT_URI"
  } > "$EVAL_SH"
  RUN_CMD="bash $EVAL_SH"
  SYNC_CMD=""   # the eval script does its own output sync
else
  [ -n "$JOB_DATASET" ] || finish 1 "train job needs a 'dataset' field (TRAIN_DATA)"
  # An s3:// dataset/holdout lets an orchestrator hand a train set built off-box (e.g. a
  # per-concept trio set for the interference experiment) without committing it to the
  # branch — mirror the sample case: train_grpo.py json.load(open())s a LOCAL path, so pull
  # the s3:// uri down first. A non-s3 value (a repo path) passes through untouched.
  case "$JOB_DATASET" in
    s3://*) TRAIN_LOCAL="data/job_${JOB_ID}_train.json"
            PREP_CMDS+=("aws s3 cp $JOB_DATASET $TRAIN_LOCAL"); JOB_DATASET="$TRAIN_LOCAL" ;;
  esac
  case "$JOB_HOLDOUT" in
    s3://*) HOLD_LOCAL="data/job_${JOB_ID}_holdout.json"
            PREP_CMDS+=("aws s3 cp $JOB_HOLDOUT $HOLD_LOCAL"); JOB_HOLDOUT="$HOLD_LOCAL" ;;
  esac
  # Train ON TOP of a trained checkpoint (depth-1 off ckpt-40 / the rank-128 ckpt-500): pull the
  # base adapter and pass CKPT=<dir> so train_grpo merges it into base before the fresh LoRA. Same
  # download path as the sample/eval branches. No 'checkpoint' field => train from base Qwen.
  CKPT_ENV=""
  if [ -n "$JOB_CKPT" ]; then
    case "$JOB_CKPT" in
      s3://*) CKPT_DIR="checkpoint/job_${JOB_ID}_ckpt"
              PREP_CMDS+=("aws s3 cp --recursive --quiet ${JOB_CKPT%/} $CKPT_DIR") ;;
      *)      CKPT_DIR="$JOB_CKPT" ;;
    esac
    CKPT_ENV="CKPT=$CKPT_DIR"
  fi
  # Optional 2nd base adapter merged BEFORE CKPT (in-memory) — train depth-1.5/2 ON TOP of a multi-
  # adapter base (base + ckpt-500 [base_checkpoint] + depth-1 [checkpoint]) with NO 15GB consolidation
  # save. train_grpo merges BASE_CKPT then CKPT, then the fresh LoRA. Mirrors sample.py's two-stage load.
  BASE_CKPT_ENV=""
  if [ -n "$JOB_BASE_CKPT" ]; then
    case "$JOB_BASE_CKPT" in
      s3://*) BASE_CKPT_DIR="checkpoint/job_${JOB_ID}_baseckpt"
              PREP_CMDS+=("aws s3 cp --recursive --quiet ${JOB_BASE_CKPT%/} $BASE_CKPT_DIR") ;;
      *)      BASE_CKPT_DIR="$JOB_BASE_CKPT" ;;
    esac
    BASE_CKPT_ENV="BASE_CKPT=$BASE_CKPT_DIR"
  fi
  RUN_DIR="checkpoint/job_${JOB_ID}"
  RUN_ENV=(TRAIN_DATA="$JOB_DATASET" RESUME_OUTPUT_DIR="$RUN_DIR" ${CKPT_ENV:+$CKPT_ENV} ${BASE_CKPT_ENV:+$BASE_CKPT_ENV}
           ${JOB_HOLDOUT:+HOLDOUT_DATA="$JOB_HOLDOUT"}
           ${JOB_N:+MAX_STEPS="$JOB_N"}
           ${JOB_MAX_TOKENS:+MAX_COMPLETION_LENGTH="$JOB_MAX_TOKENS"}
           ${JOB_EVAL_EVERY:+EVAL_EVERY="$JOB_EVAL_EVERY"}
           ${JOB_EARLY_STOP:+EARLY_STOP_PATIENCE="$JOB_EARLY_STOP"}
           ${JOB_EARLY_STOP_DECLINE:+EARLY_STOP_MIN_DECLINE="$JOB_EARLY_STOP_DECLINE"}
           ${JOB_LORA_RANK:+LORA_RANK="$JOB_LORA_RANK"}
           ${JOB_PER_DEVICE_BATCH:+PER_DEVICE_BATCH="$JOB_PER_DEVICE_BATCH"}
           ${JOB_GRAD_ACCUM:+GRAD_ACCUM="$JOB_GRAD_ACCUM"})
  RUN_CMD="$PY train/train_grpo.py"
  SYNC_CMD="aws s3 sync $RUN_DIR ${OUTPUT_URI%/}/"
fi

if [ "$DRY_RUN" -eq 1 ]; then
  echo "DRY RUN — job $JOB_ID on $AGENT would do:"
  for p in "${PREP_CMDS[@]+"${PREP_CMDS[@]}"}"; do echo "  $p"; done
  echo "  env ${RUN_ENV[*]} $RUN_CMD"
  echo "  $SYNC_CMD"
  echo "  aws s3 cp $LOG $LOG_URI"
  echo "  (progress heartbeat → ${OUTPUT_URI%/}.heartbeat every ${HEARTBEAT_S:-120}s)"
  [ "$NO_SHUTDOWN" -eq 0 ] && echo "  sudo shutdown -h +1"
  exit 0
fi

# --- run ----------------------------------------------------------------------
slack_post ":rocket: job \`$JOB_ID\` started — type=$JOB_TYPE n=${JOB_N:-default} rollouts=${JOB_ROLLOUTS:-default} max_tokens=${JOB_MAX_TOKENS:-default} → $OUTPUT_URI"

for p in "${PREP_CMDS[@]+"${PREP_CMDS[@]}"}"; do
  echo "+ $p" >> "$LOG"
  if ! bash -c "$p" >> "$LOG" 2>&1; then
    aws s3 cp "$LOG" "$LOG_URI" >/dev/null 2>&1 || true
    finish 1 "pool build failed: $p"
  fi
done

# --- progress heartbeat -------------------------------------------------------
# Stream a small tail of the LIVE log to S3 every HEARTBEAT_S seconds so a reader
# (a human, the autocalib campaign, or another agent) can see liveness + ETA
# WITHOUT shell on the box — just `aws s3 cp ${OUTPUT_URI%/}.heartbeat -`. This is
# what was missing when jobs only synced logs at the END: mid-run, S3 showed
# nothing, so "is it alive / how far along" needed an SSM round-trip nobody could
# always make. Pure observability: it writes a SEPARATE .heartbeat key and never
# touches the authoritative .log/.json (those still sync only at the end), so the
# campaign's fail-detector semantics on .log are unchanged. Killed in finish().
HEARTBEAT_URI="${OUTPUT_URI%/}.heartbeat"
HEARTBEAT_S="${HEARTBEAT_S:-120}"
(
  while true; do
    sleep "$HEARTBEAT_S"
    { echo "[$JOB_ID] heartbeat $(date -u +%Y-%m-%dT%H:%M:%SZ) on $AGENT"
      nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader 2>/dev/null | head -1
      echo "--- last log lines ---"
      tail -n 15 "$LOG" 2>/dev/null
    } | aws s3 cp - "$HEARTBEAT_URI" >/dev/null 2>&1 || true
  done
) & HB_PID=$!

echo "+ env ${RUN_ENV[*]} $RUN_CMD" >> "$LOG"
if ! env "${RUN_ENV[@]}" $RUN_CMD >> "$LOG" 2>&1; then
  aws s3 cp "$LOG" "$LOG_URI" >/dev/null 2>&1 || true
  finish 1 "$RUN_CMD exited non-zero"
fi

# Self-check: a zero-exit run can still produce broken output. Verify before
# declaring success — a bad file that syncs cleanly poisons downstream work.
if [ "$JOB_TYPE" = "sample" ]; then
  # expected row count: when sharded, this box only samples JOB_N/SHARD_TOTAL of the slice.
  WANT="${JOB_N:-0}"
  if [ -n "$JOB_SHARD_TOTAL" ] && [ "${JOB_SHARD_TOTAL:-1}" -gt 1 ] 2>/dev/null; then
    WANT=$(( ${JOB_N:-0} / JOB_SHARD_TOTAL ))
  fi
  CHECK_MSG="$(python3 - "$OUT" "$WANT" <<'PYCHECK'
import json, sys
path, want = sys.argv[1], int(sys.argv[2])
try:
    rows = json.load(open(path))
    assert isinstance(rows, list) and rows, "output is not a non-empty list"
    assert all(isinstance(r, dict) for r in rows), "non-dict rows present"
    if want: assert len(rows) >= 0.9 * want, f"only {len(rows)}/{want} rows"
    print(f"OK {len(rows)} rows")
except Exception as e:
    print(f"FAIL {e}")
PYCHECK
)"
  echo "self-check: $CHECK_MSG" >> "$LOG"
  case "$CHECK_MSG" in FAIL*)
    aws s3 cp "$LOG" "$LOG_URI" >/dev/null 2>&1 || true
    finish 1 "output self-check failed: $CHECK_MSG"
  esac
fi

if ! $SYNC_CMD >> "$LOG" 2>&1; then
  aws s3 cp "$LOG" "$LOG_URI" >/dev/null 2>&1 || true
  finish 1 "output sync to $OUTPUT_URI failed (job output is still on the box)"
fi
aws s3 cp "$LOG" "$LOG_URI" >/dev/null 2>&1 || true

finish 0 "output at $OUTPUT_URI"
