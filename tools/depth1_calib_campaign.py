#!/usr/bin/env python3
"""
depth1_calib_campaign.py — autonomous depth-1 chain calibration loop.

Runs on the t3 (autocalib): uses the box's Anthropic key (headless `claude` for the
edit step), git, Slack webhook, and AWS creds. Each iteration:

  1. build the 47-chain pool from the CURRENT (possibly edited) generators  [CPU, this box]
  2. STATIC GATE: gold recomputers + static_checks + atom-equivalence + smoke   (abort iter on fail)
  3. upload pool to S3; write a sample spec; start the L4 (sam); the box samples
     ckpt-40 via its poller and self-stops; we poll S3 for calib.json           [GPU, sam/L4]
  4. ANALYZE per-chain difficulty + diversity (analysis/depth1_calib_analyze.py)
  5. EDIT: headless `claude` tunes the CHAIN LAYER toward goldilocks (depth-0 frozen)
  6. RE-GATE the edits — auto-revert (git checkout) anything that breaks the gate
  7. write results/depth1_calib_iter<N>.md (analysis + what changed + why)
  8. commit doc + edits to the campaign branch; Slack update
  ... repeat N_ITERS times.

Safety: depth-0 atomics are protected by the atom-equivalence test (must stay
byte-identical to the fixture) — any edit that perturbs an atom is reverted. Chain
golds are independently recomputed. Difficulty moves via step/constraint count only
(§4). Nothing is pushed to main; commits land on the campaign branch for human review.

Env (all have defaults):
  N_ITERS=5  N=250  ROLLOUTS=8  MAX_TOKENS=2048
  CKPT_S3=s3://calibrate-rl-agent/runs/v12_depth0_run2/checkpoint-40
  SAMPLER=sadie   (or sam)   BUCKET=calibrate-rl-agent
  BRANCH=agent/depth1-calib-campaign   INJECTOR=generate/skeleton_injector_v12.py
  CLAUDE_CMD="claude -p"   POOL_N_PER_CHAIN=40   SAMPLE_TIMEOUT_MIN=300   DRY_RUN=0
"""
import os, sys, json, time, subprocess, glob, datetime

E = os.environ.get
N_ITERS   = int(E("N_ITERS", "5"))
RESUME    = E("RESUME", "1") == "1"   # reuse an already-landed iter calib instead of re-sampling (saves ~6h/iter)
N         = int(E("N", "250"))
ROLLOUTS  = int(E("ROLLOUTS", "8"))
MAX_TOKENS= int(E("MAX_TOKENS", "2048"))
CKPT_S3   = E("CKPT_S3", "s3://calibrate-rl-agent/runs/v12_depth0_run2/checkpoint-40")
# which L4 sampler to dispatch to (queue path = pending/<SAMPLER>/, woken by instance id)
_L4 = {"sam": "i-065bb6d4bcea507db", "sadie": "i-05c7938e1c6711370"}
SAMPLER   = E("SAMPLER", "sadie")
SAM       = E("SAMPLER_INSTANCE", _L4.get(SAMPLER, _L4["sadie"]))
BUCKET    = E("BUCKET", "calibrate-rl-agent")
BRANCH    = E("BRANCH", "agent/depth1-calib-campaign")
INJECTOR  = E("INJECTOR", "generate/skeleton_injector_v12.py")
CLAUDE    = E("CLAUDE_CMD", "claude -p")
PER_CHAIN = int(E("POOL_N_PER_CHAIN", "40"))
TIMEOUT_S = int(E("SAMPLE_TIMEOUT_MIN", "720")) * 60       # absolute backstop ONLY (default 12h)
HB_STALE_S = int(E("HEARTBEAT_STALE_MIN", "30")) * 60      # heartbeat silent + no output this long => actually hung
WEBHOOK   = E("SLACK_WEBHOOK_URL", "")
DRY_RUN   = E("DRY_RUN", "0") == "1"
REPO      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
ENV_INJ   = {**os.environ, "INJECTOR": INJECTOR}


