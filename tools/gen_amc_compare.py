#!/usr/bin/env python3
"""
Build a self-contained AMC base-vs-trained comparison viewer (side by side),
so you can read the FLIPPED problems and judge real-gain vs noise.

Reads results_qwen7b_base.json + results_qwen7b_checkpoint_*.json from the repo
root; writes tools/amc_compare.html. Open via file://.
    python3 tools/gen_amc_compare.py
"""
import os, re, json, glob, html
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BASE = os.path.join(REPO, "results_qwen7b_base.json")
TR = sorted(glob.glob(os.path.join(REPO, "results_qwen7b_checkpoint_*.json")))[-1]
OUT = os.path.join(HERE, "amc_compare.html")

base = {r.get("problem_id", r["question"]): r for r in json.load(open(BASE))}
trained = {r.get("problem_id", r["question"]): r for r in json.load(open(TR))}
keys = [k for k in base if k in trained]

recs = []
for k in keys:
    b, t = base[k], trained[k]
    if not b["correct"] and t["correct"]:
        flip = "up"
    elif b["correct"] and not t["correct"]:
        flip = "down"
    else:
        flip = "same_ok" if b["correct"] else "same_wrong"
    recs.append({
        "q": b["question"], "gold": str(b["gold_answer"]), "flip": flip,
        "b_ok": b["correct"], "b_pred": str(b.get("predicted_answer")), "b_resp": b["model_response"],
        "t_ok": t["correct"], "t_pred": str(t.get("predicted_answer")), "t_resp": t["model_response"],
    })
order = {"up": 0, "down": 1, "same_wrong": 2, "same_ok": 3}
recs.sort(key=lambda r: (order[r["flip"]], r["q"]))

nb = sum(1 for r in recs if r["b_ok"]); nt = sum(1 for r in recs if r["t_ok"])
up = sum(1 for r in recs if r["flip"] == "up"); down = sum(1 for r in recs if r["flip"] == "down")
n = up + down; kk = min(up, down)
pval = (2 * sum(comb(n, i) for i in range(0, kk + 1)) / 2**n) if n else 1.0

