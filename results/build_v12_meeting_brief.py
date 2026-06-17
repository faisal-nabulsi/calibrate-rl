#!/usr/bin/env python3
"""Build the v12 final depth-0 run meeting brief (Faisal x Zaid).
Numbers pulled live from logs/run1_v12.log on the L40S + data/v12_*.json on 2026-06-15.
Pure-ASCII content (fpdf2 core fonts are latin-1)."""
from fpdf import FPDF
from fpdf.enums import XPos, YPos

WANDB = "https://wandb.ai/rl-intro/tiny-math-solver/runs/1pf2vi1c"
BOX = "ec2-user@34.226.11.242  (L40S, i-07455ba55e473769d)"

class PDF(FPDF):
    def multi_cell(self, *a, **k):
        k.setdefault("new_x", XPos.LMARGIN); k.setdefault("new_y", YPos.NEXT)
        return super().multi_cell(*a, **k)
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140)
        self.cell(0, 8, "v12 final depth-0 run -- meeting brief (Faisal x Zaid) -- 2026-06-15", align="R")
        self.ln(10)
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140)
        self.cell(0, 8, f"page {self.page_no()} -- prepared by kathryne -- RUN IN PROGRESS at print time", align="C")

def H1(p, t):
    p.set_font("Helvetica", "B", 15); p.set_text_color(20); p.ln(2)
    p.multi_cell(0, 8, t); p.ln(1)
def H2(p, t):
    p.set_font("Helvetica", "B", 11.5); p.set_text_color(30); p.ln(1.5)
    p.multi_cell(0, 6, t); p.ln(0.5)
def body(p, t):
    p.set_font("Helvetica", "", 10); p.set_text_color(45)
    p.multi_cell(0, 5.2, t); p.ln(0.5)
def bullet(p, t, ind=0):
    p.set_font("Helvetica", "", 10); p.set_text_color(45)
    x = p.get_x()
    p.set_x(x + 4 + ind*5)
    p.multi_cell(0, 5.2, "- " + t)
def kv_table(p, rows, widths=(70, 110)):
    p.set_font("Helvetica", "", 9.5)
    for k, v in rows:
        p.set_text_color(20); p.set_font("Helvetica", "B", 9.5)
        y0 = p.get_y(); x0 = p.get_x()
        p.multi_cell(widths[0], 5.4, k, border=0)
        yk = p.get_y()
        p.set_xy(x0 + widths[0], y0)
        p.set_text_color(45); p.set_font("Helvetica", "", 9.5)
        p.multi_cell(widths[1], 5.4, v, border=0)
        p.set_y(max(yk, p.get_y()))
    p.ln(1)

p = PDF(orientation="P", unit="mm", format="A4")
p.set_auto_page_break(auto=True, margin=16)
p.add_page()

# ---- Title block ----
p.set_font("Helvetica", "B", 20); p.set_text_color(15)
p.multi_cell(0, 9, "v12 Final Depth-0 Run")
p.set_font("Helvetica", "B", 13); p.set_text_color(90)
p.multi_cell(0, 7, "Meeting brief for Faisal x Zaid")
p.set_font("Helvetica", "", 10); p.set_text_color(110)
p.multi_cell(0, 5.5, "2026-06-15  |  prepared by kathryne  |  status: RUN IN PROGRESS (~step 19/56, 34%)")
p.ln(2)
p.set_draw_color(200); p.line(p.l_margin, p.get_y(), 210-p.r_margin, p.get_y()); p.ln(3)

# ---- TL;DR ----
H1(p, "TL;DR -- what to walk out of this meeting having decided")
bullet(p, "The v12 'final depth-0' GRPO+LoRA run is LIVE on the L40S (first run on vLLM). ~34% done; clean so far.")
bullet(p, "Early held-out signal is positive: base 0.454 -> 0.535 at step 14 (+0.081, +17.8% relative) on the frozen 79-problem held-out set.")
bullet(p, "The load-bearing question is UNCHANGED: is that gain concept learning, or template/wording reliability (Zaid's 06-11 reframe)? The concept-transfer by-framing analysis (Michael, pending) is the discriminator.")
bullet(p, "Decisions gated on this: (a) does the final depth-0 run 'count' as the depth-0 model; (b) does depth-1 chaining proceed (it is curriculum-gated on a trained depth-0 model -- which THIS run produces).")
p.ln(1)
p.set_fill_color(255, 247, 224)
p.set_font("Helvetica", "B", 9.5); p.set_text_color(120, 80, 0)
p.multi_cell(0, 5.2, "FLAG (kathryne): project TODO says 'HOLD the big final depth-0 run until the concept-transfer eval result is in.' This run launched 06-14 23:44. Confirm at the top of the meeting whether that gate was cleared or this is a parallel/preliminary run -- it changes how much weight the result carries.", fill=True)
p.ln(1)