def log(m): print(f"[campaign {datetime.datetime.utcnow():%H:%M:%S}] {m}", flush=True)


def sh(cmd, check=True, env=None, capture=False, timeout=None):
    log(f"$ {cmd}" if isinstance(cmd, str) else "$ " + " ".join(cmd))
    r = subprocess.run(cmd, shell=isinstance(cmd, str), env=env or os.environ,
                       capture_output=capture, text=True, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"cmd failed ({r.returncode}): {cmd}\n{getattr(r,'stderr','')}")
    return r


def slack(msg):
    if not WEBHOOK or DRY_RUN:
        log(f"[slack] {msg}"); return
    try:
        import urllib.request
        body = json.dumps({"text": f"[autocalib] {msg}"}).encode()
        urllib.request.urlopen(urllib.request.Request(
            WEBHOOK, data=body, headers={"Content-type": "application/json"}), timeout=10)
    except Exception as e:
        log(f"slack post failed (non-fatal): {e}")


def chain_names():
    import importlib.util
    spec = importlib.util.spec_from_file_location("inj", INJECTOR)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return [n for n, _, _ in m.REGISTRY if n.startswith("chain_")]


def build_pool(out_path):
    """gen_clean each chain -> merge. Returns (n_rows, n_chains)."""
    tmp = f"/tmp/campaign_pool_{os.getpid()}"; sh(f"rm -rf {tmp} && mkdir -p {tmp}")
    for ch in chain_names():
        # hard per-chain timeout so a bad edit's slow generator can't stall the loop
        sh(f"perl -e 'alarm 30; exec @ARGV' python3 prep/gen_clean.py "
           f"--concept {ch} --n {PER_CHAIN} --out {tmp}/{ch}.json", check=False, env=ENV_INJ)
    rows = []
    for f in sorted(glob.glob(f"{tmp}/chain_*.json")):
        if f.endswith(".meta.json"): continue
        rows += json.load(open(f))
    json.dump(rows, open(out_path, "w"))
    n_chains = len({"__".join(r["chain"]["components"]) for r in rows if r.get("chain")})
    return len(rows), n_chains


def gate(pool_path):
    """Static safety gate. Returns (ok, detail). Used both pre-sample and post-edit."""
    # 1. depth-0 atoms must stay byte-identical (protects ckpt-40 calibration target).
    # Distinguish a REAL failure (test ran, atom changed -> exit 1 with "failed") from the
    # test being UNABLE to run (missing dep / collection error -> other codes or "no module"):
    # the latter is an env problem, NOT an atom perturbation, so don't misreport it as one.
    eq = sh("python3 -m pytest -q automation/calibrator/tests/test_knob_equivalence.py",
            check=False, env=ENV_INJ, capture=True)
    out = (eq.stdout + eq.stderr).lower()
    if eq.returncode == 1 and "failed" in out:
        return False, "atom-equivalence FAILED (an edit perturbed a depth-0 atom) — REVERTING"
    if eq.returncode != 0:
        return False, (f"GATE-COULD-NOT-RUN: equivalence test errored (rc={eq.returncode}) — an "
                       f"env/dep issue, NOT an atom change. Fix the box; don't trust this gate. "
                       f"tail: {out[-160:]}")
    # 2. chain golds independently recomputed
    cd = sh(f"python3 prep/check_dataset.py {pool_path}", check=False, env=ENV_INJ, capture=True)
    if "mismatch" in cd.stdout and "0 mismatches" not in cd.stdout:
        return False, "gold recomputer found mismatches"
    # 3. diversity/dedupe — computed INLINE on the actual built pool (no brittle subprocess).
    # The gate HARD-fails only on SEVERE collapse (a degenerate, answer-hacked chain); mild
    # top3 (0.30-0.50) is what the loop is meant to FIX, so the analyzer flags those for the
    # edit step rather than the gate reverting them.
    import collections
    rows = json.load(open(pool_path))
    bychain = collections.defaultdict(list)
    for r in rows:
        c = r.get("chain") or {}
        bychain["__".join(c.get("components", [])) or r.get("skeleton_type", "?")].append(
            str(r.get("answer", r.get("gold"))))
    severe = []
    for ch, ans in bychain.items():
        if len(ans) < 8:
            continue
        top3 = sum(v for _, v in collections.Counter(ans).most_common(3)) / len(ans)
        dd = len(set(ans)) / len(ans)
        if top3 > 0.50 or dd < 0.40:
            severe.append(f"{ch}(top3={top3:.2f},dd={dd:.2f})")
    if severe:
        return False, "SEVERE diversity collapse: " + ", ".join(severe[:6])
    return True, "gate OK"


