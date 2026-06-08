#!/usr/bin/env python3
"""
Clean transcript READER for the v10 training run: the trained checkpoint's full
reasoning on all 83 AMC problems (with a per-problem toggle to see the base
model). Distinct from amc_compare.html (which is the flip-comparison view).

Reads results/results_qwen7b_base.json + results/..._checkpoint_*.json;
writes tools/amc_transcripts.html. Open via file://.
    python3 tools/gen_amc_reader.py
"""
import os, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RES = os.path.join(REPO, "results")
base = {r["problem_id"]: r for r in json.load(open(os.path.join(RES, "results_qwen7b_base.json")))}
tf = sorted(glob.glob(os.path.join(RES, "results_qwen7b_checkpoint_*.json")))[-1]
trained = {r["problem_id"]: r for r in json.load(open(tf))}
keys = sorted(set(base) & set(trained))

recs = []
for k in keys:
    b, t = base[k], trained[k]
    recs.append({"id": k, "q": b["question"], "gold": str(b["gold_answer"]),
                 "t_ok": t["correct"], "t_pred": str(t.get("predicted_answer")), "t_resp": t["model_response"],
                 "b_ok": b["correct"], "b_pred": str(b.get("predicted_answer")), "b_resp": b["model_response"]})
nb = sum(r["b_ok"] for r in recs); nt = sum(r["t_ok"] for r in recs)
DATA = json.dumps(recs)

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>v10 trained — AMC transcripts</title>
<script>window.MathJax={tex:{inlineMath:[['\\\\(','\\\\)']],displayMath:[['\\\\[','\\\\]']]},svg:{fontCache:'global'}};</script>
<script async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-svg.min.js"></script>
<style>
:root{--bg:#f7f7f8;--card:#fff;--line:#e3e3e8;--ink:#1d1d1f;--mut:#6b6b76;}
*{box-sizing:border-box}body{margin:0;font:14px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
header{background:#11131a;color:#fff;padding:12px 18px}header h1{margin:0;font-size:16px}
header .sub{color:#9aa0b4;font-size:12.5px;margin-top:3px}
.wrap{display:flex;gap:14px;max-width:1280px;margin:14px auto;padding:0 14px}
.side{width:300px;flex:none}.main{flex:1;min-width:0}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-bottom:12px}
.filters button{cursor:pointer;border:1px solid var(--line);background:#fafafe;border-radius:7px;padding:5px 9px;margin:2px;font:inherit;font-size:12px}
.filters button.on{background:#3257d6;color:#fff;border-color:#3257d6}
.plist{max-height:74vh;overflow:auto}
.plist button{display:block;width:100%;text-align:left;background:#fafafe;border:1px solid var(--line);margin-bottom:5px;padding:7px 9px;border-radius:7px;font:inherit}
.plist button.sel{border-color:#3257d6;background:#eef2fe}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
.ok{background:#2faa5a}.no{background:#e5534b}
.q{background:#fbfbfd;border:1px solid var(--line);border-radius:8px;padding:11px 13px;margin-bottom:10px}
.pill{font-size:12px;color:var(--mut);background:#eef0f6;padding:2px 8px;border-radius:12px;margin-left:6px}
.badge{font-weight:700}.tok{color:#137a37}.tno{color:#b3261e}
.resp{white-space:pre-wrap;word-wrap:break-word;border:1px solid var(--line);border-radius:8px;padding:11px 13px;max-height:64vh;overflow:auto}
.hdr{display:flex;justify-content:space-between;align-items:center;margin:6px 0}
.toggle{cursor:pointer;color:#3257d6;font-size:12.5px;text-decoration:underline;background:none;border:0}
</style></head><body>
<header><h1>v10 trained model — AMC transcripts (checkpoint-120)</h1>
<div class="sub">trained %NT%/83 correct (base %NB%/83) · reading view · toggle base per problem · amc_compare.html = flip view</div></header>
<div class="wrap">
 <div class="side"><div class="panel filters">
   <button data-f="" class="on">all (83)</button>
   <button data-f="ok">trained correct</button>
   <button data-f="no">trained wrong</button>
 </div><div class="panel"><div id="plist" class="plist"></div></div></div>
 <div class="main"><div class="panel"><div id="reader"><div style="color:var(--mut)">Pick a problem to read the trained model's full reasoning.</div></div></div></div>
</div>
<script>
const DATA=%DATA%; const $=id=>document.getElementById(id); let filter="", showBase={};
function esc(s){return (s==null?'':String(s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
document.querySelectorAll('.filters button').forEach(btn=>btn.onclick=()=>{
 filter=btn.dataset.f;document.querySelectorAll('.filters button').forEach(b=>b.classList.toggle('on',b===btn));renderList();});
function renderList(){
 const d=$('plist');d.innerHTML='';
 DATA.filter(r=>!filter||(filter==='ok'?r.t_ok:!r.t_ok)).forEach(r=>{
  const b=document.createElement('button');
  b.innerHTML=`<span class="dot ${r.t_ok?'ok':'no'}"></span>${esc(r.q.slice(0,74))}${r.q.length>74?'…':''}`;
  b.onclick=()=>{[...d.children].forEach(x=>x.classList.remove('sel'));b.classList.add('sel');show(r);};
  d.appendChild(b);});
}
function show(r){
 const rd=$('reader'); const sb=showBase[r.id];
 let h=`<div class="q">${esc(r.q)}<span class="pill">gold ${esc(r.gold)}</span></div>`+
  `<div class="hdr"><b>Trained (ckpt-120) <span class="badge ${r.t_ok?'tok':'tno'}">${r.t_ok?'CORRECT':'WRONG'} · ${esc(r.t_pred)}</span></b>`+
  `<button class="toggle" onclick="showBase[${r.id}]=!showBase[${r.id}];show(DATA.find(x=>x.id===${r.id}))">${sb?'hide':'show'} base model</button></div>`+
  `<div class="resp">${esc(r.t_resp)}</div>`;
 if(sb){h+=`<div class="hdr" style="margin-top:12px"><b>Base <span class="badge ${r.b_ok?'tok':'tno'}">${r.b_ok?'CORRECT':'WRONG'} · ${esc(r.b_pred)}</span></b></div><div class="resp">${esc(r.b_resp)}</div>`;}
 rd.innerHTML=h;
 if(window.MathJax&&MathJax.typesetPromise)MathJax.typesetPromise([rd]);
}
renderList();
</script></body></html>"""
PAGE = PAGE.replace("%DATA%", DATA).replace("%NB%", str(nb)).replace("%NT%", str(nt))
open(os.path.join(HERE, "amc_transcripts.html"), "w").write(PAGE)
print(f"wrote {os.path.join(HERE,'amc_transcripts.html')}  | base {nb}/83, trained {nt}/83")
