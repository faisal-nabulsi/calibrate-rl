#!/bin/bash
# gpu_job_monitor.sh — continuous fleet idle/liveness monitor (the [thinkrock-monitor]).
# Runs as the `autocalib` cron on the always-on agents-box, every 10 min.
#
# For each RUNNING Project=calibrate-rl GPU box it SSHes in (user/key configurable via
# MONITOR_SSH_USER / MONITOR_SSH_KEY; defaults ec2-user + ~/.ssh/parena-key.pem) and asks
# tools/box_health.sh whether the box is actually working. It only ever *pages*; it never
# stops a box itself — the 8h watchdog under `agent` is the hard backstop.
#
# Note: the loop only iterates instances AWS reports as RUNNING, so an SSH failure here is
# never "the box is down" — it's "running box we couldn't reach" (almost always a fresh box
# whose authorized_keys lacks the monitor key). That case is paged distinctly and NEVER as
# a stop suggestion.
#
# Liveness source of truth = box_health.sh (systemd/GPU/proc/log aware), NOT a raw
# `tmux ls` guess. Exit-code contract: 0 = BUSY (leave it alone), 10 = IDLE (page
# "stop it"). Anything else — SSH failure, missing checkout, unexpected status — is
# treated as "could not verify" and pages a human to LOOK, never to blind-stop a
# box that might be busy.
#
# This file is the source of truth in the repo (tools/). Deploy a copy to the box's
# autocalib cron; it previously existed ONLY on the box (untracked).
source ~/.profile
now=$(date +%s)
mkdir -p ~/.monitor_state

# SSH identity for reaching the GPU boxes. Use an explicit key so the check does not
# silently depend on the agents-box default identity / ssh-agent (the rc=255 false-page
# root cause). If the key file is absent we fall back to the default identity rather than
# hard-failing, so a misconfigured key never *suppresses* a real health check.
SSH_USER="${MONITOR_SSH_USER:-ec2-user}"
SSH_KEY="${MONITOR_SSH_KEY:-$HOME/.ssh/parena-key.pem}"
SSH_OPTS=(-o ConnectTimeout=8 -o BatchMode=yes -o StrictHostKeyChecking=accept-new)
[ -f "$SSH_KEY" ] && SSH_OPTS+=(-i "$SSH_KEY")

# Paged on every monitor alert: owner + on-call + chaining agent (deduped literal).
MENTIONS="<@U0B9661M6J2> <@U0B9C6JP2MC> <@U0B9C278VPW>"   # faisal, michael, gilbert

alert() { # alert <key> <msg> — webhook page, rate-limited 2h per key
  local f=~/.monitor_state/$1 last=0
  [ -f "$f" ] && last=$(cat "$f")
  [ $((now - last)) -lt 7200 ] && return
  echo "$now" > "$f"
  curl -s -X POST -H 'Content-type: application/json' \
    --data "{\"text\":$(python3 -c 'import json,sys;print(json.dumps(sys.argv[1]))' "$2")}" \
    "$SLACK_WEBHOOK_URL" >/dev/null
}

# Scope to the GPU boxes by Role (train/sample), NOT Project — the always-on
# agents-box is tagged Project=calibrate-rl but has no Role tag, so a Project filter
# would wrongly target it (and our fail-safe would then page about the prod box every
# 2h). This mirrors the watchdog's Role=train|sample scoping.
aws ec2 describe-instances \
  --filters Name=tag:Role,Values=train,sample Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[].[InstanceId,PublicIpAddress,LaunchTime]' --output text |
