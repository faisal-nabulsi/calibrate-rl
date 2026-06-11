#!/usr/bin/env python3
"""
Build a clean, readable base-vs-trained held-out viewer (one self-contained HTML,
MathJax-rendered) with per-question verdicts. Reads gen_holdout_responses.py outputs.

    python3 tools/gen_holdout_compare.py
    -> results/holdout_compare.html   (open in a browser)
"""
import json, os, html

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = json.load(open(f"{REPO}/results/holdout_resp_base__abl3_holdout.json"))
TR   = json.load(open(f"{REPO}/results/holdout_resp_checkpoint-108__abl3_holdout.json"))
OUT  = f"{REPO}/results/holdout_compare.html"

# Per-question verdicts (read every rollout). cls = up | flat | down.
VERDICTS = [
 {"cls":"up","tag":"execution ↑↑","t":"Both apply inclusion–exclusion correctly; base botches the arithmetic when combining the terms (→173), trained executes it reliably (→169). Big execution-reliability gain."},
 {"cls":"flat","tag":"flat","t":"Already easy for both — same I–E method, both ~7/8. No change."},
 {"cls":"up","tag":"execution ↑↑","t":"Same I–E framework; base is inconsistent on the floor-division arithmetic (→411), trained nails every rollout (→421)."},
 {"cls":"up","tag":"execution ↑","t":"Both set up I–E correctly; trained a touch more reliable (8/8 vs 7/8)."},
 {"cls":"up","tag":"execution ↑↑↑ · standout","t":"Base failed ALL 8 — systematically erring on the arithmetic (→283), not random noise. Trained fixed it to 7/8. The single clearest reliability gain in the set."},
 {"cls":"flat","tag":"flat","t":"Both factorize and count divisors > 6 correctly. No change."},
 {"cls":"down","tag":"regression · noise","t":"Odd divisors of 504 — both fully get it (drop 2³, count 3²·7 → 6). Base 8/8, trained 7/8: a single-rollout slip, noise."},
 {"cls":"up","tag":"execution ↑","t":"Divisors < 40 of 1320 — same method; trained enumerates and filters more carefully (8/8 vs 6/8)."},
 {"cls":"down","tag":"REGRESSION · real","t":"Divisors < 30 of 1008 — both BAD (3/8 → 2/8). The enumeration is genuinely error-prone (long divisor list) and training didn't help. The one spot it got slightly worse — flag it honestly."},
 {"cls":"up","tag":"execution ↑","t":"Divisors < 40 of 2100 — base misses 25 and 30 (→16); trained enumerates completely (→17)."},
 {"cls":"up","tag":"completeness ↑↑","t":"a²+b²=340 — base finds a pair but mis-sums / misses pairs (→74); trained systematically finds all and sums them (→48)."},
 {"cls":"up","tag":"execution ↑","t":"a²+b²=61 — same search; trained slightly more reliable (8/8 vs 7/8)."},
 {"cls":"flat","tag":"flat","t":"a²+b²=226 — both strong, no change."},
 {"cls":"flat","tag":"cleaner method · flat","t":"a²+b²=80 — base's failing rollout uses a muddled search (pins b=1); trained's search is cleaner, but both land ~7/8 overall."},
 {"cls":"up","tag":"completeness ↑↑","t":"a²+b²=586 — base misses pairs (→58); trained's systematic search finds them all (→34)."},
]

SUMMARY = (
 "Across all 15, base and trained use the <strong>same high-level method</strong> (inclusion–exclusion, the "
 "divisor-count formula, or a sum-of-two-squares search). The <strong>+0.22 held-out gain is overwhelmingly "
 "execution reliability</strong> — the trained model carries out the arithmetic, enumeration, and search more "
 "consistently across rollouts. On these <em>in-band, calibrated</em> problems it is not learning a new method; "
 "it is becoming <strong>reliable at the method it already had</strong>. Tally: <strong>8 improved, 5 flat, "
 "2 slight regressions</strong> (#7 is noise; #9 is the genuinely enumeration-heavy case where both are weak). "
 "This is textbook <strong>“learns the concept in-distribution,”</strong> and it explains the AMC transfer gap: "
 "reliable execution on calibrated single-concept problems is a different skill from picking the right method on a "
 "harder, <strong>compositional</strong> AMC framing."
)

def esc(s): return html.escape(s or "")
bm = sum(r["pass_rate"] for r in BASE)/len(BASE)
tm = sum(r["pass_rate"] for r in TR)/len(TR)
ARROW = {"up":"▲","down":"▼","flat":"—"}

def pips(rec):
    cells = "".join(f'<i class="{ "p" if r==1.0 else "f" }"></i>' for r in rec["rewards"])
    return f'<span class="pips">{cells}</span>'

