#!/usr/bin/env bash
# job_poller.sh — boot-time check for a handed-off job. The GPU boxes are pure
# workers: an orchestrator drops a spec at s3://calibrate-rl-agent/pending/<agent>/
# (prefixes: pending/sam/, pending/sadie/, pending/awesome-ash/) and starts the
# box; this poller (run on boot by tools/calibrate-job-poller.service) claims the
# oldest spec and hands it to tools/run_sample_job.sh, which runs it, syncs the
# output, and powers the box back off.
#
# Identity: AGENT_NAME from /etc/calibrate-rl-job.env (systemd EnvironmentFile),
# falling back to the hostname. No pending spec -> exit 0 and leave the box up
# (someone started it by hand for interactive work).
set -uo pipefail
cd "$(dirname "$0")/.."
# Always run the latest merged tooling — boxes boot rarely and would go stale.
git pull -q origin main 2>/dev/null || true

# AGENT_NAME (+ webhook/escalate vars) is injected by systemd's EnvironmentFile. Source it
# for hand-runs too, so `bash tools/job_poller.sh` resolves the right S3 prefix instead of
# silently falling back to the hostname and polling pending/<host>/ — there the queued spec
# looks unclaimed and the box appears idle (the silent-handoff detour, 2026-06-12).
[ -f /etc/calibrate-rl-job.env ] && { set -a; . /etc/calibrate-rl-job.env; set +a; }

AGENT="${AGENT_NAME:-$(hostname)}"
BUCKET="${JOB_BUCKET:-s3://calibrate-rl-agent}"
PENDING="$BUCKET/pending/$AGENT"

SPEC_KEY="$(aws s3 ls "$PENDING/" 2>/dev/null | awk '$NF ~ /\.json$/ {print $NF}' | sort | head -1)"
if [ -z "$SPEC_KEY" ]; then
  echo "no pending job for $AGENT — leaving the box up"
  exit 0
fi

# Claim by moving the spec out of pending/ so a reboot can't double-run it.
CLAIMED="$BUCKET/running/$AGENT/$SPEC_KEY"
if ! aws s3 mv "$PENDING/$SPEC_KEY" "$CLAIMED"; then
  echo "ERROR: failed to claim $PENDING/$SPEC_KEY" >&2
  exit 1
fi

echo "claimed $CLAIMED — handing to run_sample_job.sh"
exec bash tools/run_sample_job.sh "$CLAIMED"
