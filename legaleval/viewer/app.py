"""LegalEval viewer/editor — a local web UI to browse prompts, responses, and grades.

Run:
    cd legaleval && .venv/bin/python -m viewer.app
    # then open http://127.0.0.1:5000

- Overview tab: what LegalEval is + the overall results table.
- Pick a prompt (sidebar, grouped by stage) -> see ALL five models' responses together,
  each a collapsible card with its grade, gate status, judge summary, and the full
  per-criterion grading rationale. A sticky model-nav jumps between them.
- Edit the prompt text and rubric inline and Save (writes back to suite/prompts.json
  and suite/rubrics/<ID>.json). Responses/grades are run outputs and are view-only.

Run dir auto-detected (newest under runs/ with responses + grades); override with LEGALEVAL_RUN.
"""

import csv
import json
import os
from collections import defaultdict
from pathlib import Path

import markdown as md
from flask import Flask, abort, render_template_string, request

ROOT = Path(__file__).resolve().parent.parent
SUITE = ROOT / "suite" / "prompts.json"
JUDGE = "claude-opus-4-8"
MODELS = ["claude-sonnet-4-6", "gpt-5.5", "gemini-3.5-flash", "qwen-3.7-plus", "llama-4-maverick"]
LABEL = {"claude-sonnet-4-6": "Claude Sonnet 4.6", "gpt-5.5": "GPT-5.5",
         "gemini-3.5-flash": "Gemini 3.5 Flash", "qwen-3.7-plus": "Qwen 3.7 Plus",
         "llama-4-maverick": "Llama 4 Maverick"}
DIMS = ["faithfulness", "directionality", "coverage", "soundness", "actionability"]
DIM_ABBR = {"faithfulness": "Faith", "directionality": "Dir", "coverage": "Cov",
            "soundness": "Sound", "actionability": "Action"}
STAGES = {"A": "Issue-spotting", "B": "Summarization & Extraction", "C": "Redlining",
          "D": "Drafting", "E": "Negotiation"}
# Per-stage explainer for the Overview page: (what the task is, why it matters for the benchmark).
STAGE_INFO = {
    "A": ("Find the legal problems in a document — missing protections, problematic clauses, "
          "and whether each gap helps or hurts the client.",
          "The highest-judgment, lowest-scoring work (A1 is the hardest task). Catching what's "
          "<i>absent</i> — and which absences are actually favorable — is where every model fails most."),
    "B": ("Pull and condense specific facts or terms from a contract — defined-term glossaries, "
          "key figures, structured extracts.",
          "The mechanical floor: faithfulness is near-ceiling here, so this stage is the control "
          "that proves models rarely fabricate — weakness elsewhere is judgment, not reading."),
    "C": ("Mark up a clause in the client's favor — directional editing toward an assigned seat.",
          "The most discriminating stage. Advocate-a-side editing is where directional drift and "
          "gate trips concentrate (C1/C2), separating strong models from weak ones."),
    "D": ("Produce a new document or clause from a brief — NDA, notice of breach, scoped amendment.",
          "Tests scope fidelity: does the model add only what's asked? The faithfulness / scope-creep "
          "gate lives here and is the single largest source of cross-judge disagreement."),
    "E": ("Reason across a whole deal — triage opposing-counsel redlines, assess deal viability.",
          "Holistic legal judgment under fluent prose: soundness failures (calling a bridgeable deal "
          "dead) and long-context frame-holding surface here, not in extraction or drafting."),
}


def categories_html(order, pmeta):
    """Overview explainer: each task category (stage) + why it matters."""
    cnt = {st: sum(1 for pid in order if pid.startswith(st)) for st in STAGES}
    items = "".join(
        f"<li style='margin:8px 0'><b>{st} · {STAGES[st]}</b> "
        f"<span class='meta'>({cnt[st]} prompt{'s' if cnt[st] != 1 else ''})</span><br>"
        f"{what} <i>Why it matters:</i> {why}</li>"
        for st, (what, why) in STAGE_INFO.items())
    return ('<h3 style="margin-top:26px">Task categories (the five stages)</h3>'
            '<p class="meta">What each category tests, and why it earns a place in the benchmark.</p>'
            f'<ul style="list-style:none;padding-left:0">{items}</ul>')


