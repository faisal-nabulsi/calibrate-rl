#!/usr/bin/env python3
"""
test_knob_equivalence.py — Phase 0 PR-1 acceptance tests (design §2a).

1. EQUIVALENCE: the JSON-driven generators produce byte-identical problems to
   the old inline-literal generators for the same seed. The fixture
   (fixture_pre_refactor_v12.json) was generated from the PRE-refactor
   generate/skeleton_injector_v12.py (main @78725d9): 200 seeds x 7 concepts.
   To re-verify the fixture's provenance: check out that commit and re-run the
   fixture block at the bottom of this file.

2. RANGES: the knob JSONs encode exactly the old inline literals.

3. RULES: the applier rejects envelope violations, num-class widening, and
   locked files; accepts legal in-envelope edits.

Run:  python automation/calibrator/tests/test_knob_equivalence.py   (or pytest)
"""
import importlib.util
import json
import os
import random
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, REPO)

from automation.calibrator.knob_loader import (  # noqa: E402
    KNOB_DIR, KnobBank, KnobEditError, KnobError, apply_edit)

TARGETS = ["triangular_filter_count", "log_laws", "ordered_triple_constraint",
           "constrained_subset_count", "inclusion_exclusion_3set",
           "constrained_divisor_count", "complex_modulus_power"]

# the old inline literals, verbatim from pre-refactor skeleton_injector_v12.py
OLD_INLINE = {
    "triangular_filter_count": {"lim": [800, 6000], "k": [2, 3, 5]},
    "log_laws": {"base": [2, 3, 5], "e1": [10, 16], "e2": [10, 16], "e3": [3, 8]},
    "ordered_triple_constraint": {"N": [10, 20]},
    "constrained_subset_count": {"n": [7, 11], "mod": [3, 4]},
    "inclusion_exclusion_3set": {"U": [200, 900],
                                 "divisor_triples": [[2, 3, 5], [3, 4, 5], [2, 5, 7],
                                                     [3, 5, 7], [2, 3, 7]]},
    "constrained_divisor_count": {
        "num_pool": [360, 420, 480, 504, 540, 600, 630, 660, 720, 756, 792, 840, 900,
                     924, 960, 990, 1008, 1080, 1120, 1152, 1260, 1320, 1440, 1560,
                     1680, 1800, 1980, 2100, 2520],
        "cond": ["odd", "gt", "lt"],
        "gt_thresholds": [6, 8, 10, 12, 15, 20, 24, 30],
        "lt_thresholds": [15, 20, 24, 30, 40, 50, 60]},
    "complex_modulus_power": {"cand_range": [20, 600], "rep_cap": [1, 3]},
}


