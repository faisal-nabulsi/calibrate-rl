#!/usr/bin/env python3
"""
test_report.py — Phase 0 PR-2 (design §2b): machine-readable calibration report.

Three guarantees, mirroring the schema agreed with Michael in
#calibrate-rl-agents (2026-06-10):

  1. KnobBank draw recording is value-only: identical seeds produce identical
     draws with recording on/off (the PR-1 equivalence guarantee survives),
     and the log contains exactly the drawn (param, value) pairs.
  2. gen_clean stamps "knobs" metadata automatically for knob-driven concepts
     (v12 injector) and stamps nothing for non-knob concepts; the gen-stats
     sidecar carries per-concept raw/kept/survival.
  3. build_report computes every §2b field correctly on a hand-checked
     synthetic calib + pool fixture (zone_frac, pass_rate_hist, truncation,
     ghost_frac, answer stats, param_vs_passrate, dedupe_survival), and
     degrades to nulls without --pool instead of crashing.

Run:  python3 automation/calibrator/tests/test_report.py
"""
import importlib.util
import json
import os
import random
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, REPO)

from automation.calibrator.knob_loader import KnobBank


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ── 1. recorder: seed-equivalent + exact log ────────────────────────────────

def test_recorder():
    K = KnobBank()
    kn = K["triangular_filter_count"]

    random.seed(1234)
    plain = (kn.randint("lim"), kn.choice("k"))

    random.seed(1234)
    K.start_draw_log()
    rec = (kn.randint("lim"), kn.choice("k"))
    log = K.take_draw_log()

    assert plain == rec, f"recording changed draws: {plain} != {rec}"
    assert log == {"triangular_filter_count": {"lim": rec[0], "k": rec[1]}}, log
    # recorder off again: no log accumulates
    kn.randint("lim")
    assert K.take_draw_log() == {}
    print("PASS recorder: value-only logging, identical draws with recording on/off")


# ── 2. gen_clean stamping + sidecar ─────────────────────────────────────────

def test_gen_clean_stamping():
    os.environ["INJECTOR"] = "generate/skeleton_injector_v12.py"
    gc = _load(os.path.join(REPO, "prep/gen_clean.py"), "gc_test")

    rows = gc.generate("triangular_filter_count", 5, seed=42)
    assert len(rows) == 5
    for r in rows:
        assert set(r["knobs"]) == {"lim", "k"}, r.get("knobs")
        assert isinstance(r["knobs"]["lim"], int)

    # non-knob concept: no "knobs" field at all
    rows2 = gc.generate("alternating_cubes", 3, seed=42)
    assert all("knobs" not in r for r in rows2)

    # stamping must not change WHICH problems a seed yields (problems from a
    # run with recording == problems from the pre-stamping code path, because
    # recording consumes no RNG; spot-check determinism across two calls)
    again = gc.generate("triangular_filter_count", 5, seed=42)
    assert [r["problem"] for r in rows] == [r["problem"] for r in again]
    assert [r["knobs"] for r in rows] == [r["knobs"] for r in again]

    # sidecar via main()
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "pool.json")
        sys.argv = ["gen_clean.py", "--concept", "triangular_filter_count",
                    "--n", "5", "--out", out, "--seed", "42"]
        gc.main()
        meta = json.load(open(os.path.join(d, "pool.meta.json")))
        mc = meta["concepts"]["triangular_filter_count"]
        assert mc["raw"] == 5 and mc["kept"] <= 5
        assert mc["survival"] == round(mc["kept"] / mc["raw"], 4)
        pool = json.load(open(out))
        assert all(set(r["knobs"]) == {"lim", "k"} for r in pool)
    print("PASS gen_clean: knobs stamped (knob concepts only), sidecar written")


# ── 3. build_report on a hand-checked fixture ───────────────────────────────

def _mk_row(problem, concept, gold, rewards, texts, zone):
    n = len(rewards)
    pr = sum(rewards) / n
    return {"problem": problem, "skeleton_type": concept, "gold": str(gold),
            "pass_rate": pr, "correct": int(sum(rewards)), "total_rollouts": n,
            "zone": zone, "rollout_rewards": rewards, "rollout_texts": texts}