# Per-dimension explainer: name -> (max points, is_gate, what it measures, why it matters).
DIM_INFO = {
    "faithfulness": (3, True,
        "Does the answer stick to the facts and clauses actually in the instance — no fabricated "
        "clauses, invented figures, or asserted facts that aren't shown?",
        "A <b>gate</b>: any trip caps the score at 0.40, because hallucinated law is the highest-risk "
        "error. It's near-ceiling (~96%), so the real risk here is judgment, not invention."),
    "directionality": (4, True,
        "Does the answer advocate for the <i>assigned</i> party — never argue the wrong side or add "
        "terms that help the counterparty?",
        "A <b>gate</b>, and the weakest dimension (~74%). Taking and holding the client's side is core "
        "to legal advocacy; it's where weaker models drift (the Qwen/Llama gate trips)."),
    "coverage": (4, False,
        "Did the answer find <i>all</i> the issues or points the gold key expects — completeness across "
        "the required findings?",
        "Measures thoroughness: how much of the expected analysis the model actually surfaces, versus "
        "stopping at the obvious one or two points."),
    "soundness": (3, False,
        "Is the legal reasoning correct — valid analysis and the right conclusions, not just confident "
        "prose?",
        "The second-weakest dimension. Reaching the correct legal answer is where models fail under "
        "fluent writing (e.g. declaring a bridgeable deal 'dead' on E2)."),
    "actionability": (2, False,
        "Is the output usable in practice — deployable clause language, clear recommendations, concrete "
        "next steps?",
        "Captures practical value: whether a lawyer could act on the answer as-is, not just whether it's "
        "analytically right."),
}


def dimensions_html():
    """Overview explainer: each grading dimension + why it matters."""
    items = "".join(
        f"<li style='margin:8px 0'><b>{d.title()}</b> "
        f"<span class='meta'>(max {mx} pt{'s' if mx != 1 else ''}{', GATE' if gate else ''})</span><br>"
        f"{what} <i>Why it matters:</i> {why}</li>"
        for d, (mx, gate, what, why) in DIM_INFO.items())
    return ('<h3 style="margin-top:26px">Grading categories (the five dimensions)</h3>'
            '<p class="meta">Every response is scored on these five dimensions against a gold rubric. '
            'The two <b>gates</b> (Faithfulness, Directionality) cap a tripping response at 0.40.</p>'
            f'<ul style="list-style:none;padding-left:0">{items}</ul>')


V8_PLAN_LOCAL = ROOT / "viewer" / "v8_plan.local.html"  # gitignored: v8 DESIGN rationale stays OUT of the repo (local + Drive only)


def v8_plan_available() -> bool:
    return V8_PLAN_LOCAL.exists()


def next_version_html():
    """Load the v8-plan page body from the local-only file. The design rationale is
    deliberately not committed (kept local + on Google Drive); returns None if absent."""
    return V8_PLAN_LOCAL.read_text() if V8_PLAN_LOCAL.exists() else None

app = Flask(__name__)


def pick_run() -> Path:
    env = os.getenv("LEGALEVAL_RUN")
    if env:
        return Path(env) if Path(env).is_absolute() else ROOT / env
    runs = ROOT / "runs"
    cand = [d for d in runs.glob("*") if (d / "responses").is_dir() and (d / "grades" / JUDGE).is_dir()]
    return max(cand, key=lambda d: len(list((d / "responses").glob("*.json")))) if cand else None


def load_suite():
    s = json.loads(SUITE.read_text())
    return s, {p["id"]: p for p in s["prompts"]}, [p["id"] for p in s["prompts"]]


