# L4 sampling fleet — raise to 3 GPUs + direct access (for Michael)

> Owner: Michael (infra/account lane). Context: the depth-1 calibration campaign +
> the depth-0 evals run across the L4 samplers (sam/sadie/sage). Two account-level
> gaps are slowing us down. Neither requires touching application code; both are
> AWS-console/account actions only you can do.

## TL;DR
1. **Raise the GPU quota so we can run 3 L4s at once** (today we cap at 2, which forces
   awkward L40S-offloading for any 3rd job). ← the high-value one.
2. **Fix the bot agent permissions** (§3 below) — the agents (gilbert/sam/…) keep hitting
   "no shell," "aws requires approval," "can't read thread replies." Mostly `claude-code-slack-bot`.
3. **(Recommended) Give the L4s direct SSM access** so they're debuggable. They're
   currently queue-only, and an all-day failure cascade (numpy → venv-activation →
   bitsandbytes) was painful precisely because nobody could shell in.

You do **not** need to provision sage's bitsandbytes fix — that's a queue `setup` job
(no box access). See the last section.

---

## Status — actioned by Michael (2026-06-16)

These no longer need Michael; they're done or self-serviceable by Faisal going forward:

- **§1 quota → 20:** request **open with AWS** (`L-DB2E81BA`, us-east-1, `CASE_OPENED`).
  Awaiting AWS approval; nothing more to file (one open request allowed per quota).
