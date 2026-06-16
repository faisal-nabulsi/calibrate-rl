#!/usr/bin/env python3
"""
depth1_calib_analyze.py — per-chain calibration readout for the depth-1 loop.

Consumes a calib.json (tools/sample.py schema: rows with pass_rate, gold, zone,
chain.components) produced by sampling the depth-1 chain pool against ckpt-40, and
emits a per-chain difficulty + diversity report the campaign uses to decide edits:

  - pass_rate (mean over the chain's problems) and n
  - goldilocks fraction: rows with 0.45 <= pass <= 0.55 (the GRPO signal target)
  - in-band fraction: rows in the wider 0.25..0.75 zone
  - too_hard / too_easy fractions (pass==0 / pass==1)  <- the ghost-batch killers
  - top3 answer share (answer-diversity; >0.30 = answer-hackable, the #78 concern)
  - verdict: TOO_HARD | TOO_EASY | LOW_DIVERSITY | IN_BAND  + a suggested direction

  python3 analysis/depth1_calib_analyze.py <calib.json> [--md out.md] [--json out.json]

The verdict/direction is ADVISORY — the edit step (campaign) decides the actual
generator change; this only measures and flags. Difficulty must move via step/
constraint count, never number size (§4); this script never edits anything.
"""
import json, sys, argparse, collections, statistics

GOLD_LO, GOLD_HI = 0.45, 0.55     # strict goldilocks band (GRPO advantage target)
BAND_LO, BAND_HI = 0.25, 0.75     # wider usable band
TOP3_MAX = 0.30                   # answer-diversity gate (share of 3 commonest answers)


def chain_name(r):
    c = r.get("chain") or {}
    comp = c.get("components") or []
    return "chain_" + "__".join(comp) if len(comp) == 2 else r.get("skeleton_type", "?")


def analyze(rows):
    by = collections.defaultdict(list)
    for r in rows:
        by[chain_name(r)].append(r)
    out = {}
    for name, rs in sorted(by.items()):
        ps = [r["pass_rate"] for r in rs]
        ans = [str(r.get("gold")) for r in rs]
        n = len(ps)
        ac = collections.Counter(ans)
        top3 = sum(v for _, v in ac.most_common(3)) / max(1, n)
        gold_frac = sum(1 for p in ps if GOLD_LO <= p <= GOLD_HI) / n
        band_frac = sum(1 for p in ps if BAND_LO <= p <= BAND_HI) / n
        too_hard = sum(1 for p in ps if p == 0.0) / n
        too_easy = sum(1 for p in ps if p == 1.0) / n
        mean = statistics.mean(ps)
        # advisory verdict: difficulty first, then diversity
        if mean < 0.20 or too_hard > 0.60:
            verdict, direction = "TOO_HARD", "ease (fewer steps/constraints)"
        elif mean > 0.80 or too_easy > 0.60:
            verdict, direction = "TOO_EASY", "harden (more steps/constraints)"
        elif top3 > TOP3_MAX:
            verdict, direction = "LOW_DIVERSITY", "diversify answers (widen non-fed inputs)"
        else:
            verdict, direction = "IN_BAND", "leave"
        out[name] = dict(n=n, mean_pass=round(mean, 3), gold_frac=round(gold_frac, 3),
                         band_frac=round(band_frac, 3), too_hard=round(too_hard, 3),
                         too_easy=round(too_easy, 3), top3=round(top3, 3),
                         verdict=verdict, direction=direction)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("calib")
    ap.add_argument("--md")
    ap.add_argument("--json")
    a = ap.parse_args()
    rows = json.load(open(a.calib))
    if isinstance(rows, dict):
        rows = rows.get("results") or rows.get("data") or []
    rep = analyze(rows)

    # overall rollup
    n_chains = len(rep)
    in_band = sum(1 for v in rep.values() if v["verdict"] == "IN_BAND")
    pool_gold = statistics.mean([v["gold_frac"] for v in rep.values()]) if rep else 0
    flagged = {k: v for k, v in rep.items() if v["verdict"] != "IN_BAND"}

    lines = [f"# depth-1 calibration readout — {len(rows)} rows, {n_chains} chains",
             f"in-band chains: **{in_band}/{n_chains}** | mean goldilocks-frac: {pool_gold:.2f}",
             "", f"flagged (need edits): **{len(flagged)}**", "",
             "| chain | n | mean | gold% | too_hard | too_easy | top3 | verdict | direction |",
             "|---|--|--|--|--|--|--|--|---|"]
    for k, v in sorted(rep.items(), key=lambda kv: (kv[1]["verdict"] == "IN_BAND", kv[0])):
        lines.append(f"| {k} | {v['n']} | {v['mean_pass']} | {v['gold_frac']} | "
                     f"{v['too_hard']} | {v['too_easy']} | {v['top3']} | {v['verdict']} | {v['direction']} |")
    md = "\n".join(lines)
    print(md if not a.md else f"in-band {in_band}/{n_chains} | flagged {len(flagged)} | mean gold {pool_gold:.2f}")
    if a.md:
        open(a.md, "w").write(md + "\n")
    if a.json:
        json.dump({"summary": dict(n_rows=len(rows), n_chains=n_chains, in_band=in_band,
                                   mean_gold_frac=round(pool_gold, 3)), "chains": rep},
                  open(a.json, "w"), indent=2)


if __name__ == "__main__":
    main()