def load_run(run: Path):
    resp, grades, cells = defaultdict(dict), defaultdict(dict), {}
    if run:
        for f in (run / "responses").glob("*.json"):
            r = json.loads(f.read_text()); resp[r["prompt_id"]][r["provider"]] = r
        for f in (run / "grades" / JUDGE).glob("*.json"):
            d = json.loads(f.read_text()); grades[d["prompt_id"]][d["provider"]] = d
        csvp = ROOT / "results" / f"{run.name}_{JUDGE}.csv"
        if csvp.exists():
            for row in csv.DictReader(csvp.open()):
                cells[(row["prompt_id"], row["provider"])] = row
    return resp, grades, cells


def rubric_path(pid, pmeta):
    return ROOT / "suite" / pmeta[pid].get("rubric_file", f"rubrics/{pid}.json")


def rubric_text(pid, pmeta):
    p = rubric_path(pid, pmeta)
    return json.loads(p.read_text()).get("rubric_markdown", "") if p.exists() else ""


BASE = """
<!doctype html><html><head><meta charset="utf-8"><title>LegalEval Viewer</title>
<style>
 :root{--bd:#e2e5ea;--mut:#6b7280;--ac:#2563eb;}
 *{box-sizing:border-box} body{margin:0;font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;color:#111}
 .wrap{display:flex;min-height:100vh}
 .side{width:250px;flex:0 0 250px;border-right:1px solid var(--bd);padding:14px;position:sticky;top:0;height:100vh;overflow:auto;background:#fafbfc}
 .side h1{font-size:16px;margin:.2em 0 .6em} .side a{display:block;padding:4px 8px;border-radius:6px;color:#222;text-decoration:none;font-size:13.5px}
 .side a:hover{background:#eef2ff} .side a.on{background:#dbeafe;font-weight:600}
 .side .stg{margin:10px 0 3px;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}
 .main{flex:1;padding:24px 32px;max-width:1100px}
 .crumb{color:var(--mut);font-size:13px;margin-bottom:4px}
 h2{margin:.1em 0 .4em} .meta{color:var(--mut);font-size:13.5px;margin-bottom:14px}
 table{border-collapse:collapse;width:100%;margin:10px 0;font-size:13.5px}
 th,td{border:1px solid var(--bd);padding:6px 9px;text-align:left} th{background:#f3f4f6}
 .badge{display:inline-block;padding:1px 8px;border-radius:20px;font-size:12px;font-weight:600}
 .b-ok{background:#dcfce7;color:#166534} .b-mid{background:#fef9c3;color:#854d0e} .b-bad{background:#fee2e2;color:#991b1b}
 .modelnav{position:sticky;top:0;background:#fff;padding:10px 0;border-bottom:1px solid var(--bd);margin-bottom:6px;z-index:5;display:flex;flex-wrap:wrap;gap:6px;align-items:center}
 .modelnav button{border:1px solid var(--bd);background:#f8fafc;border-radius:20px;padding:4px 11px;font-size:12.5px;cursor:pointer}
 .modelnav button:hover{background:#eef2ff;border-color:#c7d2fe}
 .card{border:1px solid var(--bd);border-radius:10px;margin:12px 0;overflow:hidden;scroll-margin-top:60px}
 .card .hd{display:flex;align-items:center;gap:10px;padding:10px 14px;background:#f8fafc;border-bottom:1px solid transparent;cursor:pointer}
 .card.open .hd{border-bottom-color:var(--bd)}
 .card .hd b{font-size:15px} .card .hd .caret{color:var(--mut);font-size:12px}
 .card .bd{padding:14px 16px;display:none} .card.open .bd{display:block}
 .dimchip{font-size:11.5px;color:#374151;background:#eef2f7;border-radius:6px;padding:1px 6px;margin-left:2px}
 .resp{font-size:14px} .resp h1,.resp h2,.resp h3{font-size:15px;margin:.7em 0 .3em} .resp table{font-size:12.5px}
 .resp pre{background:#f6f8fa;padding:8px;border-radius:6px;overflow:auto}
 .rationale{background:#f5f8ff;border:1px solid #d7e3ff;border-radius:10px;padding:12px 14px;margin:6px 0 14px;font-size:13.5px}
 .rationale h4{margin:.1em 0 .5em;font-size:13.5px} .gate{margin:3px 0}
 .g-pass{color:#166534;font-weight:600} .g-trip{color:#991b1b;font-weight:600}
 .sj{margin:3px 0 3px 4px;padding-left:10px;border-left:2px solid #e5e7eb}
 .v-met{color:#166534} .v-partial{color:#854d0e} .v-not_met{color:#991b1b} .v-not_applicable{color:#9ca3af}
 .quote{color:#475569;font-style:italic}
 textarea{width:100%;font:13px/1.5 ui-monospace,Menlo,monospace;padding:10px;border:1px solid var(--bd);border-radius:8px}
 .btn{background:var(--ac);color:#fff;border:0;padding:8px 16px;border-radius:8px;font-size:14px;cursor:pointer}
 .saved{color:#16a34a;font-weight:600;margin-left:10px}
 details>summary{cursor:pointer;font-weight:600;margin:6px 0;font-size:13px}
 .pill{font-size:11px;color:var(--mut);border:1px solid var(--bd);border-radius:20px;padding:1px 8px}
</style></head><body><div class="wrap">
<nav class="side">
 <h1>⚖️ LegalEval</h1>
 <a href="/" class="{{ 'on' if page=='ov' }}">Overview & results</a>
 {% if has_next_page %}<a href="/next" class="{{ 'on' if page=='next' }}">Next version (v8) plan</a>{% endif %}
 {% for st,sname in stages.items() %}<div class="stg">{{st}} · {{sname}}</div>
   {% for pid in order if pid.startswith(st) %}
     <a href="/prompt/{{pid}}" class="{{ 'on' if pid==cur }}">{{pid}} · {{pmeta[pid].name}}</a>
   {% endfor %}{% endfor %}
 <div class="stg" style="margin-top:18px">Run</div><div class="pill">{{run_name}}</div>
</nav>
<main class="main">{{ body|safe }}</main>
</div>
<script>
 function setCard(i,open){var c=document.getElementById('c'+i); if(c) c.classList.toggle('open',open);}
 function toggle(i){var c=document.getElementById('c'+i); if(c) c.classList.toggle('open');}
 function jump(i){setCard(i,true); document.getElementById('c'+i).scrollIntoView({behavior:'smooth',block:'start'});}
 function expandAll(){document.querySelectorAll('.card').forEach(c=>c.classList.add('open'));}
 function collapseAll(){document.querySelectorAll('.card').forEach(c=>c.classList.remove('open'));}
 async function save(pid){
   const fd={prompt_text:document.getElementById('pt').value, rubric:document.getElementById('rb').value};
   const r=await fetch('/prompt/'+pid+'/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(fd)});
   document.getElementById('savemsg').textContent = r.ok ? '✓ saved' : '✗ error';
 }
</script></body></html>
"""


