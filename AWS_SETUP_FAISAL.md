# CalibrateRL — AWS GPU Box: Setup Runbook + Operating Guide

> Written 2026-06-11. Lives in the outer folder (not the repo — no-new-md rule).
> The box was set up and smoke-tested end-to-end on 2026-06-10/11: calibration
> sampling, TRL GRPO config, and vLLM serving all verified working on the L40S.
>
> **PART A = the 10-minute in-person setup, in exact chronological order, with
> the owner of each step.** PART B = day-to-day reference once set up.

## What exists (context for both of you)

| Thing | Value |
|---|---|
| AWS account | `163285046002` (us-east-1) |
| GPU instance | `i-07455ba55e473769d` — **g6e.xlarge = 1× NVIDIA L40S 48GB**, 4 vCPU, 32GB RAM |
| Name tag | `parena-prod-gpu` (legacy name; it's now the CalibrateRL training box) |
| Public IP | `34.226.11.242` (elastic IP — survives stop/start) |
| Login | `ec2-user` (Amazon Linux 2023) |
| Cost | **~$1.86/hr while running. STOP IT WHEN DONE.** $0 compute while stopped. |
| Identity | `~/calibrate-rl/.agent_identity` = `train@aws` — same role as `train@lightning`: **executes runs, never designs them** |

**⚠️ DO NOT TOUCH anything else in this AWS account.** The API box
(`parena-prod-api`, `3.212.201.9`), the RDS Postgres, the load balancer, and the
S3 bucket `parena-prod-datasets-163285046002` all serve Michael's live site
**prismhealth.tech**. The GPU box is the only CalibrateRL resource.

---

# PART A — The 10-minute setup (do in this order)

## Step 0 — MICHAEL — start the box FIRST (it queues; do this before anything else)

The start often hits `InsufficientInstanceCapacity` (normal — AWS is out of spare
g6e in this zone; took 17 retries / ~25 min on 2026-06-11). Kick off the retry
loop, then do Steps 1–3 while it queues:

```bash
while ! aws ec2 start-instances --instance-ids i-07455ba55e473769d 2>/dev/null; do
  echo "no capacity, retrying in 90s…"; sleep 90
done && aws ec2 wait instance-running --instance-ids i-07455ba55e473769d && echo UP
```

## Step 1 — MICHAEL — hand Faisal his AWS credentials  ✅ keys already created

The IAM user `faisal` already exists (created 2026-06-11), scoped to
start/stop/describe **only this instance** — he cannot touch the Parena infra.
Michael has the `AccessKeyId` + `SecretAccessKey` — hand them over in person /
DM / 1Password. **Never paste them in a channel or commit them.**

(If the keys are ever lost or leaked, Michael rotates:
`aws iam create-access-key --user-name faisal` then
`aws iam delete-access-key --user-name faisal --access-key-id <old>`.)

## Step 2 — FAISAL — configure AWS CLI on your laptop (2 min)

```bash
# install if needed:  brew install awscli
aws configure
#   AWS Access Key ID:     <from Michael, Step 1>
#   AWS Secret Access Key: <from Michael, Step 1>
#   Default region name:   us-east-1
#   Default output format: json

# verify (should print the instance state, e.g. "running" or "pending"):
aws ec2 describe-instances --instance-ids i-07455ba55e473769d \
  --query 'Reservations[0].Instances[0].State.Name' --output text
```

## Step 3 — FAISAL — generate an SSH key and give Michael the public half (1 min)

```bash
# skip keygen if ~/.ssh/id_ed25519.pub already exists
ssh-keygen -t ed25519 -C "faisal"
cat ~/.ssh/id_ed25519.pub        # send THIS LINE to Michael (public key — safe to share)
```

While you're here, add to `~/.ssh/config` so `ssh gpu` works later:

```
Host gpu
    HostName 34.226.11.242
    User ec2-user
    IdentityFile ~/.ssh/id_ed25519
```

## Step 4 — wait for the box (Step 0 loop prints `UP`), then give it ~30s for sshd

## Step 5 — MICHAEL — install Faisal's key AND the agent's key on the box (30 sec)

Two keys to add: Faisal's (from Step 3) and the Slack agent's (already generated
on the API box — exact line below, it's a public key, safe to be in this doc):

```bash
ssh -i ~/.ssh/parena-key.pem ec2-user@34.226.11.242 \
  'echo "PASTE_FAISALS_PUBKEY_LINE_HERE" >> ~/.ssh/authorized_keys && \
   echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF8AG4OaaBcq1nrzkMx7spFWVqfZ73+H2I7/QIEJRmR8 agent@parena-api" >> ~/.ssh/authorized_keys'
```

## Step 6 — FAISAL — test your access (30 sec)

```bash
ssh gpu          # should land in /home/ec2-user with no password
nvidia-smi       # should show NVIDIA L40S, 46068 MiB
exit
```

## Step 7 — MICHAEL — one-time logins on the box (3 min)

```bash
ssh -i ~/.ssh/parena-key.pem ec2-user@34.226.11.242

claude           # then type /login and finish in the browser (uses Michael's Max plan)
claude -p "say hello"        # verify it answers, then Ctrl-C out

echo 'export WANDB_API_KEY=<key from wandb.ai/authorize>' >> ~/.bashrc
source ~/.bashrc
```

## Step 8 — BOTH — 60-second smoke check (optional but satisfying)

```bash
ssh gpu
source ~/rl-venv/bin/activate && cd ~/calibrate-rl && git pull
N_PROBLEMS=1 OUT=/tmp/smoke.json bash tools/sample.sh && sleep 90 && tail -3 sample.log
# expect a graded zone line like: [1/1] n/8 <zone> | <concept> | ~19s
```

## Step 9 — whoever finishes last — STOP THE BOX (unless training now)

```bash
aws ec2 stop-instances --instance-ids i-07455ba55e473769d
```

**End state:** both of you can start/stop the box and SSH in; Claude Code + W&B
are logged in on the box; training is one command away (see Part B §2).

---

# PART C — The Slack agent (do right after Part A; ~15 min, mostly Slack clicking)

**Goal:** a bot in #calibrate-rl-agents that BOTH of you can @mention anytime.
On request it pulls code, **starts the GPU box (riding out the capacity queue),
launches training on the L40S in tmux, posts lifecycle updates, and the run
auto-poweroffs the box when done.** The @mention is the human trigger, so the
"humans launch GPU runs" rule stays intact.

**Where it lives & what's ALREADY DONE (2026-06-11):** on the always-on API box
(`3.212.201.9`) under a dedicated **non-sudo user `agent`** — sandboxed away from
the prismhealth.tech processes. Already in place under `/home/agent/`:
- `claude-code-slack-bot/` (clone of the team fork) and `calibrate-rl/` with
  `.agent_identity` = `trainaws`
- Claude Code 2.1.173 installed; Node 20 + tmux on the box
- SSH keypair generated (pubkey goes onto the GPU box in Part A Step 5)

**Security model (why this is OK on the prod box):** the bot runs tools WITHOUT
asking (bypassPermissions) — but as `agent` it has no sudo, can't touch the site
processes, can only SSH to the GPU box, and its AWS credentials (Step C2) can
only start/stop that one instance. Keep it strictly in the private channel; any
@mention is a command it will execute.

## Step C1 — MICHAEL — create the Slack app "trainaws" (browser, ~7 min)

At **api.slack.com/apps → Create New App → From scratch**, name `trainaws`,
workspace = the CalibrateRL one. Then (same as AGENT_SETUP.md, condensed):

1. **OAuth & Permissions → Bot Token Scopes**, add: `app_mentions:read`,
   `channels:read`, `channels:history`, `groups:read`, `groups:history`,
   `chat:write`, `users:read`, `im:read`, `im:history`, `im:write`,
   `reactions:write` → **Install to Workspace** → copy the **`xoxb-` token**.
2. **Basic Information → App-Level Tokens → Generate**, scope
   `connections:write` → copy the **`xapp-` token**.
3. **Socket Mode → Enable.**
4. **Event Subscriptions → Enable** → bot events: `app_mention`,
   `message.channels`, `message.im`, `member_joined_channel`.
5. **Basic Information → App Credentials** → copy the **Signing Secret**.
6. In #calibrate-rl-agents: `/invite @trainaws`.

## Step C2 — MICHAEL — give the agent its AWS credentials (1 min, your laptop)

```bash
aws iam create-user --user-name slack-agent
aws iam put-user-policy --user-name slack-agent --policy-name gpu-box-start-stop --policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {"Sid": "StartStopGpuBox", "Effect": "Allow",
     "Action": ["ec2:StartInstances", "ec2:StopInstances"],
     "Resource": "arn:aws:ec2:us-east-1:163285046002:instance/i-07455ba55e473769d"},
    {"Sid": "ReadOnly", "Effect": "Allow",
     "Action": ["ec2:DescribeInstances", "ec2:DescribeInstanceStatus"],
     "Resource": "*"}
  ]}'
aws iam create-access-key --user-name slack-agent   # note the two values for C3
```

## Step C3 — MICHAEL — finish the install on the API box (5 min, paste-able)

```bash
ssh -i ~/.ssh/parena-key.pem ec2-user@3.212.201.9
sudo su - agent
```

Then as `agent`:

```bash
# 1. build the bot
cd ~/claude-code-slack-bot && npm install && npm run build

# 2. its config — paste the three Slack values from C1:
cat > .env <<'EOF'
SLACK_BOT_TOKEN=xoxb-PASTE
SLACK_APP_TOKEN=xapp-PASTE
SLACK_SIGNING_SECRET=PASTE
BASE_DIRECTORY=/home/agent/
EOF

# 3. AWS credentials from C2:
mkdir -p ~/.aws && cat > ~/.aws/credentials <<'EOF'
[default]
aws_access_key_id = PASTE_FROM_C2
aws_secret_access_key = PASTE_FROM_C2
EOF
printf '[default]\nregion = us-east-1\noutput = json\n' > ~/.aws/config
# AWS CLI for the agent (user-local, no sudo needed):
pip3 install --user awscli 2>/dev/null || sudo dnf install -y awscli  # (dnf needs ec2-user)
aws ec2 describe-instance-status --instance-ids i-07455ba55e473769d   # verify

# 4. log Claude Code in (browser handoff — uses whoever's subscription you log in)
claude          # type /login, finish in browser, then: claude -p "say hello"

# 5. helper script the bot uses to launch training end-to-end:
cat > ~/gpu_train.sh <<'EOF'
#!/usr/bin/env bash
# Start GPU box (rides capacity queue), pull repo, launch training in tmux.
# Usage: ~/gpu_train.sh "MAX_COMPLETION_LENGTH=2048 MAX_STEPS=250"
set -u
ID=i-07455ba55e473769d; IP=34.226.11.242; OVERRIDES="${1:-MAX_COMPLETION_LENGTH=2048}"
echo "starting instance (capacity queue may take ~25 min)…"
until aws ec2 start-instances --instance-ids $ID >/dev/null 2>&1; do sleep 90; done
aws ec2 wait instance-running --instance-ids $ID && sleep 40
ssh -o StrictHostKeyChecking=accept-new ec2-user@$IP \
  "cd ~/calibrate-rl && git pull -q && tmux new -d -s train \
   \"source ~/rl-venv/bin/activate && cd ~/calibrate-rl && env $OVERRIDES python3 train/train_grpo.py 2>&1 | tee train_run.log\""
echo "LAUNCHED — monitor: ssh ec2-user@$IP tail -f calibrate-rl/train_run.log"
echo "(box powers itself off when the run finishes)"
EOF
chmod +x ~/gpu_train.sh

# 6. run the bot forever under pm2:
npm install -g pm2 --prefix ~/.local
~/.local/bin/pm2 start npm --name trainaws -- start
~/.local/bin/pm2 save
~/.local/bin/pm2 startup   # prints one sudo command — run it from ec2-user
```

## Step C4 — BOTH — test in #calibrate-rl-agents (2 min)

1. `@trainaws cwd calibrate-rl` → replies with working dir set.
2. `@trainaws hi, who are you?` → answers (tag `[trainaws]` per CLAUDE.md).
3. `@trainaws what's the GPU box status?` → it runs the describe call.
4. Plain message with no @mention → silence (the bot-loop patch working).
5. The real thing, when you actually mean it:
   `@trainaws pull latest and start the abl3 training run` → it uses
   `~/gpu_train.sh`, posts `launched`, and the box powers off when done.

**What the agent can do unattended:** read/post Slack, git pull, prep
configs/data, start/stop the GPU box, launch/monitor runs **when a human asks**,
report results. **What stays human:** deciding WHAT to train (it executes
handed-off configs — `train@lightning` rules), merging PRs, go/kill calls.

---

# PART B — Day-to-day reference

## 1. Daily loop: start → work → STOP

```bash
# start (capacity retry — see Step 0; queueing is normal, not a setup error)
while ! aws ec2 start-instances --instance-ids i-07455ba55e473769d 2>/dev/null; do sleep 90; done
aws ec2 wait instance-running --instance-ids i-07455ba55e473769d

ssh gpu
tmux new -s train                          # ALWAYS tmux for long jobs (survives disconnects)
source ~/rl-venv/bin/activate
cd ~/calibrate-rl && git pull

# ... work (see §2-3) ...

# STOP WHEN DONE — $45/day if forgotten
aws ec2 stop-instances --instance-ids i-07455ba55e473769d
```

Notes:
- `train/train_grpo.py` ends with `sudo poweroff` — after a training run the box
  stops itself (billing stops). Intentional; leave it in.
- Same IP every restart (elastic). Disk persists across stop/start.
- Stopped box costs only its 800GB volume (~$64/mo, already budgeted).

## 2. What's on the box + running jobs

```
~/calibrate-rl       repo clone, .agent_identity = train@aws
~/rl-venv            TRAINING venv: torch 2.6 cu124, trl 1.5.1, peft, transformers 5.11, wandb
~/vllm-venv          SERVING venv: vLLM 0.22.1 (separate — its pins fight TRL's)
~/serve_vllm.sh      one-command vLLM server in tmux (§3)
~/setup_gpu_box.sh   the script that built all this (rerunnable)
~/Parena             Michael's old project — LEAVE IT ALONE (has uncommitted work)
Qwen2.5-7B-Instruct  pre-downloaded in ~/.cache/huggingface
```

**Calibration sampling** (HF generate — the calibration-consistent path; never
swap in vLLM/an API for zone-selection):

```bash
bash tools/sample.sh        # defaults: 500×8 @2048, temp 1.0, resumable
N_PROBLEMS=600 DATASET=data/abl3_pool_v1.json OUT=data/calib_abl3_2048.json bash tools/sample.sh
tail -f sample.log          # observed: ~19s/problem on the L40S
```

**Training** (GRPO + LoRA, 7B — humans pull the trigger per team rules; post
`launched / step N / done / failed` to #calibrate-rl-agents):

```bash
tmux new -s train
source ~/rl-venv/bin/activate && cd ~/calibrate-rl
MAX_COMPLETION_LENGTH=2048 python3 train/train_grpo.py
# resume: RESUME_OUTPUT_DIR=./checkpoint/run_<ts> python3 train/train_grpo.py
```

L40S = 48GB (vs A100-80GB on Lightning): default `PER_DEVICE_BATCH=2 GRAD_ACCUM=16`
fits comfortably; if raising per-device batch to cut step noise, watch `nvidia-smi`
(whole 7B GRPO setup ≈ 45GB at 256 seqs). Checkpoints land in
`~/calibrate-rl/checkpoint/run_<timestamp>/`; push anything you care about to
git/W&B — treat the box as compute, not storage.

## 3. vLLM endpoint (transcript reading, holdout-via-API, the step-3 UI)

```bash
bash ~/serve_vllm.sh        # tmux session "vllm", ~2-3 min to load
tmux kill-session -t vllm   # stop it — REQUIRED before training/calibration (holds 42GB)
```

Localhost-only by design (port 8000 is closed in the AWS firewall — don't reopen
it). From a laptop, tunnel:

```bash
ssh -L 8000:localhost:8000 gpu
# locally: BASE_URL=http://localhost:8000/v1  MODEL=Qwen/Qwen2.5-7B-Instruct
OPENROUTER_API_KEY=unused BASE_URL=http://localhost:8000/v1 python3 tools/run_holdout.py
```

Never run vLLM and training/calibration simultaneously — one GPU, both want it.

## 4. Gotchas (each cost us time — don't rediscover them)

1. **`dnf` / system Python:** AL2023's `dnf` needs `/usr/bin/python3` → 3.9. It
   was broken for months because a previous setup repointed it to 3.11 (fixed
   2026-06-11). **Never `alternatives --set python3 /usr/bin/python3.11`.** Venvs
   use 3.11 explicitly; system python stays 3.9.
2. **Triton JIT** needs `gcc` + `python3.11-devel` (installed). Future venv
   rebuild hitting `Failed to import trl ... gcc ... exit status 1` = this.
3. **vLLM needs its venv ACTIVATED**, not just the binary path — it shells out to
   `ninja`. `~/serve_vllm.sh` does it right.
4. **Capacity queueing** is normal (§1). Retry, don't debug.
5. **W&B:** `WANDB_API_KEY` (trainer also accepts legacy `WANDB_TOKEN`); entity
   `rl-intro`, project `tiny-math-solver`. Never commit keys.
6. **trl 1.5.1 / transformers 5.11** are newer than Lightning's. `GRPOConfig`
   dry-run passes with all of `train_grpo.py`'s args; one harmless deprecation
   (`warmup_ratio` → `warmup_steps` at transformers 5.2).
7. Only SSH (22) is open at the security-group level. Use tunnels for everything.

## 5. The Slack agent

Setup is **PART C** above. Once running: `@trainaws` in #calibrate-rl-agents from
anyone in the channel; it pulls code, starts the GPU box, launches handed-off
runs, posts lifecycle, and the box self-stops after training. Bot lives on the
API box under the sandboxed `agent` user (pm2 process `trainaws`); logs via
`~/.local/bin/pm2 logs trainaws` as that user. Claude Code is also on the GPU box
itself (`claude` in any SSH session) for interactive use.