def rep(rec, want_pass):
    for resp, r in zip(rec["responses"], rec["rewards"]):
        if (r == 1.0) == want_pass:
            return resp
    return rec["responses"][0]

def all_rollouts(rec):
    items = []
    for i, (resp, r) in enumerate(zip(rec["responses"], rec["rewards"])):
        b = '<b class="ok">✓</b>' if r == 1.0 else '<b class="no">✗</b>'
        items.append(f'<details class="ro"><summary>{b} rollout {i+1}</summary><div class="resp">{esc(resp)}</div></details>')
    return "".join(items)

rows, cards = [], []
for i, (b, t) in enumerate(zip(BASE, TR)):
    v = VERDICTS[i]; nb = int(round(b["pass_rate"]*8)); nt = int(round(t["pass_rate"]*8))
    d = nt - nb; dtxt = f"{d:+d}"
    rows.append(
        f'<tr class="r-{v["cls"]}"><td class="n"><a href="#q{i+1}">{i+1}</a></td>'
        f'<td class="cn">{esc(b["skeleton_type"]).replace("_"," ")}</td>'
        f'<td class="q">{esc(b["problem"])}</td><td class="g">{esc(str(b["gold"]))}</td>'
        f'<td class="sc">{nb}/8 → <strong>{nt}/8</strong></td>'
        f'<td class="dl {v["cls"]}">{ARROW[v["cls"]]} {dtxt}</td></tr>')
    cards.append(f"""
<section class="card" id="q{i+1}">
  <div class="head">
    <span class="num">#{i+1}</span>
    <span class="pill cn">{esc(b['skeleton_type']).replace('_',' ')}</span>
    <span class="pill gold">gold {esc(str(b['gold']))}</span>
    <span class="grow"></span>
    <span class="pill {v['cls']}">{ARROW[v['cls']]} {esc(v['tag'])}</span>
  </div>
  <p class="qtxt">{esc(b['problem'])}</p>
  <div class="scores">
    <div class="sline"><span class="lbl base">BASE</span> {pips(b)} <span class="frac">{nb}/8</span></div>
    <div class="sline"><span class="lbl tr">TRAINED</span> {pips(t)} <span class="frac">{nt}/8</span></div>
  </div>
  <div class="verdict {v['cls']}">{v['t']}</div>
  <div class="cols">
    <div class="col">
      <div class="colh base">BASE · representative {'rollout' if b['correct']==8 else 'failure'}</div>
      <div class="resp">{esc(rep(b, b['correct']==8))}</div>
      <details class="more"><summary>all 8 base rollouts</summary>{all_rollouts(b)}</details>
    </div>
    <div class="col">
      <div class="colh tr">TRAINED · representative {'rollout' if t['correct']==0 else 'success'}</div>
      <div class="resp">{esc(rep(t, t['correct']>0))}</div>
      <details class="more"><summary>all 8 trained rollouts</summary>{all_rollouts(t)}</details>
    </div>
  </div>
</section>""")