def badge(norm, tripped):
    cls = "b-ok" if norm >= 0.85 else ("b-mid" if norm >= 0.6 else "b-bad")
    return f'<span class="badge {cls}">{norm:.2f}{" ⚠gate" if tripped else ""}</span>'


DIM_MAX = {"faithfulness": 3, "directionality": 4, "coverage": 4, "soundness": 3, "actionability": 2}


def struggle_stats(grades, cells, pmeta):
    """Compute the struggle/focus metrics from one run. Shared by the GUI and the
    standalone report tool so both read the same numbers."""
    def agg(pid, prov):
        return grades.get(pid, {}).get(prov, {}).get("aggregate", {})
    prompts = sorted({p for p in pmeta})
    n_prompts = len(prompts)
    # hardest quality = mean as % of dimension max, ONLY over prompts where the dimension is graded
    qpct = {}
    for d in DIMS:
        applic = [p for p in prompts if max((agg(p, m).get(d, 0) or 0) for m in MODELS) > 0]
        vals = [agg(p, m).get(d, 0) or 0 for p in applic for m in MODELS if (p, m) in cells]
        if vals:
            qpct[d] = (sum(vals) / len(vals) / DIM_MAX[d] * 100, len(applic))
    qsorted = sorted(qpct.items(), key=lambda kv: kv[1][0])  # low (=hard) first
    # per-task mean + model spread
    byp = defaultdict(list)
    for (pid, prov), r in cells.items():
        byp[pid].append(float(r["norm"]))
    hard = sorted(byp.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))
    spread = {pid: (max(v) - min(v)) for pid, v in byp.items() if len(v) > 1}
    # gate trips overall + per task
    dt = sum(1 for r in cells.values() if "directionality" in (r["gates_tripped"] or ""))
    ft = sum(1 for r in cells.values() if "faithfulness" in (r["gates_tripped"] or ""))
    tgate = defaultdict(int)
    for (pid, prov), r in cells.items():
        if r["gates_tripped"]:
            tgate[pid] += 1
    return {
        "qsorted": qsorted, "qpct": qpct, "n_prompts": n_prompts,
        "hard": hard, "byp": byp, "spread": spread,
        "dt": dt, "ft": ft, "tgate": tgate, "pmeta": pmeta,
    }