# ---- Run config ----
H1(p, "1. Run configuration (facts)")
kv_table(p, [
    ("Model", "Qwen2.5-7B-Instruct + LoRA, GRPO"),
    ("W&B run", "1pf2vi1c  (project rl-intro / tiny-math-solver)"),
    ("Train set", "data/v12_train.json -- 449 rows, 27 concepts (log_laws dropped). 302 goldilocks + 147 borderline. Mean base pass_rate 0.488."),
    ("Held-out", "data/v12_holdout.json -- 79 rows, frozen, disjoint, seed 42, 3/concept (2 for two thin concepts). 63 goldilocks + 16 borderline. Mean base pass_rate 0.517."),
    ("Reserve", "90 too_hard rows held for B2 promotion. 127 too_easy dropped (no signal)."),
    ("Backend", "vLLM colocate ON (USE_VLLM=1, VLLM_GPU_UTIL=0.5) -- the FIRST vLLM training run."),
    ("Schedule", "2 epochs, 56 steps total, ctx/completion 2048, held-out eval every 14 steps."),
    ("Hardware", "L40S 48GB; ~4.5-5 min/step + periodic evals; ~4-6h to completion from print time."),
])

# ---- Key stats ----
H1(p, "2. Key stats (live, from the run log)")
H2(p, "Held-out mean_pass_rate -- the honest signal (per CLAUDE.md sec.7: raw reward is confounded)")
kv_table(p, [
    ("step 0 (base)", "mean_pass_rate 0.4541  |  pass@16 1.000  |  boxed_rate 0.995  |  mean tokens 756"),
    ("step 14", "mean_pass_rate 0.5348  |  pass@16 0.987  |  boxed_rate 0.994  |  mean tokens 769"),
    ("delta so far", "+0.0807 absolute (+17.8% relative).  NOTE: only ONE periodic eval has landed; the step-28 eval is the next datapoint and matters more."),
], widths=(34, 146))
H2(p, "Training health (steps 1-19)")
bullet(p, "Correctness reward: noisy, ~0.34-0.57 (peak 0.570 at step 11), currently ~0.41. Total reward ~0.47-0.67.")
bullet(p, "Ghost batches (frac_reward_zero_std): 0-0.31, mostly <=0.12. vs v3 catastrophe 77.8% and v10 ~0.10 -- goldilocks band is HEALTHY, signal is live.")
bullet(p, "KL: 0.0002 -> brief 0.017 spike at step 17 -> back ~0.0016. Stable, no policy blow-up.")
bullet(p, "Importance-sampling ratio mean: drifts 0.87 -> 0.43. This is the vLLM rollout-vs-training logprob mismatch -- EXPECTED and TRL-handled (Michael's 06-12 note), NOT a bug. Worth saying out loud so it isn't misread as divergence.")
bullet(p, "Completions: mean length ~690-900 tok, clipped_ratio ~0-0.02 (2048 ctx is not binding). Format reward saturated ~0.10 cap.")

# ---- The debate ----
p.add_page()
H1(p, "3. The debate to settle (Zaid x Faisal)")
body(p, "This is the same concept-vs-template question from the 06-11 sync, now with the final depth-0 run in flight.")
bullet(p, "Zaid's reframe (06-11): stop calling the gain 'overfitting' -- held-out went UP (+0.22 on v10/3-concept), so it is not overfit. The model is learning the question templates / wording reliably (fewer dumb mistakes on a method it already knows), NOT generalizable concept skill.")
bullet(p, "Discriminator: the concept-transfer eval -- v2 with 5 same-task framings, headroom-fixed (#61). If the gain survives surface-form variation -> concept learning. If it evaporates -> template reliability.")
bullet(p, "Michael's by-framing analysis (responses landed #31; analysis pending) is the REMAINING GATE for the 'final depth-0 run' decision. Faisal wants it; Michael is skeptical.")
bullet(p, "Why it matters for depth-1: the chaining program is justified only if depth-0 teaches transferable concept skill that compositions can build on. The base diagnostic (06-12) already confirmed the AMC ceiling is composition, not atom knowledge (composition gap +0.19 to +0.61 across 3 chains) -- so depth-1 is queued, but curriculum-gated on THIS depth-0 model.")
p.ln(1)
H2(p, "Suggested decisions to reach")
bullet(p, "1. Is the held-out trajectory (watch step-28/42/56 evals) strong enough to call the depth-0 run a success on its own terms?")
bullet(p, "2. Does the concept-transfer result change the interpretation -- and is it a blocker for declaring depth-0 'done'?")
bullet(p, "3. Green-light depth-1 calibration against this checkpoint once it lands, or hold for the transfer verdict?")

