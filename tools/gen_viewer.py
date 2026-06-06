#!/usr/bin/env python3
# Builds rollout_viewer.html from the extracted verbatim transcripts.
import os, re, json, html

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "verbatim_transcripts.txt")   # extracted from CalibrateRL_Verbatim_Transcripts pdf
OUT = os.path.join(HERE, "rollout_viewer.html")

raw = open(SRC, encoding="utf-8").read()

HEADER_RE = re.compile(
    r'(\d)/8\s+correct\s+(\S+)\s+gold=(-?[\d/.]+)\s+grades=\[([^\]]+)\]',
    re.S,
)
ROLLOUT_RE = re.compile(
    r'---\s*rollout\s+(\d+)\s*\(graded\s+(CORRECT|WRONG)\)\s*---'
)
ZONE_WORDS = ("GOLDILOCKS", "TOO_HARD", "TOO_EASY", "BORDERLINE")


def clean_text(t):
    """Collapse one-word-per-line PDF text into readable prose."""
    # Strip trailing underscore artifact rows
    t = re.sub(r'_{5,}', ' ', t)
    # Remove stray zone words anywhere (they are artifacts in bodies)
    for z in ZONE_WORDS:
        t = re.sub(r'\b' + z + r'\b', ' ', t)
    # Collapse all whitespace runs into single spaces
    t = re.sub(r'\s+', ' ', t).strip()
    # Re-introduce line breaks before structural markers for readability.
    # Before display-math open/close and inline transitions.
    t = re.sub(r'\s*\\\[\s*', '\n\\\\[ ', t)
    t = re.sub(r'\s*\\\]\s*', ' \\\\]\n', t)
    # Before "Step N", "### ", numbered "N." starts, Therefore/Thus/So,
    t = re.sub(r'\s+(Step\s+\d+)', r'\n\1', t)
    t = re.sub(r'\s+(###+\s)', r'\n\1', t)
    t = re.sub(r'\s+(Therefore[,\b])', r'\n\1', t)
    t = re.sub(r'\s+(Thus[,\b])', r'\n\1', t)
    t = re.sub(r'\s+(So,)', r'\n\1', t)
    t = re.sub(r'\s+(Finally,)', r'\n\1', t)
    t = re.sub(r'\s+(Hence[,\b])', r'\n\1', t)
    # numbered list markers " 1. " / " 2. " at start of a clause
    t = re.sub(r'(?<=[.\]])\s+(\d{1,2}\.\s)', r'\n\1', t)
    # collapse 3+ newlines
    t = re.sub(r'\n{3,}', '\n\n', t)
    t = re.sub(r'[ \t]+\n', '\n', t)
    t = re.sub(r'\n[ \t]+', '\n', t)
    return t.strip()


def infer_zone(text_before, n_correct):
    # look at last zone word appearing in the preceding text
    found = None
    for m in re.finditer(r'(GOLDILOCKS|TOO_HARD|TOO_EASY|BORDERLINE)', text_before):
        found = m.group(1)
    if found:
        return found.lower()
    if n_correct == 0:
        return "too_hard"
    if n_correct == 8:
        return "too_easy"
    return ""


# Find all header matches with their spans
headers = list(HEADER_RE.finditer(raw))
problems = []

for i, h in enumerate(headers):
    n_correct = int(h.group(1))
    concept = h.group(2)
    gold = h.group(3)
    grades_raw = h.group(4)
    grades = [g.strip() for g in grades_raw.split(",") if g.strip()]

    start = h.end()
    end = headers[i + 1].start() if i + 1 < len(headers) else len(raw)
    block = raw[start:end]

    # text before header (limited window) for zone inference
    pre_start = headers[i - 1].end() if i > 0 else 0
    pre = raw[pre_start:h.start()]
    zone = infer_zone(pre, n_correct)

    # Problem statement: text from "PROBLEM" up to first rollout marker
    statement = ""
    first_roll = ROLLOUT_RE.search(block)
    head_region = block[: first_roll.start()] if first_roll else block
    pm = re.search(r'PROBLEM\b(.*)', head_region, re.S)
    if pm:
        statement = clean_text(pm.group(1))

    # Rollouts
    rolls = []
    rmatches = list(ROLLOUT_RE.finditer(block))
    for j, rm in enumerate(rmatches):
        rnum = int(rm.group(1))
        verdict = rm.group(2)
        b_start = rm.end()
        b_end = rmatches[j + 1].start() if j + 1 < len(rmatches) else len(block)
        body = clean_text(block[b_start:b_end])
        rolls.append({"n": rnum, "verdict": verdict, "body": body})

    problems.append({
        "concept": concept,
        "n_correct": n_correct,
        "gold": gold,
        "zone": zone,
        "grades": grades,
        "statement": statement,
        "rollouts": rolls,
    })

total_rollouts = sum(len(p["rollouts"]) for p in problems)
concepts = sorted(set(p["concept"] for p in problems))