def focus_recs(s):
    """Derive 'what to focus on next' bullets (as (title, body) tuples) from struggle_stats."""
    pmeta = s["pmeta"]
    weak = [d for d, _ in s["qsorted"][:2]]
    weak_names = " + ".join(d.title() for d in weak)
    ceiling = [d.title() for d, (pct, _) in s["qpct"].items() if pct >= 90]
    ceil_names = ", ".join(ceiling) if ceiling else "the top dimensions"
    discr = sorted(s["spread"].items(), key=lambda kv: -kv[1])[:4]
    discr_str = ", ".join(f"{pid} (Δ{v:.2f})" for pid, v in discr)
    gate_tasks = sorted(s["tgate"].items(), key=lambda kv: -kv[1])
    gate_str = ", ".join(f"{pid} ({c} trip{'s' if c > 1 else ''})" for pid, c in gate_tasks) or "none this run"
    hp, hv = s["hard"][0]
    hmean = sum(hv) / len(hv)
    return [
        ("More adversarial / directional tasks",
         f"The gate trips ({gate_str}) and the widest model spread ({discr_str}) are on the "
         f"advocate-a-side prompts — the most <i>discriminating</i> items. More C1/C2-style "
         f"“redline toward your client” and E2-style verdict prompts sharpen ranking power."),
        (f"Expand the hardest family ({hp} · {pmeta[hp]['name']}, mean {hmean:.2f})",
         "It's the lowest-scoring task — an issue-spotting failure where models treat every gap as "
         "harmful, missing that some <i>absent</i> clauses are neutral-to-favorable for the client. "
         "Build 2–3 more prompts that hinge on whether an omission helps or hurts your side."),
        (f"Stress {weak_names}",
         "The two weakest dimensions. Build holistic-judgment prompts (E2-style) that force the right "
         "overall conclusion under fluent prose — where confident writing masks a wrong verdict."),
        (f"De-prioritize near-ceiling dimensions ({ceil_names})",
         "Near-ceiling across all models — high coverage but low discrimination. Pure extraction / "
         "drafting rarely separates models, so it's low-value for ranking."),
    ]


