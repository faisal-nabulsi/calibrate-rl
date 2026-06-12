#!/usr/bin/env bash
# tools/campaign_status.sh — print the latest status of an auto-calibration campaign.
#
# Usage:
#   ./tools/campaign_status.sh depth0          # latest run of campaign 'depth0'
#   ./tools/campaign_status.sh depth0 <run_id> # a specific run
#   ./tools/campaign_status.sh --list          # list campaigns/runs in the bucket
#
# Reads runs/<campaign>-<run_id>/status.json written by the orchestrator each
# iteration. Read-only; safe for any agent (including bot-to-bot turns).
#
# Config (env vars, with defaults):
#   CALIB_RUNS_URI   base URI for run state, e.g. s3://calibrate-rl-agent/runs
#                    (also accepts a local path for shadow runs, e.g. ./runs)

set -euo pipefail

RUNS_URI="${CALIB_RUNS_URI:-s3://calibrate-rl-agent/runs}"

is_s3() { [[ "$RUNS_URI" == s3://* ]]; }

list_runs() {
  if is_s3; then
    aws s3 ls "${RUNS_URI}/" | awk '{print $2}' | tr -d '/'
  else
    ls -1 "$RUNS_URI" 2>/dev/null
  fi
}

fetch_status() { # $1 = run dir name
  if is_s3; then
    aws s3 cp "${RUNS_URI}/$1/status.json" - 2>/dev/null
  else
    cat "${RUNS_URI}/$1/status.json" 2>/dev/null
  fi
}

if [[ "${1:-}" == "--list" ]]; then
  list_runs
  exit 0
fi

CAMPAIGN="${1:?usage: campaign_status.sh <campaign> [run_id] | --list}"
RUN_ID="${2:-}"

# Resolve run dir: explicit run_id, else latest (lexicographically last) for the campaign
if [[ -n "$RUN_ID" ]]; then
  RUN_DIR="${CAMPAIGN}-${RUN_ID}"
else
  RUN_DIR="$(list_runs | grep "^${CAMPAIGN}-" | sort | tail -1 || true)"
  if [[ -z "$RUN_DIR" ]]; then
    echo "No runs found for campaign '${CAMPAIGN}' under ${RUNS_URI}" >&2
    exit 1
  fi
fi

STATUS_JSON="$(fetch_status "$RUN_DIR")"
if [[ -z "$STATUS_JSON" ]]; then
  echo "No status.json in ${RUNS_URI}/${RUN_DIR} (run may not have completed iteration 1)" >&2
  exit 1
fi

# Pretty-print the fields that matter. python3 (always present) over jq (maybe not).
STATUS_JSON="$STATUS_JSON" python3 - "$RUN_DIR" << 'PYEOF'
import json, os, sys

run_dir = sys.argv[1]
s = json.loads(os.environ["STATUS_JSON"])

def g(k, d="?"): return s.get(k, d)

print(f"campaign run : {run_dir}")
print(f"state        : {g('state')}            # running | converged | escalated | halted")
print(f"iteration    : {g('iteration')}/{g('max_iters')}")
print(f"spend        : ${g('spend_usd')} / ${g('budget_usd')} budget")
print()

hist = s.get("iterations", [])
if hist:
    print("iter  goldilocks  top3   trunc  ghost  edits")
    for it in hist:
        edits = "; ".join(f"{e['concept']}.{e['param']} {e['old']}->{e['new']}"
                          for e in it.get("edits", [])) or "-"
        print(f"{it.get('iter','?'):>4}  "
              f"{it.get('goldilocks_frac','?'):>9}  "
              f"{it.get('answer_top3_share','?'):>5}  "
              f"{it.get('truncation_rate','?'):>5}  "
              f"{it.get('ghost_frac','?'):>5}  {edits}")
    print()

if g("state") == "escalated":
    print(f"ESCALATION: {g('escalation_reason')}")
if g("state") == "converged":
    print(f"PR: {g('pr_url', '(pending)')}")

per = s.get("per_concept", {})
if per:
    print("\nper-concept (latest):")
    for c, m in sorted(per.items()):
        print(f"  {c:<32} goldilocks {m.get('goldilocks_frac','?')}  "
              f"top3 {m.get('answer_top3_share','?')}  "
              f"status {m.get('status','?')}")
PYEOF
