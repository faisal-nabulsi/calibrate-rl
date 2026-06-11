# CalibrateRL — AWS Agent Fleet Runbook

End state:
| box | type | always-on | agents | job |
|---|---|---|---|---|
| **agents-box** | t3.large (8GB) | YES | gilbert, kathryne, charizard | Slack brains: pull / analyze / PR / start-stop GPU boxes |
| **train-box** | g6e.xlarge (1× L40S) | no — on-demand | trainaws (autostart) | training; self-stops |
| **sample-box** | g6.12xlarge or 2× g6.xlarge (L4) | no — on-demand | sampleaws (autostart) | calibration sampling; self-stops |

All agents authenticate with **ANTHROPIC_API_KEY** (no personal logins).
Autonomy model: agents may start/stop the two GPU boxes and trigger training/sampling
WITHOUT a human, inside hard guardrails (§5). Merges to `main` remain human.

---

## 1. Provision the t3.large (agents-box)

Console → EC2 → Launch instance:
- Ubuntu 24.04 LTS, **t3.large**, 30GB gp3
- Security group: inbound SSH (your IP only); no other inbound (Socket Mode is outbound-only)
- Key pair: create `calibrate-agents.pem`

SSH in, base install:
```bash
sudo apt-get update && sudo apt-get install -y git curl build-essential
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y nodejs
sudo npm install -g pm2 @anthropic-ai/claude-code
type gh || (sudo mkdir -p -m 755 /etc/apt/keyrings && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && sudo apt-get update && sudo apt-get install -y gh)
```

## 2. One OS user per agent (isolation = per-agent creds, no cross-contamination)

For each of `gilbert`, `kathryne`, `charizard`:
```bash
sudo adduser --disabled-password --gecos "" gilbert
sudo su - gilbert
```
Then as that user:
```bash
# repo
git clone https://github.com/faisal-nabulsi/calibrate-rl
echo "gilbert" > calibrate-rl/.agent_identity
# bot
git clone https://github.com/faisal-nabulsi/claude-code-slack-bot
cd claude-code-slack-bot && npm install
```

`.env` per agent (THEIR Slack app tokens; shared Anthropic key or per-agent keys if you
want per-agent cost attribution — per-agent recommended):
```
SLACK_BOT_TOKEN=xoxb-<this agent's>
SLACK_APP_TOKEN=xapp-<this agent's>
SLACK_SIGNING_SECRET=<this agent's>
BASE_DIRECTORY=/home/gilbert/calibrate-rl/
ANTHROPIC_API_KEY=sk-ant-<key>
ANTHROPIC_MODEL=claude-fable-5
```
Note: with ANTHROPIC_API_KEY set, do NOT run `claude /login` — key wins, no browser needed.

Slack MCP (per user, their bot token):
```bash
claude mcp add slack -s user -e SLACK_BOT_TOKEN=xoxb-<theirs> -e SLACK_TEAM_ID=T0B8SPTK3BR -- sh -c "npx -y @modelcontextprotocol/server-slack"
```

Git auth, headless (fine-grained PAT, calibrate-rl only, Contents+PR write):
```bash
gh auth login --with-token < /home/gilbert/.gh_token   # paste token into that file first, then shred it
gh auth setup-git
```

pm2 per user:
```bash
cd ~/claude-code-slack-bot
pm2 start "npx tsx src/index.ts" --name gilbert
pm2 save
```
Root once, to resurrect all users' pm2 on reboot:
```bash
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u gilbert --hp /home/gilbert   # repeat per user
```

**Retire the laptop/Lightning copies** after the t3 versions answer in Slack:
`pm2 delete <name>` on each old machine — duplicates double-reply.

## 3. GPU boxes (train-box, sample-box)

