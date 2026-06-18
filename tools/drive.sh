#!/usr/bin/env bash
# drive.sh — run core/drive.py (team Google Drive "Updates" doc) from a self-bootstrapping venv.
#
# WHY: person-sessions read/append the Updates doc via core/drive.py, which needs the google
# client libs. Modern local Pythons are externally-managed (PEP 668), so a plain `pip install`
# fails — and we don't want to --break-system-packages the system Python. This wrapper keeps the
# libs in a dedicated venv (created once, on first run) and leaves the system Python untouched.
#
# The Drive service-account key is resolved by core/drive.py from $GOOGLE_APPLICATION_CREDENTIALS
# or ~/secrets/drive-sa.json (copy it down from the agents box if you don't have it locally).
#
# Usage:
#   tools/drive.sh list                 # list team Drive files
#   tools/drive.sh read Updates         # print the Updates doc
#   tools/drive.sh append "<text>"      # append a timestamped block to Updates
#
# Override the venv location with DRIVE_VENV=/path tools/drive.sh ...
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${DRIVE_VENV:-$HOME/.cache/calibrate-drive-venv}"

if [ ! -x "$VENV/bin/python" ]; then
  echo "drive.sh: creating venv at $VENV (one-time, installs google client libs)…" >&2
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
  "$VENV/bin/pip" install --quiet google-api-python-client google-auth
fi

cd "$REPO"
exec "$VENV/bin/python" -m core.drive "$@"
