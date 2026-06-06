"""
Produce a verified-clean copy of a skeleton dataset for training.

Two fixes, both surfaced by check_dataset.py on v10:
  1. continued_fraction wrong golds. One generator version rendered the problem
     at depth D but computed the answer at depth D+2 (verified: every wrong gold
     == cf(x, depth+2)). We recompute EVERY continued_fraction gold from the
     stated (base, depth) with exact Fraction arithmetic. Validated: 186/200
     stored golds already reproduce exactly; only the 14 depth+2-bug rows change.
  2. Duplicate rows. v10 has ~1850 exact-duplicate problems (an artifact of
     accumulating multiple generator passes). We dedupe by problem text, keeping
     the first occurrence. After (1), no problem text carries conflicting golds,
     so dedupe-by-text is lossless.

Usage:
    python3 clean_dataset.py data/skeleton_dataset_v10.json data/skeleton_dataset_v10_clean.json
"""
import sys, re, json
from fractions import Fraction


def parse_cf(p):
    """Return (base_x, depth) for any of the 6 continued_fraction phrasings."""
    m = re.search(r"value of\s*(\d+)\s*\+\s*\d+\s*/", p)              # "The value of X+1/(...)"
    if m:
        x = int(m.group(1))
        return x, p.replace(" ", "").count(f"{x}+1/") + 1
    m = re.search(r"with (\d+) levels of (\d+)", p)                    # "with L levels of X"
    if m: return int(m.group(2)), int(m.group(1))
    m = re.search(r"repeats (\d+) for (\d+) levels", p)               # "repeats X for L levels"
    if m: return int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d+)-level continued fraction built from (\d+)", p)
    if m: return int(m.group(2)), int(m.group(1))
    m = re.search(r"with (\d+) total (\d+)'?s", p)                    # "with N total X's"
    if m: return int(m.group(2)), int(m.group(1))
    return None, None


def cf_value(x, depth):
    v = Fraction(x)
    for _ in range(depth - 1):
        v = x + 1 / v
    return v.numerator + v.denominator


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "data/skeleton_dataset_v10.json"
    dst = sys.argv[2] if len(sys.argv) > 2 else "data/skeleton_dataset_v10_clean.json"
    rows = json.load(open(src))

    # 1. fix continued_fraction golds
    fixed = unparsed = 0
    for r in rows:
        if r.get("skeleton_type") != "continued_fraction":
            continue
        x, d = parse_cf(r["problem"])
        if x is None:
            unparsed += 1
            continue
        correct = str(cf_value(x, d))
        if str(r["answer"]) != correct:
            r["answer"] = correct
            fixed += 1

    # 2. dedupe by problem text (first occurrence wins; lossless after step 1)
    seen, deduped = set(), []
    for r in rows:
        if r["problem"] in seen:
            continue
        seen.add(r["problem"])
        deduped.append(r)

    json.dump(deduped, open(dst, "w"))
    print(f"src {src}: {len(rows)} rows")
    print(f"  continued_fraction golds corrected: {fixed}"
          + (f"  (UNPARSED: {unparsed} — left as-is!)" if unparsed else ""))
    print(f"  duplicate rows removed: {len(rows) - len(deduped)}")
    print(f"  -> {dst}: {len(deduped)} rows")


if __name__ == "__main__":
    main()