def struggle_html(grades, cells, pmeta):
    """Live 'what the models struggled on' + 'what to focus on next', computed from this run."""
    s = struggle_stats(grades, cells, pmeta)
    np = s["n_prompts"]
    qtab = "".join(f"<tr><td>{d.title()}</td><td>{pct:.0f}%</td><td class='meta'>{n}/{np} prompts</td></tr>"
                   for d, (pct, n) in s["qsorted"])
    ptab = "".join(f"<tr><td>{pid} · {pmeta[pid]['name']}</td><td>{sum(v)/len(v):.2f}</td></tr>"
                   for pid, v in s["hard"][:5])
    dt, ft = s["dt"], s["ft"]
    weak2 = " and ".join(f"<b>{d.title()}</b>" for d, _ in s["qsorted"][:2])
    faith = s["qpct"].get("faithfulness", (0, 0))[0]
    foc = "".join(f"<li><b>{t}.</b> {b}</li>" for t, b in focus_recs(s))
    return f"""
    <h3 style="margin-top:26px">What the models struggled on</h3>
    <div style="display:flex;gap:28px;flex-wrap:wrap">
      <div style="flex:1;min-width:280px">
        <p class="meta" style="margin-bottom:2px"><b>Hardest qualities</b> (mean score as % of that dimension's
        max, over the prompts where it's graded — low = hard)</p>
        <table><tr><th>Dimension</th><th>% of max</th><th>Scope</th></tr>{qtab}</table>
      </div>
      <div style="flex:1;min-width:280px">
        <p class="meta" style="margin-bottom:2px"><b>Hardest tasks</b> (mean normalized score)</p>
        <table><tr><th>Prompt</th><th>Score</th></tr>{ptab}</table>
      </div>
    </div>
    <p style="margin-top:10px"><b>The pattern.</b> Models are strongest where the work is mechanical
    (<b>Faithfulness {faith:.0f}%</b> — they rarely fabricate; extraction & drafting near-ceiling) and weakest where
    it needs <b>legal judgment</b>: {weak2} (taking and holding the client's side; reaching the right legal
    conclusion). The hardest tasks are issue-spotting, adversarial redlining, and holistic reasoning — not
    extraction or drafting.</p>
    <p><b>Recurring failure modes.</b></p>
    <ul>
      <li><b>Directional drift</b> — on adversarial tasks, weaker models argue the wrong party's side or restore
      adverse terms ({dt} directionality gate trips). Mostly Qwen & Llama; the top three never tripped.</li>
      <li><b>The A1 "bucket split"</b> — every model misses that some <i>absent</i> clauses are
      neutral-to-favorable for the client, treating all gaps as harmful.</li>
      <li><b>Wrong legal conclusion under fluent prose</b> — on E2 most models declared a bridgeable deal "dead"
      (a Soundness failure the confident writing masks).</li>
      <li><b>Frame-holding</b> — keeping the assigned advocate role across a long, multi-part task is where
      consistency breaks down.</li>
      <li><b>Fabrication is rare</b> — only {ft} faithfulness gate trips; hallucinated clauses/figures are NOT the
      main risk here. The risk is judgment, not invention.</li>
    </ul>
    <h3 style="margin-top:26px">What to focus prompts on next</h3>
    <p class="meta">Derived from this run — where scores collapse and where models separate.</p>
    <ol>{foc}</ol>"""


def render(body, **kw):
    suite, pmeta, order = load_suite()
    return render_template_string(BASE, body=body, stages=STAGES, order=order, pmeta=pmeta,
                                  run_name=RUN.name if RUN else "—",
                                  has_next_page=v8_plan_available(), **kw)


