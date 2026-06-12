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
if ! aws s3 cp "$SRC" "$DEST.tmp" >/dev/null 2>&1; then
  echo "no persona at $SRC — bot runs stock prompt"
  exit 0
fi
mv "$DEST.tmp" "$DEST"
grep -q "^PERSONA_FILE=" "$BOT_DIR/.env" 2>/dev/null || echo "PERSONA_FILE=$DEST" >> "$BOT_DIR/.env"
command -v pm2 >/dev/null 2>&1 && pm2 restart "$AGENT" --update-env >/dev/null 2>&1
echo "persona synced for $AGENT"
