#!/usr/bin/env bash
# propose-pr.sh — Agent-safe way to land code: branch + commit + push + open a PR.
# NEVER pushes to main. A human merges the PR on GitHub; that click is the gate.
#
# Usage (run from repo root):
#   ./tools/propose-pr.sh "short description of the change"
#
# Requires: gh (GitHub CLI) authed, and branch protection on main (human approval).
# Intended to be invoked by an agent only on a HUMAN-INITIATED turn (a person asked
# for a PR). Agents must never push directly to main.

set -euo pipefail

DESC="${1:-}"
if [ -z "$DESC" ]; then
  echo "ERROR: give a short description, e.g. ./tools/propose-pr.sh \"fix grader regex\"" >&2
  exit 1
fi

# Identify the agent (for the branch name) from .agent_identity if present.
TAG="agent"
if [ -f .agent_identity ]; then
  TAG="$(tr -d '[:space:]' < .agent_identity)"
fi

# Refuse to run on main with nothing staged/changed.
if git diff --quiet && git diff --cached --quiet; then
  echo "ERROR: no changes to propose. Make your edits first." >&2
  exit 1
fi

# Never operate directly on main: create a fresh branch.
STAMP="$(date +%Y%m%d-%H%M%S)"
BRANCH="agent/${TAG}-${STAMP}"
git checkout -b "$BRANCH"

# Stage everything currently changed and commit.
git add -A
git commit -m "${DESC} [proposed by ${TAG}]"

# Push the BRANCH (not main).
git push -u origin "$BRANCH"

# Open a PR into main. --fill uses the commit message; body notes the proposer.
gh pr create \
  --base main \
  --head "$BRANCH" \
  --title "${DESC}" \
  --body "Proposed by agent \`${TAG}\` via propose-pr. A human must review and merge — this branch does not touch main on its own."

echo ""
echo "PR opened from ${BRANCH}. A human reviews and merges on GitHub."
echo "Return to main locally with: git checkout main"
