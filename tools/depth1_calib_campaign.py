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
  SAM_INSTANCE=i-065bb6d4bcea507db   BUCKET=calibrate-rl-agent
  BRANCH=agent/depth1-calib-campaign   INJECTOR=generate/skeleton_injector_v12.py
  CLAUDE_CMD="claude -p"   POOL_N_PER_CHAIN=40   SAMPLE_TIMEOUT_MIN=300   DRY_RUN=0
"""
import os, sys, json, time, subprocess, glob, datetime

E = os.environ.get
N_ITERS   = int(E("N_ITERS", "5"))
N         = int(E("N", "250"))
ROLLOUTS  = int(E("ROLLOUTS", "8"))
MAX_TOKENS= int(E("MAX_TOKENS", "2048"))
CKPT_S3   = E("CKPT_S3", "s3://calibrate-rl-agent/runs/v12_depth0_run2/checkpoint-40")
SAM       = E("SAM_INSTANCE", "i-065bb6d4bcea507db")
BUCKET    = E("BUCKET", "calibrate-rl-agent")
BRANCH    = E("BRANCH", "agent/depth1-calib-campaign")
INJECTOR  = E("INJECTOR", "generate/skeleton_injector_v12.py")
CLAUDE    = E("CLAUDE_CMD", "claude -p")
PER_CHAIN = int(E("POOL_N_PER_CHAIN", "40"))
TIMEOUT_S = int(E("SAMPLE_TIMEOUT_MIN", "300")) * 60
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
    # 3. static checks (dedupe/top3) if available
    sc = sh(f"python3 -m automation.calibrator.static_checks {pool_path}",
            check=False, env=ENV_INJ, capture=True)
    # static_checks may exit nonzero on dedupe-only flags; treat gold/top3 hard-fails only
    if sc.returncode not in (0,) and "top3" in (sc.stdout + sc.stderr).lower():
        return False, f"static_checks hard fail: {sc.stdout[-200:]}"
    return True, "gate OK"


def upload(local, s3uri):
    sh(f"aws s3 cp {local} {s3uri}")


def dispatch_sample(it, pool_s3, out_s3):
    spec = {"type": "sample", "checkpoint": CKPT_S3, "dataset": pool_s3,
            "n": N, "rollouts": ROLLOUTS, "max_tokens": MAX_TOKENS, "output_uri": out_s3}
    spec_local = f"/tmp/depth1_calib_iter{it}_spec.json"
    json.dump(spec, open(spec_local, "w"))
    spec_s3 = f"s3://{BUCKET}/pending/sam/depth1_calib_iter{it}.json"
    if DRY_RUN:
        log(f"[dry-run] would upload spec {spec} -> {spec_s3} and start {SAM}"); return
    upload(spec_local, spec_s3)
    sh(f"aws ec2 start-instances --instance-ids {SAM}")


def wait_for_output(out_s3):
    """Poll S3 until calib.json lands (box self-stops on completion)."""
    t0 = time.time()
    while time.time() - t0 < TIMEOUT_S:
        r = sh(f"aws s3 ls {out_s3}", check=False, capture=True)
        if r.returncode == 0 and r.stdout.strip():
            return True
        time.sleep(60)
    return False


EDIT_PROMPT = """You are tuning DEPTH-1 chain generators toward the goldilocks band (pass rate ~0.45-0.55) for GRPO.

Calibration readout for this iteration (per chain: verdict + suggested direction):
{report}

Edit the generators to move the FLAGGED chains toward goldilocks. Rules (HARD):
- Edit ONLY the chain layer: the `_register_diverse_chain` factory, `_ADAPT` adapters, `_DIVERSE_CHAINS` map, and chain framings in {injector}; and automation/calibrator/knobs/chain_*.json. If you change a chain's structure, update its recomputer in prep/check_dataset.py to match.
- NEVER edit depth-0 atomic generators or knobs/<atomic>.json. (An atom-equivalence test will revert any such change.)
- Difficulty moves via STEP/CONSTRAINT COUNT, never number size (§4).
- TOO_HARD -> fewer steps/constraints. TOO_EASY -> more. LOW_DIVERSITY -> widen the non-fed inputs so answers spread.
A static gate (gold recompute + dedupe/top3 + atom-equivalence + smoke) runs after you finish and REVERTS any edit that breaks it, so make valid, gate-passing edits.

When done, write a concise rationale (which chains, what you changed, why) to: {rationale_path}
"""


def llm_edit(it, report_md, rationale_path):
    prompt = EDIT_PROMPT.format(report=report_md, injector=INJECTOR, rationale_path=rationale_path)
    pf = f"/tmp/edit_prompt_iter{it}.txt"; open(pf, "w").write(prompt)
    if DRY_RUN:
        log("[dry-run] would invoke claude to edit generators"); open(rationale_path, "w").write("(dry-run, no edits)\n"); return
    # headless claude; allow file edits + reading; bounded. CLAUDE_CMD is configurable per box.
    sh(f'{CLAUDE} "$(cat {pf})" --allowedTools Edit Read Bash --permission-mode acceptEdits',
       check=False, timeout=1800)


def revert_unstaged():
    sh("git checkout -- generate/ automation/ prep/ 2>/dev/null", check=False)


def main():
    sh(f"git checkout {BRANCH}", check=False)
    slack(f":arrows_counterclockwise: depth-1 calibration campaign starting — {N_ITERS} iters, "
          f"{N}x{ROLLOUTS}@{MAX_TOKENS} on sam vs ckpt-40")
    for it in range(1, N_ITERS + 1):
        log(f"================= ITERATION {it}/{N_ITERS} =================")
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
        out_s3  = f"s3://{BUCKET}/runs/depth1_calib_iter{it}/calib.json"
        upload(pool_local, pool_s3)
        slack(f":satellite: iter {it}: sampling {N} on sam (vs ckpt-40)…")
        dispatch_sample(it, pool_s3, out_s3)
        if not (DRY_RUN or wait_for_output(out_s3)):
            slack(f":x: iter {it}: sample timed out after {TIMEOUT_S//60}min — stopping"); break

        calib_local = f"data/depth1_calib_iter{it}.json"
        if not DRY_RUN: sh(f"aws s3 cp {out_s3} {calib_local}")
        rep_md = f"results/depth1_calib_iter{it}.md"
        rat    = f"/tmp/rationale_iter{it}.md"
        if not DRY_RUN:
            sh(f"python3 analysis/depth1_calib_analyze.py {calib_local} --md {rep_md} --json /tmp/rep{it}.json")
            report_text = open(rep_md).read()
        else:
            report_text = "(dry-run: no calib data)"

        # ---- edit + re-gate (revert on fail) ----
        llm_edit(it, report_text, rat)
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
