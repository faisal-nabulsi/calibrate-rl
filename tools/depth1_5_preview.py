#!/usr/bin/env python3
"""
depth1_5_preview.py — preview + verify the DEPTH-1.5 de-announced chain surface.

Builds BOTH corpora (announced depth-1 + embedded depth-1.5) and reports:
  A. EXAMPLES — announced vs embedded, same chains (shows the wording change).
  B. ANTI-CHEAT — does the depth-1.5 WORDING overlap depth-1?
       * the three depth-1 "cheat tells" (preamble / curly-quotes / literal V) -> want 0;
       * TEMPLATE overlap: numbers masked + feeder removed, per-chain 4-gram Jaccard of
         the embedded skeletons vs the REAL depth-1 skeletons (the cheat surface). The
         feeder math text + numbers are shared BY DESIGN (controlled variable); this
         isolates the composition/target WORDING a depth-1-trained model could memorize.
  C. INDEPENDENT GOLD CHECK — re-solve both halves of every embedded row with
     check_dataset's own oracles (feeder atomic recomputer + _recompute_target, var->V).

Usage: python3 tools/depth1_5_preview.py [--per 12] [--seed 123] [--examples 5]
"""
import argparse, os, re, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import generate.skeleton_injector_v12 as M
from prep.check_dataset import _recompute_target, _chain_split, RECOMPUTERS

def shingles(text, n=4):
    toks = re.findall(r"[A-Za-z0-9⊕]+", text)
    return {tuple(toks[i:i+n]) for i in range(max(0, len(toks)-n+1))}

def jaccard(a, b):
    return len(a & b) / len(a | b) if (a | b) else 0.0

def mask_nums(t): return re.sub(r"\d+", "#", t)

def build(per, seed, embedded):
    random.seed(seed); M.PROBLEMS.clear()
    if embedded: os.environ["CHAIN_SURFACE"] = "embedded"
    else: os.environ.pop("CHAIN_SURFACE", None)
    M.build(per)
    return [r for r in M.PROBLEMS if r.get("depth") == 1]

def ann_scaffold(p):                       # depth-1 problem minus the quoted feeder
    sub, _ = _chain_split(p)
    return p.replace("“" + sub + "”", " ") if sub else p

def emb_scaffold(r):                        # depth-1.5 problem minus the feeder
    return r["problem"].replace(r["chain"]["feeder_question"].strip(), " ")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=12)
    ap.add_argument("--seed", type=int, default=123)
    ap.add_argument("--examples", type=int, default=5)
    a = ap.parse_args()

    ann = build(a.per, a.seed, embedded=False)
    emb = build(a.per, a.seed, embedded=True)
    chains = sorted({r["skeleton_type"] for r in emb})
    print(f"Built {len(ann)} announced + {len(emb)} embedded rows across {len(chains)} chains\n")

    # ── A. examples ──
    print("=" * 80); print("A. EXAMPLES  (depth-1 announced  vs  depth-1.5 embedded)"); print("=" * 80)
    by_a = {};
    for r in ann: by_a.setdefault(r["skeleton_type"], r)
    for st in chains[:a.examples]:
        ra = by_a.get(st); re_ = next(r for r in emb if r["skeleton_type"] == st)
        print(f"\n[{st}]")
        if ra: print("  D1  : " + ra["problem"].replace("\n", " "))
        print("  D1.5: " + re_["problem"].replace("\n", " "))

    # ── B. anti-cheat ──
    print("\n" + "=" * 80); print("B. ANTI-CHEAT  (does depth-1.5 wording overlap depth-1?)"); print("=" * 80)
    n = len(emb)
    t_pre = sum("Let V be the answer to this problem" in r["problem"] for r in emb)
    t_q = sum(("“" in r["problem"] or "”" in r["problem"]) for r in emb)
    t_V = sum(bool(re.search(r"\bV\b", r["problem"])) for r in emb)
    print(f"  depth-1 'cheat tells' present in the {n} embedded problems:")
    print(f"    'Let V be the answer to this problem' : {100*t_pre/n:5.1f}%   [want 0]")
    print(f"    curly-quoted feeder  “…”              : {100*t_q/n:5.1f}%   [want 0]")
    print(f"    literal standalone  V  token          : {100*t_V/n:5.1f}%   [want 0]")
    # per-chain TEMPLATE overlap (numbers masked, feeder removed): embedded vs real depth-1
    ann_sk = {}; emb_sk = {}
    for r in ann: ann_sk.setdefault(r["skeleton_type"], set()).update(shingles(mask_nums(ann_scaffold(r["problem"]))))
    for r in emb: emb_sk.setdefault(r["skeleton_type"], set()).update(shingles(mask_nums(emb_scaffold(r))))
    sims = [(st, jaccard(emb_sk[st], ann_sk.get(st, set()))) for st in chains]
    vals = [s for _, s in sims]
    mean = sum(vals)/len(vals); md = sorted(vals)[len(vals)//2]
    print(f"\n  TEMPLATE overlap (numbers masked, feeder removed) — embedded vs REAL depth-1, per chain:")
    print(f"    mean {mean:.3f}   median {md:.3f}   (depth-1 vs itself baseline = 1.000)")
    worst = sorted(sims, key=lambda x: -x[1])[:5]
    print("    highest-overlap chains (most depth-1-like wording):")
    for st, s in worst: print(f"      {s:.3f}  {st}")

    # ── C. independent gold check ──
    print("\n" + "=" * 80); print("C. INDEPENDENT GOLD CHECK  (re-solve both halves from scratch)"); print("=" * 80)
    tgt_ok = tgt_bad = feed_ok = feed_unchk = feed_bad = 0; bad = []
    for r in emb:
        ch = r["chain"]; feeder, target = ch["components"]
        V = ch["intermediate_gold"]; ans = int(r["answer"])
        cn = re.sub(r"\b" + re.escape(ch["var"]) + r"\b", "V", ch["target_clause"])
        try: got = _recompute_target(target, cn, V)
        except Exception: got = None
        if got == ans: tgt_ok += 1
        else: tgt_bad += 1; bad.append((r["skeleton_type"], "target", ans, got))
        rc = RECOMPUTERS.get(feeder)
        if rc is None: feed_unchk += 1
        else:
            try: fv = rc(ch["feeder_question"])
            except Exception: fv = None
            if fv == V: feed_ok += 1
            elif fv is None: feed_unchk += 1
            else: feed_bad += 1; bad.append((r["skeleton_type"], "feeder", V, fv))
    print(f"  TARGET step : {tgt_ok}/{n} re-solve to the stored answer   (mismatches: {tgt_bad})")
    print(f"  FEEDER V    : {feed_ok} verified, {feed_unchk} unchecked, {feed_bad} WRONG")
    for st, w, e, g in bad[:12]: print(f"    [{st}] {w}: expected {e}, got {g}")
    print("\nVERDICT:", "OK — embedded golds independently verified"
          if (tgt_bad == 0 and feed_bad == 0) else "MISMATCHES — investigate")

if __name__ == "__main__":
    main()