def _load_injector():
    path = os.path.join(REPO, "generate", "skeleton_injector_v12.py")
    spec = importlib.util.spec_from_file_location("inj_new", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _fixture():
    with open(os.path.join(HERE, "fixture_pre_refactor_v12.json")) as f:
        return json.load(f)


# ----------------------------------------------------------------- equivalence
def test_same_seed_same_problems():
    """old inline ranges == new JSON-driven ranges: same seed -> same problems."""
    m = _load_injector()
    fns = {name: fn for name, fn, _ in m.REGISTRY}
    fix = _fixture()
    checked = 0
    for concept in TARGETS:
        fn = fns[concept]
        for seed_s, expected in fix[concept].items():
            random.seed(int(seed_s))
            r = fn()
            got = None if r is None else [r[0], r[1], r[2]]
            assert got == expected, (
                f"{concept} seed {seed_s}: refactored output diverges from "
                f"pre-refactor fixture\n  old: {expected}\n  new: {got}")
            checked += 1
    assert checked == len(TARGETS) * 200
    print(f"PASS equivalence: {checked} seed-draws identical across {len(TARGETS)} concepts")


def test_json_values_match_old_inline_literals():
    """the knob files encode exactly the ranges/pools the code used to inline."""
    for concept, params in OLD_INLINE.items():
        with open(os.path.join(KNOB_DIR, concept + ".json")) as f:
            cfg = json.load(f)
        for pname, old_value in params.items():
            got = cfg["params"][pname]["value"]
            assert got == old_value, f"{concept}.{pname}: JSON {got} != old inline {old_value}"
    print(f"PASS ranges: knob JSONs match old inline literals for {len(OLD_INLINE)} concepts")


# ------------------------------------------------------------------ rule tests
def _tmp_knobs():
    d = tempfile.mkdtemp(prefix="knobs_test_")
    for fn in os.listdir(KNOB_DIR):
        shutil.copy(os.path.join(KNOB_DIR, fn), d)
    return d


def _expect_reject(exc_substr=None, **kw):
    try:
        apply_edit(**kw)
    except KnobEditError as e:
        if exc_substr:
            assert exc_substr in str(e), f"wrong rejection reason: {e}"
        return
    raise AssertionError(f"edit was NOT rejected: {kw}")


def test_applier_rules():
    d = _tmp_knobs()

    # 1. envelope is a hard wall (enforced in code, not prompt)
    _expect_reject(concept="constrained_subset_count", param="n",
                   new_value=[5, 15], knob_dir=d, exc_substr="envelope")   # 15 > 14
    _expect_reject(concept="log_laws", param="base",
                   new_value=[2, 3, 5, 9], knob_dir=d, exc_substr="envelope")  # 9 > 7

    # 2. num-class may NEVER widen, even inside the envelope
    _expect_reject(concept="ordered_triple_constraint", param="N",
                   new_value=[10, 22], knob_dir=d, exc_substr="widened")   # env allows 25
    _expect_reject(concept="triangular_filter_count", param="lim",
                   new_value=[600, 6000], knob_dir=d, exc_substr="widened")
    _expect_reject(concept="complex_modulus_power", param="cand_range",
                   new_value=[20, 700], knob_dir=d, exc_substr="widened")

    # 3. num-class narrowing is fine
    got = apply_edit("ordered_triple_constraint", "N", [10, 18], knob_dir=d)
    assert got["value"] == [10, 18]

    # 4. C-class may widen within the envelope (the sanctioned v12-style move)
    got = apply_edit("constrained_subset_count", "n", [6, 12], knob_dir=d)
    assert got["value"] == [6, 12]
    got = apply_edit("triangular_filter_count", "k", [2, 3, 5, 7], knob_dir=d)
    assert got["value"] == [2, 3, 5, 7]

    # 5. categorical envelope: members only
    _expect_reject(concept="constrained_divisor_count", param="cond",
                   new_value=["odd", "prime"], knob_dir=d, exc_substr="envelope")

    # 6. locked file rejects everything
    p = os.path.join(d, "log_laws.json")
    with open(p) as f:
        cfg = json.load(f)
    cfg["locked"] = True
    with open(p, "w") as f:
        json.dump(cfg, f)
    _expect_reject(concept="log_laws", param="e3",
                   new_value=[3, 7], knob_dir=d, exc_substr="locked")

    # 7. unknown param / dry_run leaves the file untouched
    _expect_reject(concept="constrained_subset_count", param="nope",
                   new_value=[1, 2], knob_dir=d, exc_substr="unknown")
    before = open(os.path.join(d, "constrained_subset_count.json")).read()
    apply_edit("constrained_subset_count", "mod", [3, 4, 5], knob_dir=d, dry_run=True)
    assert open(os.path.join(d, "constrained_subset_count.json")).read() == before

    # 8. edits round-trip through the loader (a written edit still validates+draws)
    bank = KnobBank(knob_dir=d)
    random.seed(0)
    assert 6 <= bank["constrained_subset_count"].randint("n") <= 12

    shutil.rmtree(d)
    print("PASS rules: envelope, num-no-widening, locked, categorical, dry_run all enforced")


def test_loader_rejects_bad_config():
    d = tempfile.mkdtemp(prefix="knobs_bad_")
    with open(os.path.join(d, "broken.json"), "w") as f:
        json.dump({"params": {"x": {"value": [5, 1], "type": "randint",
                                    "envelope": [0, 10], "knob_class": "C"}}}, f)
    try:
        KnobBank(knob_dir=d)["broken"]
    except KnobError:
        pass
    else:
        raise AssertionError("loader accepted lo>hi randint")
    finally:
        shutil.rmtree(d)
    print("PASS loader: malformed knob file fails fast at load")


if __name__ == "__main__":
    test_same_seed_same_problems()
    test_json_values_match_old_inline_literals()
    test_applier_rules()
    test_loader_rejects_bad_config()
    print("ALL PASS")

# Fixture provenance — run at the PRE-refactor commit to regenerate:
#   import importlib.util, json, random
#   spec = importlib.util.spec_from_file_location("inj_old", "generate/skeleton_injector_v12.py")
#   m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
#   fns = {n: f for n, f, _ in m.REGISTRY}
#   out = {}
#   for name in TARGETS:
#       out[name] = {}
#       for seed in range(200):
#           random.seed(seed); r = fns[name]()
#           out[name][str(seed)] = None if r is None else [r[0], r[1], r[2]]
#   json.dump(out, open("automation/calibrator/tests/fixture_pre_refactor_v12.json", "w"),
#             indent=1, ensure_ascii=False)
