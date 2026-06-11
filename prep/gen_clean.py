"""
gen_clean.py  —  generate skeleton problems and clean them in one pass.

Merges the v11 skeleton injector (generation) with Michael's clean_dataset.py
(continued_fraction gold-fix + dedupe-by-text), so you go straight from a
concept name to a verified, deduped training pool.

Examples:
    # 200 count_pythagorean problems, cleaned
    python3 prep/gen_clean.py --concept count_pythagorean --n 200 \
        --out data/cp_pool.json

    # whole registry (depth-0 only), 150 each
    python3 prep/gen_clean.py --concept all --n 150 --out data/v12_pool.json

Note: this does NOT calibrate (goldilocks zones need GPU rollouts via
sample.py / measure_environment.py). It only produces a clean, diverse pool.
"""
import argparse, importlib.util, json, os, random, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

inj   = _load(os.path.join(REPO, os.environ.get("INJECTOR", "generate/skeleton_injector_v11.py")), "inj")
clean = _load(os.path.join(REPO, "prep/clean_dataset.py"), "clean")  # for parse_cf / cf_value


def generate(concept, n, seed):
    """Generate up to n rows for one concept (or 'all' depth-0 concepts)."""
    random.seed(seed)
    gens = {name: fn for name, fn, _ in inj.REGISTRY}
    if concept != "all" and concept not in gens:
        sys.exit(f"unknown concept '{concept}'. options: {sorted(gens)}")

    targets = (
        [c for c in gens if c not in inj.DEPTH1_PARTNERS]
        if concept == "all" else [concept]
    )
    # Phase 0 PR-2 (design §2b): if the injector draws through a KnobBank
    # (v12+ exposes it as module-level `K`), record each row's drawn knob
    # values and stamp them into row metadata. Automatic for knob-driven
    # concepts; non-knob concepts simply record nothing and get no field.
    bank = getattr(inj, "K", None)
    can_record = hasattr(bank, "start_draw_log")
    rows = []
    for name in targets:
        fn = gens[name]
        made, guard = 0, 0
        while made < n and guard < n * 200:           # guard against low-cardinality generators
            guard += 1
            if can_record:
                bank.start_draw_log()
            r = fn()
            draws = bank.take_draw_log().get(name, {}) if can_record else {}
            if r is None:
                continue
            row = {"problem": r[0], "answer": str(r[1]),
                   "skeleton_type": name, "depth": 0}
            if draws:
                row["knobs"] = draws
            rows.append(row)
            made += 1
    return rows


def clean_rows(rows):
    """Apply Michael's two fixes: recompute continued_fraction golds, dedupe by text."""
    fixed = unparsed = 0
    for r in rows:
        if r.get("skeleton_type") != "continued_fraction":
            continue
        x, d = clean.parse_cf(r["problem"])
        if x is None:
            unparsed += 1
            continue
        correct = str(clean.cf_value(x, d))
        if str(r["answer"]) != correct:
            r["answer"] = correct
            fixed += 1
    seen, deduped = set(), []
    for r in rows:
        if r["problem"] in seen:
            continue
        seen.add(r["problem"])
        deduped.append(r)
    return deduped, fixed, unparsed, len(rows) - len(deduped)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--concept", required=True, help="concept name or 'all'")
    ap.add_argument("--n", type=int, default=200, help="target rows per concept (pre-dedupe)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    raw = generate(args.concept, args.n, args.seed)
    deduped, fixed, unparsed, dropped = clean_rows(raw)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(deduped, open(args.out, "w"), indent=2)

    from collections import Counter
    by_c = Counter(r["skeleton_type"] for r in deduped)
    ans  = Counter(r["skeleton_type"] for r in deduped)  # placeholder

    # Phase 0 PR-2 (design §2b): gen-stats sidecar. dedupe_survival is a
    # gen-time fact, so it rides next to the pool, not inside it (the row list
    # stays a plain list for every downstream consumer).
    raw_by_c = Counter(r["skeleton_type"] for r in raw)
    meta = {
        "generated_by": "prep/gen_clean.py",
        "injector": os.environ.get("INJECTOR", "generate/skeleton_injector_v11.py"),
        "seed": args.seed,
        "requested_per_concept": args.n,
        "concepts": {
            c: {"raw": raw_by_c[c], "kept": by_c.get(c, 0),
                "survival": round(by_c.get(c, 0) / raw_by_c[c], 4)}
            for c in sorted(raw_by_c)
        },
    }
    meta_path = os.path.splitext(args.out)[0] + ".meta.json"
    json.dump(meta, open(meta_path, "w"), indent=2)

    print(f"generated (raw):            {len(raw)}")
    print(f"continued_fraction golds fixed: {fixed}" + (f"  (UNPARSED: {unparsed})" if unparsed else ""))
    print(f"duplicate rows removed:     {dropped}")
    print(f"-> {args.out}: {len(deduped)} unique rows")
    print(f"-> {meta_path}: gen-stats sidecar (dedupe survival per concept)")
    for c, k in by_c.most_common():
        n_ans = len(set(r["answer"] for r in deduped if r["skeleton_type"] == c))
        print(f"     {c:<28} {k:>4} rows   {n_ans:>3} distinct answers")
    if len(deduped) < args.n * (1 if args.concept != "all" else len(by_c)) * 0.5:
        print("\n  WARNING: low yield after dedupe — generator likely has limited cardinality."
              "\n  Widen its parameter range before relying on this pool for training.")


if __name__ == "__main__":
    main()