# ---- W&B walkthrough ----
H1(p, "4. W&B walkthrough -- do this live with Zaid")
body(p, "Faisal: open the run and scroll these panels with Zaid. URL:")
p.set_font("Courier", "", 9); p.set_text_color(20)
p.multi_cell(0, 5, WANDB); p.ln(0.5)
bullet(p, "train/reward + rewards/correctness_reward/mean -- the noisy raw signal. Caveat it: batch composition + EMA make raw reward a poor truth source (sec.7). Use it for slope/health, not for the headline.")
bullet(p, "frac_reward_zero_std -- the ghost-batch monitor. Point out it is sitting low (<=0.12); this is the #1 run-killer and it is under control.")
bullet(p, "kl + entropy -- stability. Flat/low = policy not blowing up.")
bullet(p, "completions/mean_length + clipped_ratio -- confirms 2048 ctx isn't truncating reasoning.")
bullet(p, "sampling/importance_sampling_ratio -- pre-empt the question: the downward drift is the vLLM logprob mismatch, expected.")
bullet(p, "Held-out mean_pass_rate is NOT in W&B charts -- W&B rejects out-of-order steps, so held-out is emitted to stdout banners only (sec.9). Read it from the log banners or rebuild via holdout_matrix.py. The numbers in section 2 above are the source of truth for the meeting.")

# ---- Transcripts ----
H1(p, "5. Accessing transcripts (if Zaid asks)")
H2(p, "A. Live per-prompt rollouts (this run)")
body(p, "Written every step as parquet (log_completions=True). On the L40S box:")
p.set_font("Courier", "", 8.5); p.set_text_color(20)
p.multi_cell(0, 4.6,
"ssh " + BOX + "\n"
"ls ~/calibrate-rl/checkpoint/run_20260614_234419/completions/   # completions_00001.parquet ... one per step\n"
"python3 - <<'PY'\n"
"import pandas as pd, glob\n"
"f = sorted(glob.glob('/home/ec2-user/calibrate-rl/checkpoint/run_20260614_234419/completions/*.parquet'))[-1]\n"
"df = pd.read_parquet(f)\n"
"print(df.columns.tolist()); print(df[['prompt','completion','reward']].head())\n"
"PY")
p.ln(1)
H2(p, "B. Base-vs-trained held-out responses (qualitative diff)")
p.set_font("Courier", "", 8.5); p.set_text_color(20)
p.multi_cell(0, 4.6,
"# on the agents box, in the repo (results/):\n"
"results/holdout_resp_base__abl3_holdout.json\n"
"results/holdout_resp_checkpoint-108__abl3_holdout.json\n"
"results/holdout_compare.html        # side-by-side viewer (PR #21) -- open in a browser")
p.ln(1)
H2(p, "C. Concept-transfer eval responses (the discriminator)")
p.set_font("Courier", "", 8.5); p.set_text_color(20)
p.multi_cell(0, 4.6,
"results/holdout_resp_base__concept_transfer_eval.json\n"
"results/holdout_resp_checkpoint-108__concept_transfer_eval.json   # 5 same-task framings (#61)")
p.ln(2)
p.set_font("Helvetica", "I", 9); p.set_text_color(110)
p.multi_cell(0, 5, "Keep grader + system prompt + gen length identical across calib / held-out / AMC when comparing (sec.9). The v12 holdout is frozen and disjoint (seed 42, leak-checked).")

out = "/home/kathryne/calibrate-rl/results/v12_depth0_meeting_brief.pdf"
p.output(out)
print("wrote", out)
