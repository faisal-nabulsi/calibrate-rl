#!/usr/bin/env bash
# setup_box_env.sh — write /etc/calibrate-rl-job.env (the systemd poller's EnvironmentFile) for a
# GPU box, pulling the Slack webhook from SSM Parameter Store (central, SecureString) instead of
# hand-copying it per box. That hand-copy gap is what left awesome-ash silently MUTED: it had
# AGENT_NAME + WANDB but no SLACK_WEBHOOK_URL, so run_sample_job's slack_post() no-op'd and no
# train lifecycle posts went out (while sam/sadie, which had the webhook, reported normally).
#
# Prereqs (one-time, fleet-wide):
#   1. store the webhook:  aws ssm put-parameter --name /calibrate-rl/slack-webhook \
#                            --type SecureString --value '<hooks.slack.com/... url>'
#   2. the box IAM role allows  ssm:GetParameter + kms:Decrypt  on that parameter (michael's lane).
#
# Usage (run ON the box as ec2-user with sudo):
#   tools/setup_box_env.sh <agent_name>      # awesome-ash | sam | sadie | sage
#
# Idempotent (rewrites the file). The webhook is decrypted into a shell var and never printed; the
# W&B key (training boxes) is read from the box's own ~/.netrc and never leaves the box.
set -euo pipefail
AGENT="${1:?usage: setup_box_env.sh <agent_name>}"
PARAM="${SLACK_WEBHOOK_PARAM:-/calibrate-rl/slack-webhook}"
ENVF=/etc/calibrate-rl-job.env

WH="$(aws ssm get-parameter --name "$PARAM" --with-decryption --query Parameter.Value --output text 2>/dev/null || true)"
[ -n "$WH" ] && [ "$WH" != "None" ] || {
  echo "ERROR: could not read $PARAM from SSM Parameter Store." >&2
  echo "  create it once: aws ssm put-parameter --name $PARAM --type SecureString --value '<url>'" >&2
  echo "  and grant this box's IAM role ssm:GetParameter + kms:Decrypt on it." >&2
  exit 1; }

# W&B key from the box's netrc — training boxes have it; samplers won't (omitted then, harmless).
WK="$(awk '/api\.wandb\.ai/{f=1} f&&/password/{print $2; exit}' "$HOME/.netrc" 2>/dev/null || true)"

{
  echo "AGENT_NAME=$AGENT"
  echo "SLACK_WEBHOOK_URL=$WH"
  [ -n "$WK" ] && { echo "WANDB_API_KEY=$WK"; echo "WANDB_ENTITY=rl-intro"; }
} | sudo tee "$ENVF" >/dev/null

# The poller service runs as the invoking user (User=ec2-user), so it must be able to READ the
# file — a root-owned 0600 env file is unreadable to the service (the exact bug that needed a
# post-hoc chown on ash; systemd injects the vars but run_sample_job's own re-source fails).
sudo chown "$(id -un):$(id -gn)" "$ENVF"
sudo chmod 600 "$ENVF"
echo "wrote $ENVF: agent=$AGENT webhook=SET(len ${#WH}) wandb=${WK:+SET}"