- **§2 allowlist:** **merged (#88)** — `tools/agent_claude_settings.json` grants bare `Bash`
  (all commands incl. compound `a && b`) + the full Slack MCP incl. `slack_get_thread_replies`.
  Boxes pick it up on their next boot/job cycle (`persona_sync`); no force-reboot of a busy box.
  Person-sessions now also inherit it via a checked-in **`.claude/settings.json`** (this change).
  *(Still bot-repo, not this repo: spawned-subagent `Bash`/MCP inheritance — `claude-code-slack-bot`.)*
- **§3 SSM on the L4s:** **`AmazonSSMManagedInstanceCore` attached to the `calibrate-rl-gpu-box`
  role.** All three L4s use that profile, so sam/sadie register within minutes (no reboot needed)
  and sage registers on next start. Then `aws ssm start-session --target <L4>` works directly.

**Faisal can do all of the above himself from now on:** the `faisal` IAM user has
`AdministratorAccess` (EC2/IAM/SSM/service-quotas/S3 all covered), and his Claude Code
person-session auto-approves Bash + the Slack MCP via the repo `.claude/settings.json`. So
quota bumps, instance-profile attaches, reboots, and SSM are self-serve — no Michael bottleneck.

---

## 1. Raise the G-family quota to fit 3 L4s + the L40S
**Symptom:** starting a 3rd L4 fails the account limit (we observed "max 2 L4s"), and
even within that we hit transient `InsufficientInstanceCapacity` on start.

**The quota:** L4 boxes are `g6.xlarge` (4 vCPU each); the L40S is `g6e.xlarge` (4 vCPU).
Both count against the single Service Quota **"Running On-Demand G and VT instances"**
(measured in **vCPUs**, region `us-east-1`).
- 3× L4 = 12 vCPU, plus L40S = 16 vCPU. Current cap appears to be ~8–12.
- **Request: raise "Running On-Demand G and VT instances" to ≥ 20 vCPU** (headroom for
  3 L4s + the L40S + a little slack).

**How:** AWS Console → Service Quotas → Amazon EC2 → "Running On-Demand G and VT
instances" → Request increase → 20 (us-east-1). (Or `aws service-quotas
request-service-quota-increase --service-code ec2 --quota-code L-DB2E81BA --desired-value 20`.)

**Separately, `InsufficientInstanceCapacity`** is AWS *hardware* availability in the AZ,
not the quota — it's transient (our start loop retries through it). If it's chronic, an
**On-Demand Capacity Reservation** for 1–2 `g6.xlarge` in our AZ would guarantee starts.
Optional; the retry loop has been sufficient.

**Payoff:** with 3 L4 slots, the campaign + composition-gap diagnostic + by-framing eval
all run on L4s in parallel — no more offloading the 3rd job to the L40S.

## 2. Fix the bot agent permissions (`claude-code-slack-bot` + deploy)
All day, the agents (gilbert/sam/…) hit permission walls that stopped them diagnosing or
executing: *"no standalone Bash tool, only Monitor," "aws requires approval," "journalctl/pm2
blocked," "can't read thread replies," "agents-box mirror outside my sandbox," "compound
commands need approval."* The in-repo allowlist (`tools/agent_claude_settings.json`) is being
widened to grant everything (Bash + the full slack MCP) — Faisal's PR — but that only helps
**main** agents, and only after the boxes reboot to pick up the new `~/.claude/settings.json`.
The rest is in the bot repo / deploy and needs you:

- **Spawned subagents have no Bash tool + restricted MCP.** When an agent spawns a subagent to
  diagnose, that subagent runs with only `Monitor` (no `Bash`) and can't hit aws/S3/threads —
  which is why gilbert "couldn't read the log this session" repeatedly. Give spawned subagents
  the `Bash` tool + the slack MCP and have them **inherit the permission allowlist**.
- **Agents can't read Slack thread replies** (`slack_get_thread_replies` → permission-denied)
  even though it's in the allowlist — so they can't follow threads and resort to top-level
  reposts (the gilbert/sam coordination thrash). Fix the bot's MCP permission for thread reads.
- **Compound commands prompt** (`a && b`) even when each part is allowed — that's a Claude Code
  default. Either instruct agents (bot system prompt) to run **single** commands, or set the
  bot's permission mode to auto-approve its allowlisted tools.
- **Reboot the L4s** so they pick up the current `agent_claude_settings.json` (persona_sync
  drops it on boot; boxes that booted before it have a stale settings.json). Boxes that cycle
  through jobs will refresh naturally, but a manual reboot guarantees it.
- **Leave instance start/stop gated** — that's the intentional §2 guard (agents never auto
  start/stop boxes). Not a bug; do not "fix" it.

## 3. (Recommended) Direct SSM access to the L4s
**Symptom:** `aws ssm start-session --target <L4>` → `TargetNotConnected`;
`aws ssm describe-instance-information` lists only the t3. The L4s have **no registered
SSM agent**, are in a different VPC (172.31) from the t3 (10.0.0), and are SG-locked
(SSH from the t3 times out even with the egress IP authorized). So they're reachable
**only** via the outbound S3 job queue — which is why today's env failures (numpy,
bitsandbytes) each cost a full re-provision cycle instead of a 30-second shell fix.

**Fix:** attach an IAM **instance profile** with the `AmazonSSMManagedInstanceCore`
managed policy to each L4 (sam `i-065bb6d4bcea507db`, sadie `i-05c7938e1c6711370`,
sage `i-0161b1d0bc48ede12`), then reboot so the SSM agent registers — same setup the t3
already has. After that, `aws ssm start-session --target <L4>` works directly.
(If you'd rather not use SSM: open SSH to the L4 SG from the t3's egress IP + confirm
the route — but SSM is cleaner and matches the t3.)

**Payoff:** future on-box debugging is a shell, not a queue round-trip.

---

## Not your action: sage's bitsandbytes fix (queue-dispatchable)
sage still has bitsandbytes, which breaks `from peft import PeftModel` (its bnb tuner
JIT-compiles triton via gcc and fails on the L4s). The fix is **#86's `provision_box.sh`**,
which `pip uninstall -y bitsandbytes` — dispatched as a `setup` job over the queue, **no
box access**. Already done on sadie (`Successfully uninstalled bitsandbytes-0.49.2 …
PeftModel import clean`). For sage:
```bash
echo '{"type":"setup","output_uri":"s3://calibrate-rl-agent/runs/setup_sage/done.json"}' > /tmp/s.json
aws s3 cp /tmp/s.json s3://calibrate-rl-agent/pending/sage/setup_sage.json
aws ec2 start-instances --instance-ids i-0161b1d0bc48ede12   # retry if InsufficientInstanceCapacity
# verify: aws s3 cp s3://calibrate-rl-agent/runs/setup_sage/done.json.log - | tail -3  -> "PeftModel import clean"
```
(Anyone can run this; listed here only so the full fleet picture is in one place.)
