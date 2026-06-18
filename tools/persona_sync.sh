#!/usr/bin/env bash
# persona_sync.sh — boot-time persona fetch for GPU-box agents.
# Personas are PRIVATE (they never live in this public repo): the content sits
# in s3://calibrate-rl-agent/personas/<agent>_persona.md. This script pulls the
# current copy, wires PERSONA_FILE into the bot's .env if missing, and restarts
# the bot so the persona is in its system prompt from the first turn after boot.
# No persona in the bucket -> exit 0, bot runs stock. Identity: AGENT_NAME from
# /etc/calibrate-rl-job.env (same file the job poller uses).
set -uo pipefail
AGENT="${AGENT_NAME:-$(hostname)}"
BOT_DIR="$HOME/claude-code-slack-bot"
DEST="$BOT_DIR/${AGENT}_persona.md"
SRC="s3://calibrate-rl-agent/personas/${AGENT}_persona.md"

[ -d "$BOT_DIR" ] || { echo "no bot dir on this box — nothing to do"; exit 0; }

# --- Agent permission allowlist (boot-applied) ---
# A headless on-box agent has no human to click "Allow" on a permission prompt, so
# without this it's gated out of aws/ssh/tmux + the Slack MCP. (2026-06-15 awesome-ash
# incident: training was healthy but ash couldn't manage the box or post status because
# Bash(aws|ssh) and the slack MCP tools were unapproved and no one was at the terminal.)
# Canonical, version-controlled source: tools/agent_claude_settings.json — pulled fresh
# each boot by the job poller's `git reset --hard origin/main`. Idempotent: overwrite so
# the on-box file always tracks the repo. Survives AMI re-bakes and setup_gpu_box re-runs.
SETTINGS_SRC="$(cd "$(dirname "$0")" && pwd)/agent_claude_settings.json"
if [ -f "$SETTINGS_SRC" ]; then
  mkdir -p "$HOME/.claude"
  cp "$SETTINGS_SRC" "$HOME/.claude/settings.json"
  echo "agent permission allowlist applied from $SETTINGS_SRC"
fi

# Prefer the VERSION-CONTROLLED repo persona (pulled fresh via the poller's `git reset --hard
# origin/main`) so persona edits go through PR review, not a manual S3 push. Fall back to S3 for
# any agent without a repo persona.
REPO_PERSONA="$(cd "$(dirname "$0")/.." && pwd)/personas/${AGENT}_persona.md"
if [ -f "$REPO_PERSONA" ]; then
  cp "$REPO_PERSONA" "$DEST"
  echo "persona for $AGENT from repo (version-controlled): $REPO_PERSONA"
elif ! aws s3 cp "$SRC" "$DEST.tmp" >/dev/null 2>&1; then
  echo "no persona at $SRC — bot runs stock prompt"
  exit 0
else
  mv "$DEST.tmp" "$DEST"
fi
grep -q "^PERSONA_FILE=" "$BOT_DIR/.env" 2>/dev/null || echo "PERSONA_FILE=$DEST" >> "$BOT_DIR/.env"
command -v pm2 >/dev/null 2>&1 && pm2 restart "$AGENT" --update-env >/dev/null 2>&1
echo "persona synced for $AGENT"