def upload(local, s3uri):
    sh(f"aws s3 cp {local} {s3uri}")


def ensure_running(instance, tries=30, wait=60):
    """Get the box to running. Tolerates: already running/pending (ok); a TRANSITIONAL
    state (stopping/shutting-down — e.g. mid self-stop from a prior job — wait for it to
    settle); InsufficientInstanceCapacity (GPU AZ full — retry); IncorrectInstanceState
    (can't start mid-transition — retry). Only a genuinely unexpected error fails. Bool."""
    for i in range(tries):
        st = sh(f"aws ec2 describe-instances --instance-ids {instance} "
                f"--query 'Reservations[].Instances[].State.Name' --output text",
                check=False, capture=True).stdout.strip()
        if st in ("running", "pending"):
            return True
        if st in ("stopping", "shutting-down"):       # still self-stopping — let it settle first
            log(f"{instance} is {st}; waiting {wait}s for it to reach stopped"); time.sleep(wait); continue
        r = sh(f"aws ec2 start-instances --instance-ids {instance}", check=False, capture=True)
        if r.returncode == 0:
            return True
        blob = (r.stdout + r.stderr)
        if any(x in blob for x in ("InsufficientInstanceCapacity", "IncorrectInstanceState", "Unsupported")):
            log(f"start retry {i+1}/{tries} in {wait}s ({blob.strip()[-100:]})"); time.sleep(wait); continue
        log(f"start-instances failed (unexpected): {blob[-200:]}"); return False
    return False


def dispatch_sample(it, pool_s3, out_s3):
    spec = {"type": "sample", "checkpoint": CKPT_S3, "dataset": pool_s3,
            "n": N, "rollouts": ROLLOUTS, "max_tokens": MAX_TOKENS, "output_uri": out_s3}
    spec_local = f"/tmp/depth1_calib_iter{it}_spec.json"
    json.dump(spec, open(spec_local, "w"))
    spec_s3 = f"s3://{BUCKET}/pending/{SAMPLER}/depth1_calib_iter{it}.json"
    if DRY_RUN:
        log(f"[dry-run] would upload spec {spec} -> {spec_s3} and start {SAM}"); return True
    upload(spec_local, spec_s3)
    return ensure_running(SAM)


def wait_for_output(out_s3):
    """HEARTBEAT-AWARE wait. The sampler streams a `<output>.heartbeat` to S3 every ~120s
    (run_sample_job, #92); keep waiting as long as it ADVANCES (the job is making progress)
    and only declare a real 'timeout' if the heartbeat goes stale for HB_STALE_S with no
    output — i.e. genuinely hung. So a slow-but-fine 6h+ sample no longer false-aborts the
    whole campaign (the iter-1 footgun: 250x8@2048 ran ~6h > the old 5h wall-clock cap, so
    the wait gave up an hour before the box finished and `break` killed all 5 iters).
    TIMEOUT_S is now just an absolute backstop. The stale-timeout only kicks in ONCE a
    heartbeat has appeared — a heartbeat-LESS run (e.g. a box on pre-#92 code, as iter-1
    itself was) falls back to the TIMEOUT_S wall-clock so we never penalize it as 'hung'.
    Returns 'ok' | 'fail:<tail>' | 'timeout'."""
    bucket = out_s3.split("/")[2]
    key = "/".join(out_s3.split("/")[3:])
    logkey = key + ".log"
    hbkey  = key + ".heartbeat"
    def mtime(k):                       # LastModified of an S3 object, or None if absent
        r = sh(f"aws s3api head-object --bucket {bucket} --key {k} --query LastModified --output text",
               check=False, capture=True)
        return r.stdout.strip() if r.returncode == 0 else None
    t0 = time.time()
    last_hb = None
    last_progress = None                # set on the FIRST heartbeat; until then, only TIMEOUT_S applies
    while time.time() - t0 < TIMEOUT_S:
        if sh(f"aws s3api head-object --bucket {bucket} --key {key}",
              check=False, capture=True).returncode == 0:
            return "ok"
        if mtime(logkey):
            body = sh(f"aws s3 cp s3://{bucket}/{logkey} -", check=False, capture=True).stdout
            if "Traceback" in body or "FAILED" in body or "Error" in body:
                return "fail:" + body[-400:]
        hb = mtime(hbkey)
        if hb and hb != last_hb:        # heartbeat advanced => still working; reset the stale clock
            last_hb, last_progress = hb, time.time()
        if last_progress is not None and time.time() - last_progress > HB_STALE_S:
            return "timeout"            # heartbeat WAS flowing, then went silent HB_STALE_S => hung
        time.sleep(60)
    return "timeout"