def test_build_report():
    ac = _load(os.path.join(REPO, "analysis/analyze_calibration.py"), "ac_test")

    BOX = "Reasoning... \\boxed{7}."     # has \boxed -> not truncated
    CUT = "Reasoning that never ends"    # no \boxed -> truncated
    rows = [
        # concept A: 4 problems, K=4. correct counts: 0, 2, 4, 3
        _mk_row("pA1", "A", 5, [0, 0, 0, 0], [CUT, CUT, BOX, BOX], "too_hard"),
        _mk_row("pA2", "A", 5, [1, 1, 0, 0], [BOX, BOX, BOX, BOX], "goldilocks"),
        _mk_row("pA3", "A", 9, [1, 1, 1, 1], [BOX, BOX, BOX, BOX], "too_easy"),
        _mk_row("pA4", "A", 2, [1, 1, 1, 0], [BOX, BOX, BOX, BOX], "borderline"),
        # concept B: 1 problem
        _mk_row("pB1", "B", 3, [1, 0, 1, 0], [BOX, CUT, BOX, BOX], "goldilocks"),
    ]
    pool = [
        {"problem": "pA1", "skeleton_type": "A", "knobs": {"n": 7}},
        {"problem": "pA2", "skeleton_type": "A", "knobs": {"n": 7}},
        {"problem": "pA3", "skeleton_type": "A", "knobs": {"n": 9}},
        {"problem": "pA4", "skeleton_type": "A", "knobs": {"n": 9}},
        {"problem": "pB1", "skeleton_type": "B"},               # no knobs stamped
    ]
    meta = {"concepts": {"A": {"raw": 5, "kept": 4, "survival": 0.8}}}

    rep = ac.build_report(rows, "fixture.json", pool, meta)
    assert rep["schema_version"] == 1
    assert rep["n_problems"] == 5 and rep["rollouts"] == 4

    A = rep["concepts"]["A"]
    assert A["zone_frac"] == {"too_easy": 0.25, "goldilocks": 0.25,
                              "borderline": 0.25, "too_hard": 0.25}
    assert A["pass_rate_hist"] == [1, 0, 1, 1, 1]          # counts of correct=0..4
    assert A["truncation_rate"] == round(2 / 16, 4)         # 2 CUT of 16 rollouts
    assert A["ghost_frac"] == 0.5                           # pA1 (0/4) + pA3 (4/4)
    assert A["answer_top3_share"] == 1.0                    # golds 5,5,9,2 -> top3 covers all... (5:2, 9:1, 2:1) = 4/4
    # entropy of {5:2, 9:1, 2:1} = 1.5 bits
    assert A["answer_entropy"] == 1.5
    assert A["dedupe_survival"] == 0.8
    # param_vs_passrate: n=7 -> mean(0.0, 0.5) = 0.25 over 2; n=9 -> mean(1.0, 0.75) = 0.875 over 2
    pv = A["param_vs_passrate"]["n"]
    assert pv["7"] == {"pass_rate": 0.25, "n": 2}, pv
    assert pv["9"] == {"pass_rate": 0.875, "n": 2}, pv
    # failure_modes present (classifier importable) with sane mass
    if A["failure_modes"] is not None:
        fm = dict(A["failure_modes"])
        n_cl = fm.pop("n_classified")
        assert n_cl == 3                                    # pA1, pA2, pA4 have wrong rollouts
        assert abs(sum(fm.values()) - 1.0) < 1e-6

    B = rep["concepts"]["B"]
    assert B["param_vs_passrate"] is None                   # pool row had no knobs
    assert B["dedupe_survival"] is None                     # not in sidecar
    assert B["ghost_frac"] == 0.0

    O = rep["overall"]
    assert O["truncation_rate"] == round(3 / 20, 4)
    assert O["ghost_frac"] == 0.4
    assert O["mean_pass"] == round((0.0 + 0.5 + 1.0 + 0.75 + 0.5) / 5, 4)

    # degraded mode: no pool, no sidecar -> nulls, no crash
    rep2 = ac.build_report(rows, "fixture.json", None, None)
    assert rep2["concepts"]["A"]["param_vs_passrate"] is None
    assert rep2["concepts"]["A"]["dedupe_survival"] is None
    print("PASS build_report: all §2b fields hand-verified; nulls without --pool")


if __name__ == "__main__":
    test_recorder()
    test_gen_clean_stamping()
    test_build_report()
    print("ALL PASS")