print(f"Problems: {len(problems)}")
print(f"Rollouts: {total_rollouts}")
print(f"Concepts ({len(concepts)}): {concepts}")
for p in problems:
    print(f"  {p['n_correct']}/8 {p['zone']:12s} {p['concept']:30s} gold={p['gold']} rolls={len(p['rollouts'])}")

data_json = json.dumps({"problems": problems}, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Qwen2.5-7B Math Rollout Viewer</title>
<script>
window.MathJax = {
  tex: { inlineMath: [['\\(','\\)']], displayMath: [['\\[','\\]']] },
  options: { skipHtmlTags: ['script','noscript','style','textarea','pre'] }
};
</script>
<script async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-chtml.min.js"></script>
<style>
:root{
  --bg:#f7f8fa; --panel:#ffffff; --ink:#1c1e21; --muted:#65676b;
  --border:#e2e4e8; --accent:#2563eb;
  --green:#16a34a; --red:#dc2626; --blue:#2563eb; --gray:#6b7280;
}
*{box-sizing:border-box;}
body{
  margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  background:var(--bg); color:var(--ink); font-size:15px; line-height:1.6;
}
header.top{
  background:var(--panel); border-bottom:1px solid var(--border);
  padding:12px 20px; display:flex; align-items:center; gap:16px; flex-wrap:wrap;
  position:sticky; top:0; z-index:10;
}
header.top h1{font-size:17px; margin:0; font-weight:650;}
.counts{color:var(--muted); font-size:13px;}
.controls{display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-left:auto;}
.controls input[type=text]{
  padding:7px 10px; border:1px solid var(--border); border-radius:7px; font-size:14px; width:230px;
}
.controls select{padding:7px 8px; border:1px solid var(--border); border-radius:7px; font-size:13px;}
.layout{display:flex; align-items:stretch;}
aside{
  width:330px; min-width:330px; border-right:1px solid var(--border);
  background:var(--panel); height:calc(100vh - 56px); overflow-y:auto;
}
.plist-item{
  padding:10px 14px; border-bottom:1px solid var(--border); cursor:pointer;
}
.plist-item:hover{background:#f0f3f8;}
.plist-item.active{background:#e8f0fe;}
.plist-item .row1{display:flex; align-items:center; gap:8px; margin-bottom:3px;}
.plist-item .concept{font-weight:600; font-size:14px; word-break:break-word;}
.plist-item .meta{font-size:12px; color:var(--muted);}
.chip{display:inline-block; padding:2px 7px; border-radius:10px; font-size:11px; font-weight:600; color:#fff; white-space:nowrap;}
.chip.too_easy{background:var(--green);}
.chip.too_hard{background:var(--red);}
.chip.goldilocks{background:var(--blue);}
.chip.borderline{background:var(--gray);}
.chip.unknown{background:#9ca3af;}
.score{font-size:12px; font-weight:700; color:var(--muted); margin-left:auto;}
main{flex:1; height:calc(100vh - 56px); overflow-y:auto; padding:24px 28px;}
.reader{max-width:820px; margin:0 auto;}
.phead{margin-bottom:18px; padding-bottom:14px; border-bottom:1px solid var(--border);}
.phead h2{margin:0 0 8px; font-size:20px;}
.phead .metaline{font-size:13px; color:var(--muted); display:flex; gap:14px; flex-wrap:wrap; align-items:center;}
.statement{background:#f0f4ff; border:1px solid #d8e2fb; border-radius:8px; padding:12px 16px; margin:14px 0; font-size:15px;}
.statement .lbl{font-size:11px; font-weight:700; color:var(--accent); text-transform:uppercase; letter-spacing:.05em; display:block; margin-bottom:4px;}
.card{
  background:var(--panel); border:1px solid var(--border); border-radius:9px;
  margin:14px 0; overflow:hidden;
}
.card-head{
  display:flex; align-items:center; gap:10px; padding:10px 14px; cursor:pointer;
  background:#fafbfc; border-bottom:1px solid var(--border); user-select:none;
}
.card.collapsed .card-head{border-bottom:none;}
.card-head .rn{font-weight:650; font-size:14px;}
.badge{padding:2px 9px; border-radius:6px; font-size:11px; font-weight:700; color:#fff;}
.badge.CORRECT{background:var(--green);}
.badge.WRONG{background:var(--red);}
.toggle{margin-left:auto; color:var(--muted); font-size:13px;}
.card-body{padding:14px 18px; font-size:15px; white-space:pre-wrap; word-wrap:break-word; overflow-x:auto;}
.card.collapsed .card-body{display:none;}
.empty{color:var(--muted); text-align:center; margin-top:80px; font-size:15px;}
.hidden{display:none !important;}
</style>
</head>
<body>
<header class="top">
  <h1>Qwen2.5-7B Math Rollouts</h1>
  <span class="counts" id="counts"></span>
  <div class="controls">
    <input type="text" id="search" placeholder="Search concept or body text...">
    <select id="zoneFilter">
      <option value="">All zones</option>
      <option value="too_easy">too_easy</option>
      <option value="too_hard">too_hard</option>
      <option value="goldilocks">goldilocks</option>
      <option value="borderline">borderline</option>
    </select>
    <select id="verdictFilter">
      <option value="">CORRECT &amp; WRONG</option>
      <option value="CORRECT">Has CORRECT</option>
      <option value="WRONG">Has WRONG</option>
    </select>
  </div>
</header>

<div class="layout">
  <aside id="plist"></aside>
  <main><div class="reader" id="reader"><div class="empty">Select a problem from the left.</div></div></main>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const PROBLEMS = DATA.problems;
let activeIdx = -1;

document.getElementById('counts').textContent =
  PROBLEMS.length + " problems · " +
  PROBLEMS.reduce((a,p)=>a+p.rollouts.length,0) + " rollouts";

function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function zoneClass(z){return ['too_easy','too_hard','goldilocks','borderline'].includes(z)?z:'unknown';}

function matchesFilters(p){
  const q = document.getElementById('search').value.trim().toLowerCase();
  const zf = document.getElementById('zoneFilter').value;
  const vf = document.getElementById('verdictFilter').value;
  if(zf && p.zone !== zf) return false;
  if(vf && !p.rollouts.some(r=>r.verdict===vf)) return false;
  if(q){
    const inConcept = p.concept.toLowerCase().includes(q);
    const inBody = p.rollouts.some(r=>r.body.toLowerCase().includes(q)) ||
                   (p.statement||'').toLowerCase().includes(q);
    if(!inConcept && !inBody) return false;
  }
  return true;
}

function renderList(){
  const el = document.getElementById('plist');
  el.innerHTML='';
  let shown=0;
  PROBLEMS.forEach((p,i)=>{
    if(!matchesFilters(p)) return;
    shown++;
    const div=document.createElement('div');
    div.className='plist-item'+(i===activeIdx?' active':'');
    div.dataset.idx=i;
    const zc=zoneClass(p.zone);
    div.innerHTML =
      '<div class="row1">'+
        '<span class="chip '+zc+'">'+(p.zone||'?')+'</span>'+
        '<span class="score">'+p.n_correct+'/8</span>'+
      '</div>'+
      '<div class="concept">'+esc(p.concept)+'</div>'+
      '<div class="meta">gold = '+esc(p.gold)+' · '+p.rollouts.length+' rollouts</div>';
    div.onclick=()=>selectProblem(i);
    el.appendChild(div);
  });
  if(shown===0){
    el.innerHTML='<div style="padding:20px;color:var(--muted);font-size:13px;">No problems match.</div>';
  }
}

function selectProblem(i){
  activeIdx=i;
  renderList();
  const p=PROBLEMS[i];
  const reader=document.getElementById('reader');
  const zc=zoneClass(p.zone);
  let h='<div class="phead">'+
    '<h2>'+esc(p.concept)+'</h2>'+
    '<div class="metaline">'+
      '<span class="chip '+zc+'">'+(p.zone||'unknown')+'</span>'+
      '<span><b>'+p.n_correct+'/8</b> correct</span>'+
      '<span>gold = <b>'+esc(p.gold)+'</b></span>'+
      '<span>grades = ['+esc(p.grades.join(', '))+']</span>'+
    '</div></div>';
  if(p.statement && p.statement.length>2){
    h+='<div class="statement"><span class="lbl">Problem</span>'+esc(p.statement)+'</div>';
  }
  p.rollouts.forEach((r,ri)=>{
    h+='<div class="card" data-card="'+ri+'">'+
      '<div class="card-head" onclick="toggleCard(this)">'+
        '<span class="rn">rollout '+r.n+'</span>'+
        '<span class="badge '+r.verdict+'">'+r.verdict+'</span>'+
        '<span class="toggle">[−]</span>'+
      '</div>'+
      '<div class="card-body">'+esc(r.body)+'</div>'+
    '</div>';
  });
  reader.innerHTML=h;
  reader.parentElement.scrollTop=0;
  typeset(reader);
}

function toggleCard(headEl){
  const card=headEl.parentElement;
  card.classList.toggle('collapsed');
  const t=headEl.querySelector('.toggle');
  t.textContent=card.classList.contains('collapsed')?'[+]':'[−]';
}

function typeset(node){
  if(window.MathJax && MathJax.typesetPromise){
    MathJax.typesetPromise([node]).catch(()=>{});
  }
}

document.getElementById('search').addEventListener('input',renderList);
document.getElementById('zoneFilter').addEventListener('change',renderList);
document.getElementById('verdictFilter').addEventListener('change',renderList);

renderList();
</script>
</body>
</html>
"""

HTML = HTML.replace("__DATA__", data_json)
open(OUT, "w", encoding="utf-8").write(HTML)
print("Wrote", OUT, len(HTML), "chars")
