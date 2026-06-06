#!/usr/bin/env python3
"""
Step 3 — "Call the model yourself" UI (CalibrateRL experiment-design protocol).

A tiny zero-dependency local web app: serves a browser UI that calls
Qwen2.5-7B-Instruct over an OpenAI-compatible chat API, using the EXACT system
prompt the calibration/training pipeline uses, and auto-grades each response
with Faisal's real reward_func so you see what the pipeline would score.

Works with any OpenAI-compatible endpoint:
  - HuggingFace router (default):  base_url = https://router.huggingface.co/v1
    model = Qwen/Qwen2.5-7B-Instruct ,  key = your HF token (hf_...)
  - Any other (vLLM serve, Together, OpenAI, your Studio): set base_url/model/key in the UI.

Run:
    python3 step3_call_model.py
then open http://localhost:8011 in your browser.
Optional: export QWEN_API_KEY=hf_xxx  to pre-fill the key field.
"""
import json, os, re, ssl, sys, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# macOS python.org builds often ship without linked CA certs -> use certifi's
# bundle so HTTPS to the API verifies. QWEN_INSECURE=1 disables verification
# (localhost dev escape hatch only; not recommended).
if os.environ.get("QWEN_INSECURE") == "1":
    _SSL_CTX = ssl._create_unverified_context()
else:
    try:
        import certifi
        _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        _SSL_CTX = ssl.create_default_context()

# ── reuse the REAL grader from the repo ───────────────────────────────────────
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # tools/ -> repo root
sys.path.insert(0, REPO)
try:
    from reward_func import extract_predicted_answer, extract_gold_answer, _numbers_match
    GRADER_OK = True
except Exception as e:                                  # pragma: no cover
    GRADER_OK = False
    _GRADER_ERR = str(e)

PORT = int(os.environ.get("PORT", "8011"))

# Exact pipeline system prompt (measure_v10_full.py / train_grpo.py)
SYSTEM_PROMPT = ("You are a math problem solver. Think step by step and put your "
                 "final answer in \\boxed{}.")

# The held-out 100 — the EXACT stratified, deduped, disjoint slice train_grpo.py
# reserves (data/skeleton_dataset_v10_clean.json, seed 42, never trained on).
# Browsing these = getting familiar with the set you'll judge reasoning maturity
# on, pre- vs post-RL.
try:
    from holdout_eval import make_skeleton_split
    _, _HOLD = make_skeleton_split(os.path.join(REPO, "data/skeleton_dataset_v10_clean.json"),
                                   n_holdout=100, seed=42)
    _HOLD = sorted(_HOLD, key=lambda r: (r.get("skeleton_type", ""), str(r.get("answer"))))
    PROBLEMS = [(r.get("skeleton_type", "?"), r.get("answer"), r["problem"]) for r in _HOLD]
except Exception as e:
    print(f"WARNING: could not load held-out set ({e}); problem list will be empty.")
    PROBLEMS = []

DEFAULT_BASE = "https://router.huggingface.co/v1"
DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"


def grade(text, gold):
    if not GRADER_OK:
        return {"pred": None, "method": "grader_unavailable", "correct": False}
    pred, method = extract_predicted_answer(text)
    g = extract_gold_answer(str(gold))
    correct = g is not None and pred is not None and _numbers_match(pred, g)
    return {"pred": pred, "method": method, "correct": bool(correct)}


def call_model(base_url, model, api_key, problem, temperature, max_tokens):
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": problem},
        ],
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=180, context=_SSL_CTX) as r:
        data = json.loads(r.read().decode())
    return data["choices"][0]["message"]["content"]


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def _send(self, code, body, ctype="application/json"):
        b = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif self.path == "/problems":
            self._send(200, json.dumps([
                {"concept": c, "gold": g, "problem": p} for c, g, p in PROBLEMS]))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path != "/generate":
            return self._send(404, json.dumps({"error": "not found"}))
        n = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(n) or b"{}")
        try:
            text = call_model(
                req.get("base_url", DEFAULT_BASE), req.get("model", DEFAULT_MODEL),
                req.get("api_key", ""), req["problem"],
                req.get("temperature", 1.0), req.get("max_tokens", 1024))
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            return self._send(200, json.dumps({"error": f"HTTP {e.code} from API: {detail}"}))
        except Exception as e:
            return self._send(200, json.dumps({"error": f"{type(e).__name__}: {e}"}))
        g = grade(text, req.get("gold")) if req.get("gold") is not None else {}
        self._send(200, json.dumps({"text": text, **g}))


PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<title>Step 3 — Call the model</title>
<script>
window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},
 svg:{fontCache:'global'}};
</script>
<script async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-svg.min.js"></script>
<style>
:root{--bg:#f7f7f8;--card:#fff;--line:#e3e3e8;--ink:#1d1d1f;--mut:#6b6b76;--accent:#3257d6;}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
 color:var(--ink);background:var(--bg)}
header{background:#11131a;color:#fff;padding:14px 20px}
header h1{margin:0;font-size:17px;font-weight:600}
header .sub{color:#9aa0b4;font-size:12.5px;margin-top:3px}
.wrap{display:flex;gap:18px;max-width:1180px;margin:18px auto;padding:0 18px}
.col{flex:1;min-width:0}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:14px}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut);margin:0 0 10px}
label{display:block;font-size:12px;color:var(--mut);margin:8px 0 3px}
input,select,textarea{width:100%;padding:7px 9px;border:1px solid var(--line);border-radius:7px;font:inherit;background:#fff}
textarea{resize:vertical}
.row{display:flex;gap:10px}.row>div{flex:1}
button{cursor:pointer;border:0;border-radius:7px;padding:8px 13px;font:inherit;font-weight:600}
.go{background:var(--accent);color:#fff;width:100%;margin-top:10px;padding:10px}
.go:disabled{opacity:.5;cursor:wait}
.plist button{display:block;width:100%;text-align:left;background:#fafafe;border:1px solid var(--line);
 margin-bottom:6px;padding:8px 10px;font-weight:500;border-radius:7px}
.plist button:hover{border-color:var(--accent)}
.plist .c{font-size:11px;color:var(--mut)}
.out{white-space:pre-wrap;word-wrap:break-word;background:#fbfbfd;border:1px solid var(--line);
 border-radius:8px;padding:14px;min-height:80px;max-width:820px}
.verdict{display:flex;gap:14px;align-items:center;margin:10px 0;flex-wrap:wrap}
.badge{padding:4px 11px;border-radius:20px;font-weight:700;font-size:13px}
.ok{background:#e6f6ec;color:#137a37}.no{background:#fdeaea;color:#b3261e}
.pill{font-size:12px;color:var(--mut);background:#eef0f6;padding:3px 9px;border-radius:14px}
.muted{color:var(--mut);font-size:12.5px}
.err{background:#fdeaea;color:#b3261e;padding:10px;border-radius:8px;white-space:pre-wrap}
code{background:#eef0f6;padding:1px 5px;border-radius:4px;font-size:13px}
</style></head><body>
<header><h1>Step 3 · Call the model yourself</h1>
<div class="sub">Qwen2.5-7B-Instruct · exact pipeline system prompt · auto-graded by reward_func.py</div></header>
<div class="wrap">
 <div class="col" style="max-width:330px">
  <div class="panel"><h2>Connection</h2>
   <label>API base URL</label><input id="base" value="">
   <label>Model</label><input id="model" value="">
   <label>API key / token <span class="muted">(stays local)</span></label>
   <input id="key" type="password" placeholder="hf_... or sk-...">
   <div class="row"><div><label>Temperature</label><input id="temp" type="number" step="0.1" value="1.0"></div>
    <div><label>Max tokens</label><input id="max" type="number" value="1024"></div></div>
   <div class="muted" style="margin-top:8px">Temp 1.0 = calibration setting. Try 0.7 / 1.2 to see the spread.</div>
  </div>
  <div class="panel"><h2>Held-out 100 <span id="pcount" class="muted"></span></h2>
   <select id="cfilter" style="margin-bottom:8px"></select>
   <div id="plist" class="plist"></div></div>
 </div>
 <div class="col">
  <div class="panel"><h2>Problem</h2>
   <textarea id="prob" rows="3" placeholder="Click a problem at left, or type your own..."></textarea>
   <div class="row" style="margin-top:8px"><div><label>Gold (for grading, optional)</label><input id="gold"></div>
    <div><label>Concept</label><input id="concept" placeholder="(free-form)"></div></div>
   <button class="go" id="run">Call the model</button>
  </div>
  <div class="panel"><h2>Response</h2>
   <div id="verdict"></div>
   <div id="out" class="out muted">Output will appear here.</div>
  </div>
 </div>
</div>
<script>
const $=id=>document.getElementById(id);
$('base').value=localStorage.base||"%BASE%";
$('model').value=localStorage.model||"%MODEL%";
$('key').value=localStorage.qkey||"%KEY%";
for(const el of ['base','model','key'])$(el).addEventListener('change',e=>{
  localStorage[el==='key'?'qkey':el]=e.target.value;});
let ALLP=[];
fetch('/problems').then(r=>r.json()).then(ps=>{
 ALLP=ps;
 const concepts=[...new Set(ps.map(p=>p.concept))].sort();
 $('cfilter').innerHTML='<option value="">all concepts ('+ps.length+')</option>'+
   concepts.map(c=>`<option value="${c}">${c} (${ps.filter(p=>p.concept===c).length})</option>`).join('');
 $('cfilter').onchange=e=>renderProblems(e.target.value);
 renderProblems('');
});
function renderProblems(filter){
 const list=ALLP.filter(p=>!filter||p.concept===filter);
 $('pcount').textContent='· '+list.length+' shown';
 const d=$('plist'); d.innerHTML='';
 list.forEach(p=>{const b=document.createElement('button');
  b.innerHTML=`<div>${p.problem}</div><div class="c">${p.concept} · gold ${p.gold}</div>`;
  b.onclick=()=>{$('prob').value=p.problem;$('gold').value=p.gold;$('concept').value=p.concept;};
  d.appendChild(b);});
}
$('run').onclick=async()=>{
 const prob=$('prob').value.trim();if(!prob){alert('Enter a problem');return;}
 const btn=$('run');btn.disabled=true;btn.textContent='Calling…';
 $('verdict').innerHTML='';$('out').className='out muted';$('out').textContent='Waiting for the model…';
 try{
  const r=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({base_url:$('base').value,model:$('model').value,api_key:$('key').value,
    problem:prob,gold:$('gold').value||null,temperature:parseFloat($('temp').value),
    max_tokens:parseInt($('max').value)})});
  const j=await r.json();
  if(j.error){$('out').className='err';$('out').textContent=j.error;}
  else{
   $('out').className='out';$('out').textContent=j.text;
   if(j.method){const ok=j.correct;
    $('verdict').innerHTML=`<span class="badge ${ok?'ok':'no'}">${ok?'CORRECT':'WRONG'}</span>`+
     `<span class="pill">grader read: <b>${j.pred}</b></span>`+
     `<span class="pill">via ${j.method}</span>`+
     `<span class="pill">gold ${$('gold').value}</span>`;}
   if(window.MathJax&&MathJax.typesetPromise)MathJax.typesetPromise([$('out')]);
  }
 }catch(e){$('out').className='err';$('out').textContent=e.toString();}
 btn.disabled=false;btn.textContent='Call the model';
};
</script></body></html>
"""
PAGE = (PAGE.replace("%BASE%", DEFAULT_BASE).replace("%MODEL%", DEFAULT_MODEL)
            .replace("%KEY%", os.environ.get("QWEN_API_KEY", "")))


if __name__ == "__main__":
    if not GRADER_OK:
        print(f"WARNING: could not import reward_func ({_GRADER_ERR}); grading disabled.")
    print(f"Step 3 UI  →  http://localhost:{PORT}")
    print("Open it, paste your token, click a problem, hit 'Call the model'. Ctrl-C to stop.")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