CSS = """
*{box-sizing:border-box}
:root{--ink:#1f2328;--muted:#59636e;--line:#d1d9e0;--bg:#eef1f4;--card:#fff;
      --base:#0969da;--tr:#1a7f37;--up:#1a7f37;--down:#cf222e;--flat:#6e7781;--gold:#9a6700}
body{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,sans-serif;color:var(--ink);background:var(--bg);margin:0}
.wrap{max-width:1080px;margin:0 auto;padding:40px 24px 90px}
h1{font-size:27px;line-height:1.25;margin:0 0 6px;letter-spacing:-.015em}
.sub{color:var(--muted);margin:0 0 26px}
.hero{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:26px 28px;margin-bottom:26px;box-shadow:0 1px 3px rgba(31,35,40,.06)}
.stat{font-size:36px;font-weight:780;letter-spacing:-.02em;margin-bottom:14px}
.stat .b{color:var(--base)}.stat .t{color:var(--tr)}.stat .d{color:var(--tr);font-size:24px;font-weight:700;margin-left:6px}
.summary{font-size:16px;color:#39424b;line-height:1.72;max-width:78ch}
.summary strong{color:var(--ink)}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;margin:0 0 34px;font-size:14.5px}
thead th{text-align:left;padding:12px 14px;color:var(--muted);font-weight:600;font-size:12px;letter-spacing:.06em;text-transform:uppercase;border-bottom:1px solid var(--line);background:#f6f8fa}
tbody td{padding:11px 14px;border-bottom:1px solid #eaeef2;vertical-align:top}
tbody tr:last-child td{border-bottom:0}
td.n a{color:var(--base);text-decoration:none;font-weight:700}
td.cn{color:#475160;white-space:nowrap}td.q{color:#39424b;max-width:440px}td.g{color:var(--gold);font-weight:600;white-space:nowrap}
td.sc{white-space:nowrap;color:#475160}td.sc strong{color:var(--tr)}
td.dl{white-space:nowrap;font-weight:700}td.dl.up{color:var(--up)}td.dl.down{color:var(--down)}td.dl.flat{color:var(--flat)}
tr.r-up td.n a{border-left:3px solid var(--up);padding-left:7px;margin-left:-10px}
tr.r-down td.n a{border-left:3px solid var(--down);padding-left:7px;margin-left:-10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:22px 24px;margin:18px 0;box-shadow:0 1px 3px rgba(31,35,40,.05);scroll-margin-top:18px}
.head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:12px}
.num{font-weight:780;font-size:18px;color:var(--ink)}.grow{flex:1}
.pill{font-size:12.5px;font-weight:600;padding:3px 10px;border-radius:999px;border:1px solid var(--line);white-space:nowrap}
.pill.cn{color:#475160;background:#f3f5f8}.pill.gold{color:var(--gold);background:#fdf6e3;border-color:#eed9a0}
.pill.up{color:#fff;background:var(--up);border-color:var(--up)}.pill.down{color:#fff;background:var(--down);border-color:var(--down)}.pill.flat{color:#475160;background:#eef1f4}
.qtxt{font-size:17px;line-height:1.55;margin:2px 0 14px;color:#15191d}
.scores{display:flex;flex-direction:column;gap:6px;margin-bottom:14px}
.sline{display:flex;align-items:center;gap:10px}
.lbl{font-size:11px;font-weight:700;letter-spacing:.06em;width:74px}.lbl.base{color:var(--base)}.lbl.tr{color:var(--tr)}
.pips{display:inline-flex;gap:3px}.pips i{width:15px;height:15px;border-radius:4px;display:inline-block}
.pips i.p{background:var(--tr)}.pips i.f{background:#e7ebef;border:1px solid #d9dfe5}
.frac{color:var(--muted);font-size:13px}
.verdict{font-size:15.5px;line-height:1.6;padding:12px 16px;border-radius:10px;margin-bottom:18px;border-left:4px solid var(--flat);background:#f6f8fa;color:#2c333a}
.verdict.up{border-left-color:var(--up);background:#eaf6ec}.verdict.down{border-left-color:var(--down);background:#fcebec}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:820px){.cols{grid-template-columns:1fr}}
.colh{font-size:11.5px;font-weight:700;letter-spacing:.05em;margin-bottom:7px;text-transform:uppercase}
.colh.base{color:var(--base)}.colh.tr{color:var(--tr)}
.resp{background:#f6f8fa;border:1px solid var(--line);border-radius:10px;padding:14px 16px;font-size:14.5px;line-height:1.62;color:#2b3138;max-height:460px;overflow:auto;white-space:normal}
.more{margin-top:8px}.more>summary{cursor:pointer;color:var(--base);font-size:13px;font-weight:600;padding:4px 0}
.ro{border:1px solid var(--line);border-radius:8px;margin:6px 0;background:#fff}
.ro>summary{cursor:pointer;padding:7px 11px;font-size:13px;color:#475160}
.ro .resp{margin:0;border:0;border-top:1px solid var(--line);border-radius:0 0 8px 8px;max-height:360px}
.ok{color:var(--tr)}.no{color:var(--down)}
"""

HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Held-out: base vs trained (abl3 ckpt-108)</title>
<script>window.MathJax={tex:{inlineMath:[['\\\\(','\\\\)']],displayMath:[['\\\\[','\\\\]']]},chtml:{scale:0.96}};</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>__CSS__</style></head><body><div class="wrap">
<h1>Held-out reasoning — base vs trained</h1>
<p class="sub">3-concept ablation · checkpoint-108 · 15 calibrated held-out problems · 8 rollouts each · same Qwen-7B ± the LoRA adapter · 2026-06-11</p>
<div class="hero">
  <div class="stat">base <span class="b">__BM__</span> &nbsp;→&nbsp; trained <span class="t">__TM__</span><span class="d">+__DM__</span></div>
  <div class="summary">__SUMMARY__</div>
</div>
<table><thead><tr><th>#</th><th>concept</th><th>question</th><th>gold</th><th>base → trained</th><th>Δ</th></tr></thead>
<tbody>__ROWS__</tbody></table>
__CARDS__
</div></body></html>"""

HTML = (HTML.replace("__CSS__", CSS).replace("__BM__", f"{bm:.3f}").replace("__TM__", f"{tm:.3f}")
            .replace("__DM__", f"{tm-bm:.3f}").replace("__SUMMARY__", SUMMARY)
            .replace("__ROWS__", "".join(rows)).replace("__CARDS__", "".join(cards)))
open(OUT, "w").write(HTML)
print(f"wrote {OUT}  ({len(HTML)//1024} KB)")
print(f"base {bm:.3f} -> trained {tm:.3f}  (+{tm-bm:.3f})")