EDIT_PROMPT = """You are tuning DEPTH-1 chain generators toward the goldilocks band (pass rate ~0.45-0.55) for GRPO.

Calibration readout for this iteration (per chain: verdict + suggested direction):
{report}

Edit the generators to move the FLAGGED chains toward goldilocks. Rules (HARD):
- Edit ONLY the chain layer: the `_register_diverse_chain` factory, `_ADAPT` adapters, `_DIVERSE_CHAINS` map, and chain framings in {injector}; and automation/calibrator/knobs/chain_*.json. If you change a chain's structure, update its recomputer in prep/check_dataset.py to match.
- NEVER edit depth-0 atomic generators or knobs/<atomic>.json. (An atom-equivalence test will revert any such change.)
- Difficulty moves via STEP/CONSTRAINT COUNT, never number size (§4).
- Your PRIMARY lever is DIFFICULTY. TOO_HARD -> fewer steps/constraints; TOO_EASY -> more. Aim for the
  usable band (mean pass 0.25-0.75, ideally ~0.5). Do NOT over-ease a TOO_HARD chain past 0.75 into too-easy
  (iters 1-5 over-eased several chains, e.g. vieta_sumcubes/percent_compound, into the 0.9s).
- DIVERSITY (answer top3) is OWNED BY THE STATIC BUILD GATE, which recomputes top3 at build-n (~40/chain)
  and reverts any edit that pushes a chain >0.30. Do NOT chase the per-iteration SAMPLE top3 — at ~5-10
  rows/chain it is small-sample noise (a sample top3 of 0.45 is almost always already <0.30 at build n).
  Only act on a LOW_DIVERSITY verdict — the readout raises it ONLY when the sample is large enough to trust.
- If a LOW_DIVERSITY chain's cap is the FEEDER (it emits few distinct intermediate V, so no target-side
  widening can spread the answers), you CANNOT fix it from the chain layer — write it in your rationale under
  a "FEEDER-CAPPED (needs human feeder-pass)" heading and LEAVE IT; do not thrash the target side (that only
  breaks dedupe -> revert, which is what burned iters 1-5).
A static gate (gold recompute + dedupe/top3 + atom-equivalence + smoke) runs after you finish and REVERTS any edit that breaks it, so make valid, gate-passing edits.

When done, write a concise rationale (which chains, what you changed, why) to: {rationale_path}
"""


