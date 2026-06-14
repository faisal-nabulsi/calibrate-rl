"""Tier 0 — deterministic checks (LegalEval v6 §6.5), no LLM.

String/arithmetic checks for the prompts whose gold is mechanically
verifiable: B1 (defined-term set), D2 (uptime math + citations),
D3 (required amendment elements). Results are stored on each grade record
as an advisory signal: score.py routes any judge/Tier-0 disagreement to the
human-confirm queue rather than silently trusting either side.

run_checks() returns None for prompts with no deterministic layer.
"""

import re

# B1 gold list — 20 top-level terms + nested "Control" (the discriminator).
# Rubric Coverage banding: 18-20 found = 4, 15-17 = 3, 12-14 = 2, <12 = 1.
B1_TERMS = [
    "Action", "Affiliate", "Agreement", "Change Order", "Confidential Information",
    "Customer", "Customer Contract Manager", "Customer Equipment", "Customer Materials",
    "Deliverables", "Disclosing Party", "Force Majeure Event",
    "Intellectual Property Rights", "Law", "Losses", "Permitted Subcontractor",
    "Person", "Receiving Party", "Services", "Term",
]

# D2 gold math: 1,086 min downtime / 43,200 min => 97.486% uptime.
# Accept anything in the rounding band 97.48-97.5 (see rubric fix).
D2_UPTIME_LOW, D2_UPTIME_HIGH = 97.48, 97.50


def _b1(text: str) -> dict:
    # Terms appear quoted in a glossary row; substring match is enough here
    # because every gold term is distinctive in context.
    found = [t for t in B1_TERMS if t in text]
    missing = [t for t in B1_TERMS if t not in found]
    n = len(found)
    band = 4 if n >= 18 else 3 if n >= 15 else 2 if n >= 12 else 1
    control = bool(re.search(r'["“‘\']?Control["”’\']?', text))
    checks = {
        "terms_found": n,
        "terms_missing": missing,
        "coverage_band_from_terms": band,
        "control_subdefinition_captured": control,
    }
    flags = []
    if n < 18:
        flags.append(f"only {n}/20 gold terms found")
    if not control:
        flags.append("nested 'Control' sub-definition not captured")
    return {"checks": checks, "flags": flags}


def _d2(text: str) -> dict:
    pcts = [float(m) for m in re.findall(r"9[0-9]\.\d+(?=\s*%)", text)]
    uptime_stated = [p for p in pcts if 96.0 < p < 98.5]  # candidate uptime figures
    uptime_ok = any(D2_UPTIME_LOW <= p <= D2_UPTIME_HIGH for p in uptime_stated)
    checks = {
        "uptime_figures_stated": uptime_stated,
        "uptime_in_accepted_band": uptime_ok,        # 97.48-97.5
        "cites_5_2": bool(re.search(r"5\.2", text)),
        "cites_9_1": bool(re.search(r"9\.1", text)),
        "preserves_9_2": bool(re.search(r"9\.2", text)),
        "reserves_rights": "reserv" in text.lower(),
    }
    flags = [k for k, v in checks.items()
             if k != "uptime_figures_stated" and not v]
    return {"checks": checks, "flags": flags}


def _d3(text: str) -> dict:
    low = text.lower()
    checks = {
        "labeled_amendment_no_1": bool(re.search(r"amendment\s+no\.?\s*1", low)),
        "continuity_clause": "full force and effect" in low,
        "thirty_day_payment": bool(re.search(r"thirty\s*\(30\)|30\s*days?", low)),
        "ten_day_cure": bool(re.search(r"ten\s*\(10\)|10[-\s]day", low)),
        "interest_per_month": bool(re.search(r"1(\.0)?\s*%", text)) and "per month" in low,
        "twenty_day_dispute": bool(re.search(r"twenty\s*\(20\)|20\s*days?", low)),
    }
    flags = [k for k, v in checks.items() if not v]
    return {"checks": checks, "flags": flags}


CHECKERS = {"B1": _b1, "D2": _d2, "D3": _d3}


def run_checks(prompt_id: str, response_text: str) -> dict | None:
    checker = CHECKERS.get(prompt_id)
    return checker(response_text) if checker else None