DATA = json.dumps(recs)
PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>AMC base vs trained</title>
<script>window.MathJax={tex:{inlineMath:[['\\\\(','\\\\)']],displayMath:[['\\\\[','\\\\]']]},svg:{fontCache:'global'}};</script>
<script async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-svg.min.js"></script>
<style>
:root{--bg:#f7f7f8;--card:#fff;--line:#e3e3e8;--ink:#1d1d1f;--mut:#6b6b76;}
*{box-sizing:border-box}body{margin:0;font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
header{background:#11131a;color:#fff;padding:12px 18px}header h1{margin:0;font-size:16px}
header .sub{color:#9aa0b4;font-size:12.5px;margin-top:3px}
.wrap{display:flex;gap:14px;max-width:1500px;margin:14px auto;padding:0 14px}
.side{width:330px;flex:none}.main{flex:1;min-width:0}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-bottom:12px}
.filters button{cursor:pointer;border:1px solid var(--line);background:#fafafe;border-radius:7px;padding:5px 9px;margin:2px;font:inherit;font-size:12px}
.filters button.on{background:#3257d6;color:#fff;border-color:#3257d6}
.plist{max-height:74vh;overflow:auto}
.plist button{display:block;width:100%;text-align:left;background:#fafafe;border:1px solid var(--line);margin-bottom:5px;padding:7px 9px;border-radius:7px;font:inherit}
.plist button.sel{border-color:#3257d6;background:#eef2fe}
.tag{display:inline-block;font-size:10.5px;font-weight:700;padding:1px 7px;border-radius:10px;margin-right:6px}
.up{background:#e6f6ec;color:#137a37}.down{background:#fdeaea;color:#b3261e}.same_ok{background:#eef0f6;color:#137a37}.same_wrong{background:#eef0f6;color:#6b6b76}
.cols{display:flex;gap:14px}.col{flex:1;min-width:0;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.col h3{margin:0;padding:8px 12px;font-size:13px;background:#fafafe;border-bottom:1px solid var(--line);display:flex;justify-content:space-between}
.col .resp{padding:11px 13px;white-space:pre-wrap;word-wrap:break-word;max-height:68vh;overflow:auto}
.ok{color:#137a37}.no{color:#b3261e}.badge{font-weight:700}
.q{background:#fbfbfd;border:1px solid var(--line);border-radius:8px;padding:11px 13px;margin-bottom:10px}
.pill{font-size:12px;color:var(--mut);background:#eef0f6;padding:2px 8px;border-radius:12px;margin-left:6px}
</style></head><body>
<header><h1>AMC — base vs trained (checkpoint-120)</h1>
<div class="sub">base %NB%/83 → trained %NT%/83 (%NET%) · flips: %UP%↑ %DOWN%↓ · McNemar p ≈ %P% (not significant)</div></header>
<div class="wrap">
 <div class="side"><div class="panel filters">
   <button data-f="" class="on">all (%TOTAL%)</button>
   <button data-f="up">↑ up (%UP%)</button>
   <button data-f="down">↓ down (%DOWN%)</button>
   <button data-f="same_wrong">stayed wrong</button>
   <button data-f="same_ok">stayed right</button>
 </div><div class="panel"><div id="plist" class="plist"></div></div></div>
 <div class="main"><div class="panel"><div id="reader"><div style="color:var(--mut)">Pick a problem — read base vs trained side by side.</div></div></div></div>
</div>
<script>
const DATA=%DATA%; const $=id=>document.getElementById(id); let filter="";
function esc(s){return (s==null?'':String(s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
document.querySelectorAll('.filters button').forEach(btn=>btn.onclick=()=>{
 filter=btn.dataset.f;document.querySelectorAll('.filters button').forEach(b=>b.classList.toggle('on',b===btn));renderList();});
function renderList(){
 const d=$('plist');d.innerHTML='';
 DATA.map((r,i)=>[r,i]).filter(([r])=>!filter||r.flip===filter).forEach(([r,i])=>{
  const b=document.createElement('button');
  b.innerHTML=`<div><span class="tag ${r.flip}">${({up:'WRONG→RIGHT',down:'RIGHT→WRONG',same_ok:'right',same_wrong:'wrong'})[r.flip]}</span></div>`+
    `<div style="margin-top:3px">${esc(r.q.slice(0,80))}${r.q.length>80?'…':''}</div>`;
  b.onclick=()=>{[...d.children].forEach(x=>x.classList.remove('sel'));b.classList.add('sel');show(r);};
  d.appendChild(b);});
}
function col(title,ok,pred,resp){
 return `<div class="col"><h3><span>${title}</span><span class="badge ${ok?'ok':'no'}">${ok?'CORRECT':'WRONG'} · ${esc(pred)}</span></h3><div class="resp">${esc(resp)}</div></div>`;
}
function show(r){
 const rd=$('reader');
 rd.innerHTML=`<div class="q">${esc(r.q)}<span class="pill">gold ${esc(r.gold)}</span></div>`+
   `<div class="cols">${col('BASE',r.b_ok,r.b_pred,r.b_resp)}${col('TRAINED (ckpt-120)',r.t_ok,r.t_pred,r.t_resp)}</div>`;
 if(window.MathJax&&MathJax.typesetPromise)MathJax.typesetPromise([rd]);
}
renderList();
</script></body></html>"""
PAGE = (PAGE.replace("%DATA%", DATA).replace("%NB%", str(nb)).replace("%NT%", str(nt))
        .replace("%NET%", f"{nt-nb:+d}").replace("%UP%", str(up)).replace("%DOWN%", str(down))
        .replace("%P%", f"{pval:.2f}").replace("%TOTAL%", str(len(recs))))
open(OUT, "w").write(PAGE)
print(f"wrote {OUT}")
print(f"base {nb}/83 → trained {nt}/83 ({nt-nb:+d}) | up {up} down {down} | McNemar p≈{pval:.2f}")
