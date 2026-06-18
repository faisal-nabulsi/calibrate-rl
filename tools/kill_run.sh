#!/usr/bin/env bash
# kill_run.sh — operator: stop the depth-1 calibration run WITHOUT triggering DIAGNOSE pages.
#
# Why this exists: killing a run with a bare `pkill sample.py` makes sample.py exit non-zero,
# which run_sample_job.sh's finish() reports as FAILED + "DIAGNOSE NEEDED" — indistinguishable
# from a real crash, so the monitor pages and the bots auto-investigate an INTENTIONAL stop.
#
# What this does, in order:
#   1. set an S3 halt flag — run_sample_job's finish() reads it and posts a calm
#      ":octagonal_sign: stopped by operator" instead of a FAILED/DIAGNOSE page.
#   2. kill the campaign loop on the t3 (so it stops dispatching).
#   3. kill any sample.py on the L4 samplers — they self-stop; finish() sees the flag -> calm.
#
# The flag is CLEARED automatically by the next campaign launch, so it never suppresses a real
# failure on a later run. Usage:  tools/kill_run.sh ["reason"]
set -uo pipefail

BUCKET="${BUCKET:-calibrate-rl-agent}"
HALT="s3://$BUCKET/control/halt"
REASON="${1:-operator kill}"
T3="i-09d247668650dad2d"
SAMPLERS="i-065bb6d4bcea507db i-05c7938e1c6711370"   # sam, sadie

echo "1) setting halt flag $HALT"
printf '%s @ %s\n' "$REASON" "$(date -u +%FT%TZ)" | aws s3 cp - "$HALT"

echo "2) killing campaign loop on the t3 ($T3)"
aws ssm send-command --instance-ids "$T3" --document-name AWS-RunShellScript \
  --parameters commands='pkill -f depth1_calib_campaign.py || true' \
  --query Command.CommandId --output text || true

echo "3) killing sample.py on the L4 samplers ($SAMPLERS)"
aws ssm send-command --instance-ids $SAMPLERS --document-name AWS-RunShellScript \
  --parameters commands='pkill -f sample.py || true' \
  --query Command.CommandId --output text || true

echo
echo "done. boxes will self-stop; finish() posts a calm 'stopped by operator' (no DIAGNOSE)."
echo "the halt flag is cleared automatically on the next campaign launch."
