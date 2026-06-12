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
#   type        "sample" | "train" — routes to tools/sample.py or train/train_grpo.py
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
#
# Reporting: start/done/fail posted to $SLACK_WEBHOOK_URL if set (best-effort —
# a dead webhook never fails the job). The job log is uploaded next to the output.
# Identity: $AGENT_NAME (from /etc/calibrate-rl-job.env via systemd) else hostname.

set -uo pipefail   # deliberately no -e: failures must reach the fail-post + shutdown path
cd "$(dirname "$0")/.."

# GPU deps live in the box's rl-venv (torch/transformers); systemd gives us bare PATH.
[ -f "$HOME/rl-venv/bin/activate" ] && source "$HOME/rl-venv/bin/activate"
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
  if [ "$code" -eq 0 ]; then
    echo "job $JOB_ID done — $msg"
    slack_post ":white_check_mark: job \`$JOB_ID\` done — $msg"
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
PY
)" || { LOG_URI="(none)"; finish 1 "spec $SPEC_URI is not valid JSON"; }
eval "$PARSED"

LOG_URI="${OUTPUT_URI%/}.log"
case "$JOB_TYPE" in sample|train) ;; *) finish 1 "spec 'type' must be sample|train, got '$JOB_TYPE'";; esac
case "$OUTPUT_URI" in s3://*) ;; *) finish 1 "spec 'output_uri' must be an s3:// uri";; esac

# --- build the command -------------------------------------------------------
declare -a RUN_ENV
declare -a PREP_CMDS
RUN_CMD=""
SYNC_CMD=""

if [ "$JOB_TYPE" = "sample" ]; then
  POOL="${JOB_DATASET:-data/skeleton_dataset_v11_clean.json}"
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
  RUN_ENV=(DATASET="$POOL" OUT="$OUT"
           ${JOB_N:+N_PROBLEMS="$JOB_N"}
           ${JOB_ROLLOUTS:+N_ROLLOUTS="$JOB_ROLLOUTS"}
           ${JOB_MAX_TOKENS:+MAX_NEW_TOKENS="$JOB_MAX_TOKENS"})
  RUN_CMD="python3 tools/sample.py"
  SYNC_CMD="aws s3 cp $OUT $OUTPUT_URI"
else
  [ -n "$JOB_DATASET" ] || finish 1 "train job needs a 'dataset' field (TRAIN_DATA)"
  RUN_DIR="checkpoint/job_${JOB_ID}"
  RUN_ENV=(TRAIN_DATA="$JOB_DATASET" RESUME_OUTPUT_DIR="$RUN_DIR"
           ${JOB_HOLDOUT:+HOLDOUT_DATA="$JOB_HOLDOUT"}
           ${JOB_N:+MAX_STEPS="$JOB_N"}
           ${JOB_MAX_TOKENS:+MAX_COMPLETION_LENGTH="$JOB_MAX_TOKENS"})
  RUN_CMD="python3 train/train_grpo.py"
  SYNC_CMD="aws s3 sync $RUN_DIR ${OUTPUT_URI%/}/"
fi

if [ "$DRY_RUN" -eq 1 ]; then
  echo "DRY RUN — job $JOB_ID on $AGENT would do:"
  for p in "${PREP_CMDS[@]+"${PREP_CMDS[@]}"}"; do echo "  $p"; done
  echo "  env ${RUN_ENV[*]} $RUN_CMD"
  echo "  $SYNC_CMD"
  echo "  aws s3 cp $LOG $LOG_URI"
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

echo "+ env ${RUN_ENV[*]} $RUN_CMD" >> "$LOG"
if ! env "${RUN_ENV[@]}" $RUN_CMD >> "$LOG" 2>&1; then
  aws s3 cp "$LOG" "$LOG_URI" >/dev/null 2>&1 || true
  finish 1 "$RUN_CMD exited non-zero"
fi

# Self-check: a zero-exit run can still produce broken output. Verify before
# declaring success — a bad file that syncs cleanly poisons downstream work.
if [ "$JOB_TYPE" = "sample" ]; then
  CHECK_MSG="$(python3 - "$OUT" "${JOB_N:-0}" <<'PYCHECK'
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
