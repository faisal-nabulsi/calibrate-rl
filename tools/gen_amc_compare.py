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
        "id": k, "q": b["question"], "gold": str(b["gold_answer"]), "flip": flip,
        "b_ok": b["correct"], "b_pred": str(b.get("predicted_answer")), "b_resp": b["model_response"],
        "t_ok": t["correct"], "t_pred": str(t.get("predicted_answer")), "t_resp": t["model_response"],
    })
order = {"up": 0, "down": 1, "same_wrong": 2, "same_ok": 3}
recs.sort(key=lambda r: (order[r["flip"]], r["q"]))

# Michael's per-problem judgment after reading both responses.
# verdict: real-improve | minor-improve | path | real-regress | fluke
JUDGMENTS = {
 18: ("path", "Cleaner method, sloppy execution. Base double-counted via overlapping quadrant cases (→925). "
      "Trained switched to symmetric |x|,|y| counting and landed the correct 841 despite a visible arithmetic "
      "stumble it recovered from. Better approach, messy run."),
 42: ("real-improve", "GENUINE fix. Base made a fundamental log error — wrote a₇ = 27·log₂a₇ instead of 27 + log₂a₇ — "
      "and brute-forced fruitlessly until it ran out of tokens (no answer). Trained did the algebra correctly "
      "(a₇ = 27 + log₂a₇ → 32) and solved cleanly. Real reasoning, not luck."),
 59: ("real-improve", "GENUINE fix. Base used the wrong form 5k² — missing that 5∣square ⟹ 25∣square. Trained correctly "
      "used 25m². A real number-theory insight."),
 66: ("real-improve", "GENUINE fix. Base mis-identified the intersection points (mirrored wrong → undefined/vertical slope) "
      "and fumbled. Trained recognized BOTH circles pass through the origin, used origin + the second point → slope 2/5 → 7. "
      "Real geometric insight."),
 67: ("minor-improve", "Minor fix, same method. Both optimize with calculus; base slipped an extra factor of 2 in the area "
      "(→3/4 → 25), trained executed the algebra correctly (→3/2 → 13). Cleaner execution, not a new concept."),
 68: ("real-improve", "GENUINE fix. Base got confused by the custom operation, left x unsolved and just boxed 40. Trained "
      "correctly evaluated z⊗z = x²+y²i and solved the full system (x=√10) → 50."),
 80: ("real-improve", "GENUINE fix. Base ignored the denominator's sign — treated it as numerator≥0 → 0≤log n≤2, a range where "
      "the fraction is actually NEGATIVE. Trained correctly handled the fraction's sign → n=1 and 100–999 → 901."),
 7:  ("real-regress", "Real regression, on a recall-heavy problem. Base recalled the known Pell sequence (288 → digit sum 18). "
      "Trained tried to DERIVE the recurrence, used wrong coefficients (498) → 24. Worse reasoning — but base essentially memorized it."),
 19: ("real-regress", "REAL regression. Base correctly included the 'average equals X itself' case (X=4); trained dropped it, "
      "got only X=22,10 → 32. A genuinely missed case, not noise."),
 53: ("real-regress", "REAL regression. Trained made arithmetic errors building the array rows AND a logic error (treated the whole "
      "2023rd row as digit 3, computed 2023×3 → units 9). Base computed the rows and pattern correctly → 5."),
 60: ("fluke", "NOT a reasoning loss — a careless fumble. Trained actually computed the answer correctly via logs "
      "(⌊17.385⌋+1 = 18) but then contradicted itself and boxed 19. It had the right answer in hand."),
 71: ("fluke", "NOT a reasoning loss — truncation. Trained took a verbose exhaustive-enumeration path and ran out of tokens "
      "before concluding. Base used a cleaner brute-force-to-30 and finished (29 → 11). An efficiency/budget failure."),
}
OVERALL = ("Reading all 12 flips changes the picture vs the count. The 7 UPs are mostly GENUINE reasoning fixes "
           "(real algebra/number-theory/geometry corrections — #42, #59, #66, #68, #80), not luck. Of the 5 DOWNs, "
           "3 are real regressions (#7, #19, #53) and 2 aren't reasoning losses at all (#60 careless mis-box, #71 "
           "truncation). So ~6 real improvements vs ~3 real regressions, with 2 fixable fluke losses. The net count "
           "(+2, McNemar p≈0.77) is within noise, but the QUALITY of the changes shows real, modest reasoning movement — "
           "not the pure noise the number alone implies. Encouraging for run 2 with more optimization force.")

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
<div style="max-width:1500px;margin:14px auto 0;padding:0 14px"><div class="panel" style="border-left:4px solid #3257d6"><b>Michael's read (after reading all 12 flipped transcripts):</b> %OVERALL%</div></div>
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
const DATA=%DATA%; const JUDG=%JDATA%; const $=id=>document.getElementById(id); let filter="";
const VCOL={'real-improve':'#137a37','minor-improve':'#137a37','path':'#3257d6','real-regress':'#b3261e','fluke':'#b07a00'};
const VLAB={'real-improve':'REAL IMPROVEMENT','minor-improve':'MINOR IMPROVEMENT','path':'DIFFERENT PATH','real-regress':'REAL REGRESSION','fluke':'FLUKE (not reasoning)'};
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
 const rd=$('reader'); const j=JUDG[r.id]; let jbox='';
 if(j){jbox=`<div style="border-left:4px solid ${VCOL[j[0]]};background:#fafafe;padding:9px 12px;margin-bottom:10px;border-radius:6px">`+
   `<b style="color:${VCOL[j[0]]}">${VLAB[j[0]]} — judgment:</b> ${esc(j[1])}</div>`;}
 rd.innerHTML=`<div class="q">${esc(r.q)}<span class="pill">gold ${esc(r.gold)}</span></div>`+jbox+
   `<div class="cols">${col('BASE',r.b_ok,r.b_pred,r.b_resp)}${col('TRAINED (ckpt-120)',r.t_ok,r.t_pred,r.t_resp)}</div>`;
 if(window.MathJax&&MathJax.typesetPromise)MathJax.typesetPromise([rd]);
}
renderList();
</script></body></html>"""
PAGE = (PAGE.replace("%DATA%", DATA).replace("%JDATA%", json.dumps(JUDGMENTS))
        .replace("%OVERALL%", html.escape(OVERALL))
        .replace("%NB%", str(nb)).replace("%NT%", str(nt))
        .replace("%NET%", f"{nt-nb:+d}").replace("%UP%", str(up)).replace("%DOWN%", str(down))
        .replace("%P%", f"{pval:.2f}").replace("%TOTAL%", str(len(recs))))
open(OUT, "w").write(PAGE)
print(f"wrote {OUT}")
print(f"base {nb}/83 → trained {nt}/83 ({nt-nb:+d}) | up {up} down {down} | McNemar p≈{pval:.2f}")