while read -r id ip launch; do
  [ "$ip" = "None" ] && continue
  up_min=$(( (now - $(date -d "$launch" +%s)) / 60 ))
  [ $up_min -lt 20 ] && continue   # grace period after start

  # Ask box_health.sh over the configured SSH path. The remote prints
  # "<verdict_exit> <fresh_log_count>". A missing checkout exits 99 (distinct from a
  # busy/idle verdict); ssh itself exits 255 on connect/auth failure.
  out=$(ssh "${SSH_OPTS[@]}" "$SSH_USER@$ip" '
    cd ~/calibrate-rl 2>/dev/null || exit 99
    bash tools/box_health.sh >/dev/null 2>&1; v=$?
    f=$(find ~/job_state ~/calibrate-rl/logs -name "*.log" -mmin -15 2>/dev/null | wc -l)
    echo "$v $f"' 2>/dev/null)
  sshrc=$?

  # Fail SAFE: any failure to obtain a clean verdict pages for a human look — never
  # a stop suggestion. Split the two cases: a pure SSH connect/auth failure (255) on a
  # box AWS reports RUNNING is almost always a fresh-box key gap, not a sick box — page
  # it distinctly and non-urgently with the actual remediation, so it stops reading as
  # "the box might be dead."
  if [ $sshrc -ne 0 ] || [ -z "$out" ]; then
    if [ $sshrc -eq 255 ]; then
      alert "${id}-ssh-unreachable" "[thinkrock-monitor] $id ($ip) is RUNNING ${up_min}min but the monitor can't SSH in (rc=255) — health check skipped, NOT a down box. Likely the monitor key isn't in this box's authorized_keys (fresh box) or MONITOR_SSH_KEY is unset/wrong. Do NOT stop; fix authorized_keys / MONITOR_SSH_KEY. $MENTIONS"
    else
      alert "${id}-unverifiable" "[thinkrock-monitor] could not verify liveness on $id ($ip) — connected but health check failed (rc=$sshrc; e.g. missing checkout). Manual look needed; do NOT blind-stop, the box may be busy. $MENTIONS"
    fi
    continue
  fi

  verdict=$(echo "$out" | awk '{print $1}')
  fresh=$(echo "$out" | awk '{print $2}')
  case "$verdict" in
    10)  # IDLE — box_health says no active job + GPU idle
      alert "${id}-idle" "[thinkrock-monitor] $id ($ip) has been RUNNING ${up_min}min and box_health reports IDLE (no active job, GPU idle). If nobody is using it, stop it. $MENTIONS" ;;
    0)   # BUSY — leave it; only flag the hang case (running but no log progress)
      if [ "${fresh:-0}" = "0" ]; then
        alert "${id}-stale" "[thinkrock-monitor] $id ($ip) box_health=BUSY but its log hasn't moved in 15+ min — possible hang. DIAGNOSE NEEDED $MENTIONS"
      fi ;;
    *)   # unexpected status (missing box_health → 127, cd → 99, etc.) — don't trust it
      alert "${id}-unverifiable" "[thinkrock-monitor] could not verify liveness on $id ($ip) — box_health returned unexpected status '$verdict'. Manual check needed; do NOT blind-stop. $MENTIONS" ;;
  esac
done

# Unclaimed-handoff check: a spec in pending/<agent>/ while that agent's box is
# RUNNING (>10 min) means the boot poller never claimed it — the silent failure
# mode of 2026-06-12. Page a human; do NOT suggest stopping (a job is queued!).
declare -A AGENT_BOX=( [sam]=i-065bb6d4bcea507db [sadie]=i-05c7938e1c6711370 [awesome-ash]=i-07455ba55e473769d )
for a in sam sadie awesome-ash; do
  spec=$(aws s3 ls "s3://calibrate-rl-agent/pending/$a/" 2>/dev/null | awk '$NF ~ /\.json$/ {print $NF}' | head -1)
  [ -z "$spec" ] && continue
  read -r bst blaunch <<< "$(aws ec2 describe-instances --instance-ids ${AGENT_BOX[$a]} --query 'Reservations[0].Instances[0].[State.Name,LaunchTime]' --output text 2>/dev/null)"
  [ "$bst" = "running" ] || continue
  bup=$(( (now - $(date -d "$blaunch" +%s 2>/dev/null || echo $now)) / 60 ))
  [ $bup -lt 10 ] && continue
  alert "${AGENT_BOX[$a]}-unclaimed" "[thinkrock-monitor] HANDOFF FAILED: $a's box is RUNNING ${bup}min but spec '$spec' is still UNCLAIMED in pending/$a/ — boot poller didn't fire. Do NOT stop the box; the queued job needs to start. DIAGNOSE NEEDED $MENTIONS"
done