def rationale_html(pid, pmeta, agg, sample):
    """Show WHY: gate decisions + reasoning, judge summary, per-criterion sub-judgments."""
    parts = ['<div class="rationale"><h4>Why this score</h4>']
    for gate in pmeta[pid].get("gates", []):
        g = agg.get(f"gate_{gate}", {})
        tripped = g.get("tripped")
        reason = (g.get("reasoning") or [""])[0]
        cls = "g-trip" if tripped else "g-pass"
        lab = "TRIPPED" if tripped else "pass"
        hc = " · needs human confirm" if g.get("needs_human_confirm") else ""
        parts.append(f'<div class="gate"><span class="{cls}">{gate.title()} gate: {lab}{hc}</span> — {reason}</div>')
    note = (agg.get("notes") or [""])[0]
    if note:
        parts.append(f'<div style="margin-top:6px"><b>Judge summary.</b> {note}</div>')
    # per-criterion sub-judgments from the (first) judge sample
    if sample:
        rows = []
        for d in DIMS:
            dg = sample.get(d) or {}
            sjs = dg.get("sub_judgments") or []
            if not sjs:
                continue
            rows.append(f'<div style="margin-top:6px"><b>{DIM_ABBR[d]} = {dg.get("score","–")}</b></div>')
            for sj in sjs:
                v = sj.get("verdict", "")
                q = sj.get("evidence_quote")
                qh = f' <span class="quote">“{q[:200]}”</span>' if q else ""
                rows.append(f'<div class="sj"><span class="v-{v}">{v}</span> · {sj.get("criterion","")}{qh}</div>')
        if rows:
            parts.append("<details><summary>Per-criterion breakdown (evidence)</summary>" + "".join(rows) + "</details>")
    parts.append("</div>")
    return "".join(parts)


@app.route("/")
def index():
    suite, pmeta, order = load_suite()
    resp, grades, cells = load_run(RUN)
    by, gt, n = defaultdict(list), defaultdict(int), defaultdict(int)
    for (pid, prov), r in cells.items():
        by[prov].append(float(r["norm"])); n[prov] += 1
        if r["gates_tripped"]:
            gt[prov] += 1
    rank = sorted([m for m in MODELS if n[m]], key=lambda m: -sum(by[m]) / n[m])
    rows = "".join(f"<tr><td>{i+1}</td><td>{LABEL[m]}</td><td>{sum(by[m])/n[m]:.3f}</td>"
                   f"<td>{gt[m]}/{n[m]}</td></tr>" for i, m in enumerate(rank))
    body = f"""
    <div class="crumb">Overview</div><h2>LegalEval v7 — automated legal benchmark</h2>
    <p class="meta">14 prompts across 5 stages (189 pts) · 5 models under test · Opus 4.8 judge (k=1) · rubric {suite['rubric_version']}.</p>
    <p><b>How it works.</b> Each model gets the bare prompt <i>incognito</i> (no system prompt, tools, or memory).
    The Opus 4.8 judge scores 5 dimensions (Faithfulness, Directionality, Coverage, Soundness, Actionability)
    against a gold rubric; code normalizes to 0–1 and <b>caps any gate-tripping response at 0.40</b> (a gate trips on
    fabrication or advocating the wrong party). Pick a prompt on the left to see all five responses + their grades and rationale.</p>
    {categories_html(order, pmeta)}
    {dimensions_html()}
    <h3 style="margin-top:26px">Overall ranking (mean normalized score, after gate cap)</h3>
    <table><tr><th>#</th><th>Model</th><th>Mean</th><th>Gate trips</th></tr>{rows}</table>
    {struggle_html(grades, cells, pmeta)}
    <p class="meta">⚠ k=1 single judge sample; margins overlap within CIs. Opus grading Claude Sonnet is same-family
    (self-grading caveat). Edit prompts/rubrics from any prompt page.</p>
    """
    return render(body, page="ov", cur=None)


@app.route("/next")
def next_version():
    body = next_version_html()
    if body is None:
        abort(404)
    return render(body, page="next", cur=None)


