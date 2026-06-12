#!/usr/bin/env bash
# box_health.sh — authoritative "is this box actually doing work?" check.
#
# WHY THIS EXISTS
#   The fleet idle-monitor (on thinkrock) decided a box was idle by looking for a
#   named tmux *session*. But jobs on these boxes are launched by systemd, not tmux:
#       calibrate-job-poller.service → tools/job_poller.sh
#         → (exec) tools/run_sample_job.sh → python3 tools/sample.py | train_grpo.py
#   That whole tree is a child of the systemd unit — there is NO tmux session — so a
#   tmux-based check reports "NO active job session" for a perfectly healthy run and
#   tells a human to stop it (2026-06-12: nearly killed chain_depth1_base_diag_300,
#   exactly as it killed attempt 1 that morning). This script replaces that predicate
#   with signals that SEE service-launched jobs.
#
# USAGE
#   bash tools/box_health.sh            # human-readable; exit 0 = BUSY, 10 = IDLE
#   bash tools/box_health.sh --json     # machine-readable for the monitor
#   The remote monitor should SSH-exec this and key off the verdict / exit code
#   (busy → leave the box up) instead of checking `tmux ls`. A human or @sam can run
#   it on-box for the read-only health check, too.
#
# CONFIG (env, all optional)
#   JOB_UNIT        systemd unit that owns jobs   (default: calibrate-job-poller.service)
#   GPU_BUSY_PCT    GPU util %% that counts as busy (default: 5)
#   LOG_FRESH_SECS  job-log mtime freshness window (default: 600 = 10 min)
#   REPO            repo root holding logs/        (default: script's parent dir)
set -u

JSON=0
[ "${1:-}" = "--json" ] && JSON=1

JOB_UNIT="${JOB_UNIT:-calibrate-job-poller.service}"
GPU_BUSY_PCT="${GPU_BUSY_PCT:-5}"
LOG_FRESH_SECS="${LOG_FRESH_SECS:-600}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${REPO:-$(dirname "$SCRIPT_DIR")}"
# Keep AGENT_NAME consistent with the job runners for reporting.
[ -f /etc/calibrate-rl-job.env ] && { set -a; . /etc/calibrate-rl-job.env; set +a; }
AGENT="${AGENT_NAME:-$(hostname)}"

# --- signal 1: systemd unit active (authoritative) ----------------------------
# The poller exits 0 when no job is queued, so the unit is "active" only while a
# claimed job is running under it. active ⇒ busy; inactive ⇒ no service-run job.
UNIT_STATE="unknown"; UNIT_BUSY=0
if command -v systemctl >/dev/null 2>&1; then
  UNIT_STATE="$(systemctl is-active "$JOB_UNIT" 2>/dev/null || true)"
  [ "$UNIT_STATE" = "active" ] && UNIT_BUSY=1
fi

# --- signal 2: sampler/trainer process present (authoritative) ----------------
# Catches a job started by hand (no systemd) or one whose unit name differs.
PROC_BUSY=0; PROC_INFO=""
if PROC_INFO="$(pgrep -fa 'tools/sample\.py|train/train_grpo\.py' 2>/dev/null)"; then
  [ -n "$PROC_INFO" ] && PROC_BUSY=1
fi
PROC_INFO="$(printf '%s' "$PROC_INFO" | head -1 | cut -c1-100)"

# --- signal 3: GPU utilization (corroborating) --------------------------------
GPU_MAX="n/a"; GPU_BUSY=0
if command -v nvidia-smi >/dev/null 2>&1; then
  GPU_MAX="$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null \
            | tr -d ' ' | sort -nr | head -1)"
  [ -z "$GPU_MAX" ] && GPU_MAX="n/a"
  if [ "$GPU_MAX" != "n/a" ] && [ "$GPU_MAX" -ge "$GPU_BUSY_PCT" ] 2>/dev/null; then GPU_BUSY=1; fi
fi

# --- signal 4: freshest job log (corroborating + progress) --------------------
# logs/job_<JOB_ID>.log; sample.py prints "[done/N] ..." per problem (sample.py:128).
LOG_BUSY=0; LOG_AGE="n/a"; LOG_FILE=""; PROGRESS=""
LOG_FILE="$(ls -1t "$REPO"/logs/job_*.log 2>/dev/null | head -1)"
if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
  LOG_AGE=$(( $(date +%s) - $(stat -c %Y "$LOG_FILE" 2>/dev/null || echo 0) ))
  [ "$LOG_AGE" -le "$LOG_FRESH_SECS" ] && LOG_BUSY=1
  PROGRESS="$(grep -oE '\[[0-9]+/[0-9]+\]' "$LOG_FILE" 2>/dev/null | tail -1)"
fi

# --- verdict ------------------------------------------------------------------
# Lean BUSY: any positive signal means real work, so we never repeat the false
# "idle" that this script exists to prevent. IDLE only when every signal is quiet.
if [ "$UNIT_BUSY" = 1 ] || [ "$PROC_BUSY" = 1 ] || [ "$GPU_BUSY" = 1 ] || [ "$LOG_BUSY" = 1 ]; then
  VERDICT="BUSY"; CODE=0
else
  VERDICT="IDLE"; CODE=10
fi

if [ "$JSON" = 1 ]; then
  printf '{"agent":"%s","verdict":"%s","unit":"%s","unit_state":"%s","proc_busy":%s,"gpu_max_pct":"%s","log_file":"%s","log_age_s":"%s","progress":"%s"}\n' \
    "$AGENT" "$VERDICT" "$JOB_UNIT" "$UNIT_STATE" "$PROC_BUSY" "$GPU_MAX" "${LOG_FILE##*/}" "$LOG_AGE" "$PROGRESS"
else
  echo "box=$AGENT verdict=$VERDICT"
  echo "  unit($JOB_UNIT) : $UNIT_STATE $([ "$UNIT_BUSY" = 1 ] && echo '(busy)')"
  echo "  job process     : $([ "$PROC_BUSY" = 1 ] && echo "running — $PROC_INFO" || echo 'none')"
  echo "  gpu util max    : ${GPU_MAX}% $([ "$GPU_BUSY" = 1 ] && echo '(busy)')"
  echo "  newest job log  : ${LOG_FILE##*/} age=${LOG_AGE}s ${PROGRESS:+progress=$PROGRESS} $([ "$LOG_BUSY" = 1 ] && echo '(fresh)')"
fi
exit $CODE