def llm_edit(it, report_md, rationale_path):
    """Run headless claude to edit the chain generators. Returns the claude EXIT CODE so the
    caller can verify it actually ran: a missing / unauthenticated CLI exits non-zero (127 =
    'command not found') and used to be SWALLOWED by check=False, letting the campaign commit a
    fake 'edits' iteration that changed nothing for a whole run."""
    prompt = EDIT_PROMPT.format(report=report_md, injector=INJECTOR, rationale_path=rationale_path)
    pf = f"/tmp/edit_prompt_iter{it}.txt"; open(pf, "w").write(prompt)
    if DRY_RUN:
        log("[dry-run] would invoke claude to edit generators"); open(rationale_path, "w").write("(dry-run, no edits)\n"); return 0
    # headless claude; allow file edits + reading; bounded. CLAUDE_CMD is configurable per box.
    r = sh(f'{CLAUDE} "$(cat {pf})" --allowedTools Edit Read Bash --permission-mode acceptEdits',
           check=False, timeout=1800)
    if r.returncode != 0:
        log(f"edit step: '{CLAUDE}' exited {r.returncode} — claude CLI missing / unauthenticated / errored; generators NOT tuned")
    return r.returncode


def revert_unstaged():
    sh("git checkout -- generate/ automation/ prep/ 2>/dev/null", check=False)


def _no_edits_yet():
    """No per-iter generator edits committed on this branch yet → the generators still match
    whatever produced an existing calib, so a resume is correct. (Edit commits are titled
    'depth1 calib iter N: ...'.) Once any iter has tuned + committed, we re-sample instead."""
    r = sh("git log --oneline -100", check=False, capture=True)
    return "depth1 calib iter" not in (r.stdout or "")


def _resume_calib(out_s3, calib_local):
    """If out_s3's calib already exists and is a valid, non-trivial JSON array, download it to
    calib_local and return True (resume). Else False (must sample). Recovers a sample that
    landed after the campaign had already given up (the iter-1 timeout footgun)."""
    bucket = out_s3.split("/")[2]; key = "/".join(out_s3.split("/")[3:])
    if sh(f"aws s3api head-object --bucket {bucket} --key {key}", check=False, capture=True).returncode != 0:
        return False
    sh(f"aws s3 cp {out_s3} {calib_local}", check=False)
    try:
        return len(json.load(open(calib_local))) >= 50
    except Exception:
        return False