@app.route("/prompt/<pid>")
def prompt_view(pid):
    suite, pmeta, order = load_suite()
    if pid not in pmeta:
        abort(404)
    resp, grades, cells = load_run(RUN)
    m = pmeta[pid]
    srows, nav, cards = "", "", ""
    for i, prov in enumerate(MODELS):
        c = cells.get((pid, prov))
        grade = grades.get(pid, {}).get(prov, {})
        agg = grade.get("aggregate", {})
        samples = grade.get("samples") or []
        sample = samples[0] if samples else None
        ds = " · ".join(f"{DIM_ABBR[d][:1]}:{agg.get(d,'–')}" for d in DIMS)
        b = badge(float(c["norm"]), bool(c["gates_tripped"])) if c else ""
        if c:
            srows += (f"<tr><td><a href='#c{i}' onclick=\"jump({i})\">{LABEL[prov]}</a></td><td>{b}</td>"
                      f"<td>{c['raw']}/{c['max']}</td><td class='meta'>{ds}</td></tr>")
        nav += f'<button onclick="jump({i})">{LABEL[prov]} {b}</button>'
        r = resp.get(pid, {}).get(prov)
        html = md.markdown(r["response_text"], extensions=["tables", "fenced_code"]) if r else "<i>[no response]</i>"
        chips = "".join(f'<span class="dimchip">{DIM_ABBR[d]} {agg.get(d,"–")}</span>' for d in DIMS) if agg else ""
        rat = rationale_html(pid, pmeta, agg, sample) if agg else ""
        cards += f"""
        <div class="card" id="c{i}">
          <div class="hd" onclick="toggle({i})"><span class="caret">▸</span><b>{LABEL[prov]}</b> {b}
            <span style="margin-left:6px">{chips}</span>
            <span class="pill" style="margin-left:auto">{(len(r['response_text']) if r else 0)} chars</span></div>
          <div class="bd">{rat}
            <details><summary>Full response</summary><div class="resp">{html}</div></details>
          </div>
        </div>"""
    body = f"""
    <div class="crumb">{m['stage']} · {STAGES.get(pid[0],'')}</div>
    <h2>{pid} · {m.get('name','')}</h2>
    <p class="meta">/{m.get('max_points','?')} pts · gates: {', '.join(m.get('gates',[]))} · source: {m.get('source_type','?')}</p>
    <table><tr><th>Model</th><th>Score</th><th>Raw/Max</th><th>Dimensions (F·D·C·S·A)</th></tr>{srows}</table>
    <details><summary>✎ Edit prompt &amp; rubric (saves to suite/)</summary>
      <p style="margin:.4em 0;color:#6b7280">Prompt text</p>
      <textarea id="pt" rows="10">{(m.get('prompt_text') or '')}</textarea>
      <p style="margin:.6em 0 .4em;color:#6b7280">Rubric (gold key)</p>
      <textarea id="rb" rows="14">{rubric_text(pid, pmeta)}</textarea>
      <p style="margin-top:10px"><button class="btn" onclick="save('{pid}')">Save</button>
      <span id="savemsg" class="saved"></span></p>
    </details>
    <h3 style="margin-top:22px">All model responses & grading rationale</h3>
    <div class="modelnav"><button onclick="expandAll()">⊕ Expand all</button>
      <button onclick="collapseAll()">⊖ Collapse all</button>
      <span style="color:#9ca3af;font-size:12px;margin:0 4px">jump:</span>{nav}</div>
    {cards}
    """
    return render(body, page="pr", cur=pid)


@app.route("/prompt/<pid>/save", methods=["POST"])
def save_prompt(pid):
    suite, pmeta, order = load_suite()
    if pid not in pmeta:
        abort(404)
    data = request.get_json(force=True)
    full = json.loads(SUITE.read_text())
    for p in full["prompts"]:
        if p["id"] == pid:
            p["prompt_text"] = data.get("prompt_text", p.get("prompt_text"))
    SUITE.write_text(json.dumps(full, indent=2))
    rp = rubric_path(pid, pmeta)
    if rp.exists() and "rubric" in data:
        rj = json.loads(rp.read_text()); rj["rubric_markdown"] = data["rubric"]
        rp.write_text(json.dumps(rj, indent=2))
    return {"ok": True}


RUN = pick_run()

if __name__ == "__main__":
    print(f"LegalEval viewer — run dir: {RUN}")
    app.run(debug=True, port=int(os.getenv("PORT", "5000")))
