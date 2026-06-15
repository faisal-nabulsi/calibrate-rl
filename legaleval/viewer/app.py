"""LegalEval viewer/editor — a local web UI to browse prompts, responses, and grades.

Run:
    cd legaleval && .venv/bin/python -m viewer.app
    # then open http://127.0.0.1:5000

- Overview tab: what LegalEval is + the overall results table.
- Pick a prompt (sidebar, grouped by stage) -> see ALL five models' responses together,
  each with its grade (dimension scores, gate status, judge notes).
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
from flask import Flask, abort, redirect, render_template_string, request, url_for

ROOT = Path(__file__).resolve().parent.parent
SUITE = ROOT / "suite" / "prompts.json"
RUBRICS = ROOT / "suite" / "rubrics"
JUDGE = "claude-opus-4-8"
MODELS = ["claude-sonnet-4-6", "gpt-5.5", "gemini-3.5-flash", "qwen-3.7-plus", "llama-4-maverick"]
LABEL = {"claude-sonnet-4-6": "Claude Sonnet 4.6", "gpt-5.5": "GPT-5.5",
         "gemini-3.5-flash": "Gemini 3.5 Flash", "qwen-3.7-plus": "Qwen 3.7 Plus",
         "llama-4-maverick": "Llama 4 Maverick"}
DIMS = ["faithfulness", "directionality", "coverage", "soundness", "actionability"]
STAGES = {"A": "Issue-spotting", "B": "Summarization & Extraction", "C": "Redlining",
          "D": "Drafting", "E": "Negotiation"}

app = Flask(__name__)


def pick_run() -> Path:
    env = os.getenv("LEGALEVAL_RUN")
    if env:
        return Path(env) if Path(env).is_absolute() else ROOT / env
    runs = ROOT / "runs"
    cand = [d for d in runs.glob("*") if (d / "responses").is_dir() and (d / "grades" / JUDGE).is_dir()]
    return max(cand, key=lambda d: len(list((d / "responses").glob("*.json"))) ) if cand else None


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
    rf = pmeta[pid].get("rubric_file", f"rubrics/{pid}.json")
    return ROOT / "suite" / rf


def rubric_text(pid, pmeta):
    p = rubric_path(pid, pmeta)
    if p.exists():
        return json.loads(p.read_text()).get("rubric_markdown", "")
    return ""


BASE = """
<!doctype html><html><head><meta charset="utf-8"><title>LegalEval Viewer</title>
<style>
 :root{--bd:#e2e5ea;--mut:#6b7280;--ac:#2563eb;--ok:#16a34a;--bad:#dc2626;}
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
 .card{border:1px solid var(--bd);border-radius:10px;margin:14px 0;overflow:hidden}
 .card .hd{display:flex;align-items:center;gap:10px;padding:10px 14px;background:#f8fafc;border-bottom:1px solid var(--bd);cursor:pointer}
 .card .hd b{font-size:15px} .card .bd{padding:14px 16px}
 .resp{font-size:14px} .resp h1,.resp h2,.resp h3{font-size:15px;margin:.7em 0 .3em} .resp table{font-size:12.5px}
 .resp pre{background:#f6f8fa;padding:8px;border-radius:6px;overflow:auto}
 .note{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:8px 12px;margin-top:10px;font-size:13px}
 .dims{font-size:12.5px;color:var(--mut)} textarea{width:100%;font:13px/1.5 ui-monospace,Menlo,monospace;padding:10px;border:1px solid var(--bd);border-radius:8px}
 .btn{background:var(--ac);color:#fff;border:0;padding:8px 16px;border-radius:8px;font-size:14px;cursor:pointer}
 .btn.sec{background:#eef2ff;color:var(--ac)} .saved{color:var(--ok);font-weight:600;margin-left:10px}
 details>summary{cursor:pointer;font-weight:600;margin:8px 0}
 .pill{font-size:11px;color:var(--mut);border:1px solid var(--bd);border-radius:20px;padding:1px 8px}
</style></head><body><div class="wrap">
<nav class="side">
 <h1>⚖️ LegalEval</h1>
 <a href="{{ url_for('index') }}" class="{{ 'on' if page=='ov' }}">Overview & results</a>
 {% for st,sname in stages.items() %}<div class="stg">{{st}} · {{sname}}</div>
   {% for pid in order if pid.startswith(st) %}
     <a href="{{ url_for('prompt_view', pid=pid) }}" class="{{ 'on' if pid==cur }}">{{pid}} · {{pmeta[pid].name}}</a>
   {% endfor %}{% endfor %}
 <div class="stg" style="margin-top:18px">Run</div><div class="pill">{{run_name}}</div>
</nav>
<main class="main">{{ body|safe }}</main>
</div>
<script>
 function tog(id){var e=document.getElementById(id);e.style.display=e.style.display==='none'?'block':'none';}
 async function save(pid){
   const fd={prompt_text:document.getElementById('pt').value, rubric:document.getElementById('rb').value};
   const r=await fetch('/prompt/'+pid+'/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(fd)});
   document.getElementById('savemsg').textContent = r.ok ? '✓ saved' : '✗ error';
 }
</script></body></html>
"""


def badge(norm, tripped):
    cls = "b-ok" if norm >= 0.85 else ("b-mid" if norm >= 0.6 else "b-bad")
    txt = f"{norm:.2f}" + (" ⚠gate" if tripped else "")
    return f'<span class="badge {cls}">{txt}</span>'


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
    fabrication or advocating the wrong party). Pick a prompt on the left to see all five responses + their grades.</p>
    <h3>Overall ranking (mean normalized score, after gate cap)</h3>
    <table><tr><th>#</th><th>Model</th><th>Mean</th><th>Gate trips</th></tr>{rows}</table>
    <p class="meta">⚠ k=1 single judge sample; margins overlap within CIs. Opus grading Claude Sonnet is same-family
    (self-grading caveat). Edit prompts/rubrics from any prompt page.</p>
    """
    return render_template_string(BASE, body=body, page="ov", cur=None, stages=STAGES,
                                  order=order, pmeta=pmeta, run_name=RUN.name if RUN else "—")


@app.route("/prompt/<pid>")
def prompt_view(pid):
    suite, pmeta, order = load_suite()
    if pid not in pmeta:
        abort(404)
    resp, grades, cells = load_run(RUN)
    m = pmeta[pid]
    # per-prompt score table
    srows = ""
    for prov in MODELS:
        c = cells.get((pid, prov)); a = grades.get(pid, {}).get(prov, {}).get("aggregate", {})
        ds = " · ".join(f"{d[:1].upper()}:{a.get(d,'–')}" for d in DIMS)
        if c:
            srows += (f"<tr><td>{LABEL[prov]}</td><td>{badge(float(c['norm']), bool(c['gates_tripped']))}</td>"
                      f"<td>{c['raw']}/{c['max']}</td><td class='dims'>{ds}</td></tr>")
    # response cards (all five together)
    cards = ""
    for i, prov in enumerate(MODELS):
        r = resp.get(pid, {}).get(prov); c = cells.get((pid, prov))
        a = grades.get(pid, {}).get(prov, {}).get("aggregate", {})
        b = badge(float(c["norm"]), bool(c["gates_tripped"])) if c else ""
        html = md.markdown(r["response_text"], extensions=["tables", "fenced_code"]) if r else "<i>[no response]</i>"
        note = (a.get("notes") or [""])[0]
        notehtml = f'<div class="note"><b>Judge:</b> {note}</div>' if note else ""
        cards += f"""
        <div class="card">
          <div class="hd" onclick="tog('r{i}')"><b>{LABEL[prov]}</b> {b}
            <span class="pill" style="margin-left:auto">{(len(r['response_text']) if r else 0)} chars · click to toggle</span></div>
          <div class="bd" id="r{i}"><div class="resp">{html}</div>{notehtml}</div>
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
    <h3 style="margin-top:22px">All model responses</h3>
    {cards}
    """
    return render_template_string(BASE, body=body, page="pr", cur=pid, stages=STAGES,
                                  order=order, pmeta=pmeta, run_name=RUN.name if RUN else "—")


@app.route("/prompt/<pid>/save", methods=["POST"])
def save_prompt(pid):
    suite, pmeta, order = load_suite()
    if pid not in pmeta:
        abort(404)
    data = request.get_json(force=True)
    # prompt_text -> prompts.json
    full = json.loads(SUITE.read_text())
    for p in full["prompts"]:
        if p["id"] == pid:
            p["prompt_text"] = data.get("prompt_text", p.get("prompt_text"))
    SUITE.write_text(json.dumps(full, indent=2))
    # rubric -> rubrics/<id>.json
    rp = rubric_path(pid, pmeta)
    if rp.exists() and "rubric" in data:
        rj = json.loads(rp.read_text()); rj["rubric_markdown"] = data["rubric"]
        rp.write_text(json.dumps(rj, indent=2))
    return {"ok": True}


RUN = pick_run()

if __name__ == "__main__":
    print(f"LegalEval viewer — run dir: {RUN}")
    app.run(debug=True, port=int(os.getenv("PORT", "5000")))