Per Michael's GPU runbook pattern, for each box:
- AMI: Deep Learning Ubuntu (or your existing training AMI)
- **train-box:** g6e.xlarge (1× L40S 48GB) — fits 7B GRPO LoRA (~45GB)
- **sample-box:** 2× L4 (g6.12xlarge gives 4; g6.2xlarge gives 1 — pick per parallelism; 2× L4 target)
- Tag both: `Project=calibrate-rl`, `Role=train|sample`
- **Instance setting: stop on shutdown** (so in-job `poweroff` = stopped = not billed)

On each box, a dedicated agent (same bot install as §2, name `trainaws` / `sampleaws`,
its own Slack app + tokens) with pm2 startup — so the agent is reachable ~60s after
the box starts. Training/sampling scripts end with self-stop:
```bash
sudo shutdown -h now   # already in train_grpo.py pattern
```

## 4. Scoped IAM — agents can touch ONLY these two instances

IAM policy attached to the agents-box instance role (no static keys on disk):
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["ec2:StartInstances", "ec2:StopInstances", "ec2:DescribeInstances", "ec2:DescribeInstanceStatus"],
    "Resource": "arn:aws:ec2:*:<ACCOUNT_ID>:instance/*",
    "Condition": {"StringEquals": {"aws:ResourceTag/Project": "calibrate-rl"}}
  }]
}
```
Start/Stop/Describe on the tagged boxes. Nothing else — no run-instances (can't create
new boxes), no IAM, no S3 deletes. "All the permissions they need" = exactly these.

## 5. Guardrails (code, not prompts) — the price of no-human-in-the-loop

1. **Budget watchdog (non-negotiable).** Cron on agents-box every 10 min:
   any Project=calibrate-rl GPU instance running > MAX_HOURS (default 6) → force-stop
   + post `[watchdog] force-stopped <id> after 6h` to Slack. Plus an AWS Budget alert
   (e.g. $100/mo) emailing you. The watchdog stops runaways even if every agent is wrong.
2. **Concurrency lock.** Before any StartInstances: DescribeInstances — if a box with
   the same Role tag is already running, refuse and report. Max one train + one sample
   box at a time, enforced in the start script the agents call (not in their judgment).
3. **Kill criteria in the loop config** (auto-calibrator §1): max iters, plateau,
   oscillation, budget-usd cap per run — already in `automation/calibrator/config.yaml`.
4. **Self-poweroff stays the default.** Every GPU job ends in shutdown; "off" is the
   resting state.
5. **Main stays human-merged.** Autonomous runs work on `auto/<run-id>` branches and
   end with propose-pr.sh. The loop NEVER waits on the merge (next run chains off its
   local result); humans batch-merge. Spend is autonomous; the shared repo is not.

## 6. The hand-off flow (end-to-end)

1. Orchestrator (on agents-box or sample-box) needs GPU sampling → start script checks
   lock → StartInstances(sample-box) → polls until Slack shows sampleaws online.
2. Posts `@sampleaws run calib <run-id> concepts=...` → sampleaws executes, syncs
   results to S3/GCS, posts done, self-stops.
3. Loop DECIDE/APPLY happens on the always-on box. On a training decision:
   start train-box → `@trainaws run grpo <config>` → trainaws trains, checkpoints to
   S3, posts metrics, self-stops.
4. Converged → propose-pr.sh from the orchestrator's branch → Slack link → human merges
   whenever. Next run proceeds immediately.

## 7. Smoke tests (in order)

1. `@gilbert hi` from the t3 — replies, reactions cycle, no laptop duplicate replies.
2. `@gilbert open a test PR via tools/propose-pr.sh` — PAT path works headless.
3. `@gilbert start the sample box` — instance starts, sampleaws appears in Slack,
   `@gilbert stop the sample box` — stops. (Tests IAM + lock.)
4. Watchdog dry-run: start sample-box, set MAX_HOURS=0.1, confirm force-stop + Slack post.
5. One real shadow calibration: orchestrator on agents-box, SAMPLE on sample-box.