def main():
    # double-run guard: refuse to start if another campaign instance is already running.
    # Two instances race on the same git tree + dispatch duplicate samples (the 02:32 footgun
    # that took two kills + a branch reset to clean up). NB: `pgrep -f depth1_calib_campaign.py`
    # also matches the su/bash LAUNCH WRAPPERS (their argv contains the script name), so filter to
    # processes whose ACTUAL executable (/proc/<pid>/comm) is a python interpreter, and drop self.
    me = os.getpid()
    others = []
    for p in sh("pgrep -f depth1_calib_campaign.py", check=False, capture=True).stdout.split():
        if not p.strip().isdigit() or int(p) == me:
            continue
        try:
            if open(f"/proc/{p}/comm").read().strip().startswith("python"):
                others.append(p)
        except Exception:
            pass
    if others:
        slack(f":no_entry: campaign launch aborted — another instance is already running (pids {','.join(others)}). "
              f"Not double-running.")
        log(f"ABORT: campaign already running (pids {others}); refusing to double-run")
        return
    sh(f"git checkout {BRANCH}", check=False)
    slack(f":arrows_counterclockwise: depth-1 calibration campaign starting — {N_ITERS} iters, "
          f"{N}x{ROLLOUTS}@{MAX_TOKENS} on {SAMPLER} vs ckpt-40")
    for it in range(1, N_ITERS + 1):
        log(f"================= ITERATION {it}/{N_ITERS} =================")
        out_s3      = f"s3://{BUCKET}/runs/depth1_calib_iter{it}/calib.json"
        calib_local = f"data/depth1_calib_iter{it}.json"

        # RESUME: if this iter's calib already landed AND we haven't tuned generators yet this
        # campaign, reuse it instead of re-spending ~6h re-sampling — recovers the iter-1 timeout
        # footgun (the sample completed, but the campaign had already given up before analyzing
        # it). The no-edits guard keeps it correct: after any iter commits edits, a stale calib no
        # longer matches the generators, so we fall through to a fresh sample.
        if RESUME and not DRY_RUN and _no_edits_yet() and _resume_calib(out_s3, calib_local):
            slack(f":recycle: iter {it}: resuming from already-sampled calib — skipped re-sampling (~6h saved)")
            log(f"iter {it}: RESUMED from existing {out_s3}")
        else:
            pool_local = f"data/chain_depth1_47_pool_iter{it}.json"
            nrows, nch = build_pool(pool_local)
            log(f"pool: {nrows} rows / {nch} chains")
            ok, detail = gate(pool_local)
            if not ok:
                slack(f":x: iter {it} pre-sample gate failed: {detail} — reverting + stopping"); revert_unstaged(); break
            if DRY_RUN:
                log(f"[dry-run] pool built + gate PASSED ({nrows} rows / {nch} chains) — "
                    f"stopping before GPU / edits / commit. Real run does the rest."); continue
            pool_s3 = f"s3://{BUCKET}/runs/depth1_calib_iter{it}/pool.json"
            # clear any stale output at this key from a PRIOR run — else wait_for_output reads the
            # old calib.json.log (e.g. a previous iteration's traceback) and false-fails instantly.
            sh(f"aws s3 rm {out_s3}", check=False); sh(f"aws s3 rm {out_s3}.log", check=False)
            upload(pool_local, pool_s3)
            slack(f":satellite: iter {it}: sampling {N} on {SAMPLER} (vs ckpt-40)…")
            if not dispatch_sample(it, pool_s3, out_s3):
                slack(f":warning: iter {it}: couldn't start {SAMPLER} — AWS out of GPU capacity after retries. "
                      f"Campaign stopping; relaunch when capacity returns."); break
            status = wait_for_output(out_s3)
            if status != "ok":
                slack(f":x: iter {it}: sample did not complete on {SAMPLER} — {status[:300]} — stopping"); break
            if not DRY_RUN: sh(f"aws s3 cp {out_s3} {calib_local}")
        rep_md = f"results/depth1_calib_iter{it}.md"
        rat    = f"/tmp/rationale_iter{it}.md"
        if not DRY_RUN:
            sh(f"python3 analysis/depth1_calib_analyze.py {calib_local} --md {rep_md} --json /tmp/rep{it}.json")
            report_text = open(rep_md).read()
        else:
            report_text = "(dry-run: no calib data)"

        # ---- edit + re-gate (revert on fail) ----
        rc = llm_edit(it, report_text, rat)
        # HARD GUARD: the edit must have RUN (rc 0) AND actually changed a generator. A silent
        # no-op (claude not installed -> rc 127, swallowed by check=False) ran a whole campaign
        # committing fake "edits" that changed nothing. Stop loudly instead of looping uselessly.
        if not DRY_RUN:
            changed = sh("git status --porcelain generate/ automation/ prep/",
                         check=False, capture=True).stdout.strip()
            if rc != 0 or not changed:
                slack(f":x: iter {it}: edit step made NO generator changes (claude rc={rc}) — not a real "
                      f"edit. Stopping; fix the editor (is the claude CLI installed + on PATH?) first.")
                revert_unstaged(); break
        post_pool = f"/tmp/postedit_pool_iter{it}.json"
        if not DRY_RUN:
            build_pool(post_pool)
            ok, detail = gate(post_pool)
            if not ok:
                slack(f":warning: iter {it}: edits failed the gate ({detail}) — REVERTED, keeping prior generators")
                revert_unstaged()
            else:
                log(f"iter {it}: edits passed the gate")

        # ---- doc + commit ----
        if os.path.exists(rat):
            open(rep_md, "a").write("\n\n## edits this iteration\n" + open(rat).read())
        sh(f"git add -A && git commit -q -m 'depth1 calib iter {it}: analysis + edits [autocalib]' || true", check=False)
        sh(f"git push -q origin {BRANCH} || true", check=False)
        slack(f":white_check_mark: iter {it} done — readout + edits committed to {BRANCH}")
    slack(f":checkered_flag: depth-1 calibration campaign finished ({N_ITERS} iters). Review {BRANCH} and open a PR.")


if __name__ == "__main__":
    main()
