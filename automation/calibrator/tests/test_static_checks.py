#!/usr/bin/env python3
"""
Tests for static_checks.py (Phase 0 PR-3, design §2c).

  1. unit: each check's pass/fail logic on hand-built rows, including the
     exact thresholds (>= 0.90 survival, <= 0.30 top3 — boundaries PASS);
  2. gold check: mismatch detection, conflicting golds, no-recomputer
     UNCHECKED, recomputer-parses-nothing FAIL;
  3. CLI: exit 0 on a passing concept, exit 1 when a threshold is forced
     impossible, and determinism (same concept twice -> identical stdout).

Run:  python3 automation/calibrator/tests/test_static_checks.py
"""
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SC_PATH = os.path.join(HERE, "..", "static_checks.py")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


sc = _load(SC_PATH, "sc_under_test")


def rows_of(pairs):
    return [{"problem": p, "answer": str(a), "skeleton_type": "t"} for p, a in pairs]


def test_dedupe():
    # 10 rows, 9 unique -> 0.90 exactly: boundary must PASS (>=)
    r = rows_of([(f"p{i}", i) for i in range(9)] + [("p0", 0)])
    res = sc.check_dedupe(r, 0.90)
    assert res["ok"] is True, res
    # 10 rows, 8 unique -> 0.80: FAIL
    r = rows_of([(f"p{i}", i) for i in range(8)] + [("p0", 0), ("p1", 1)])
    assert sc.check_dedupe(r, 0.90)["ok"] is False
    # empty -> FAIL, never a divide-by-zero
    assert sc.check_dedupe([], 0.90)["ok"] is False
    print("PASS dedupe: boundary 0.90 passes, below fails, empty fails")


def test_top3():
    # 10 unique answers over 10 rows -> share 0.30 exactly: boundary PASSes (<=)
    r = rows_of([(f"p{i}", i) for i in range(10)])
    assert sc.top3_share([x["answer"] for x in r]) == 0.30
    assert sc.check_top3(r, 0.30)["ok"] is True
    # concentrate: answers 1,1,1,1,2,2,2,3,3,3 -> top3 = 1.0 -> FAIL
    r = rows_of([(f"p{i}", a) for i, a in enumerate([1, 1, 1, 1, 2, 2, 2, 3, 3, 3])])
    assert sc.check_top3(r, 0.30)["ok"] is False
    # duplicates must NOT double-count: 5 dup rows of answer 7 + 7 unique others
    r = rows_of([("same", 7)] * 5 + [(f"p{i}", i) for i in range(7)])
    share_deduped = 3 / 8  # 8 unique problems, top3 = 3
    res = sc.check_top3(r, share_deduped)
    assert res["ok"] is True, res
    assert sc.check_top3(r, share_deduped - 0.01)["ok"] is False
    assert sc.check_top3([], 0.30)["ok"] is False
    print("PASS top3: boundary 0.30 passes, concentration fails, dedupe before measuring")


def test_golds():
    good = lambda p: int(p.split("=")[1])          # parses "x=N" -> N
    blind = lambda p: None                          # parses nothing
    half = lambda p: int(p.split("=")[1]) if p.startswith("ok") else None

    # all correct -> PASS
    r = rows_of([(f"x={i}", i) for i in range(5)])
    assert sc.check_golds(r, good)["ok"] is True
    # one wrong gold -> FAIL with example
    r = rows_of([(f"x={i}", i) for i in range(4)] + [("x=9", 8)])
    res = sc.check_golds(r, good)
    assert res["ok"] is False and "stored=8" in res["detail"], res
    # conflicting golds (same text, two answers) -> FAIL even if recomputer absent
    r = rows_of([("x=1", 1), ("x=1", 2)])
    assert sc.check_golds(r, None)["ok"] is False
    assert sc.check_golds(r, good)["ok"] is False
    # no recomputer, no conflicts -> UNCHECKED (ok=None), not a silent pass
    r = rows_of([("x=1", 1)])
    res = sc.check_golds(r, None)
    assert res["ok"] is None and "UNCHECKED" in res["detail"]
    # recomputer that parses zero rows -> FAIL (gate would verify nothing)
    res = sc.check_golds(r, blind)
    assert res["ok"] is False and "NOTHING" in res["detail"], res
    # partial coverage with all parsed rows correct -> PASS, coverage reported
    r = rows_of([("ok=3", 3), ("nope", 99)])
    res = sc.check_golds(r, half)
    assert res["ok"] is True and "1/2" in res["detail"], res
    print("PASS golds: mismatch, conflict, UNCHECKED, zero-coverage, partial-coverage")


def test_report_exit_logic():
    # UNCHECKED (ok=None) must not fail the run; any ok=False must
    res = {"c1": {"golds": {"ok": None, "detail": "UNCHECKED"},
                  "dedupe": {"ok": True, "detail": ""},
                  "top3": {"ok": True, "detail": ""}}}
    assert sc.report(res, 1) is True
    res["c1"]["top3"] = {"ok": False, "detail": ""}
    assert sc.report(res, 1) is False
    print("PASS report: UNCHECKED is not a failure; any FAIL flips the verdict")


def test_cli():
    env = dict(os.environ)
    base = [sys.executable, SC_PATH, "--concept", "triangular_filter_count", "--n", "60"]
    a = subprocess.run(base, capture_output=True, text=True, cwd=REPO, env=env)
    assert a.returncode == 0, a.stdout + a.stderr
    assert "STATIC CHECKS: PASS" in a.stdout
    # determinism: identical stdout on a second run
    b = subprocess.run(base, capture_output=True, text=True, cwd=REPO, env=env)
    assert a.stdout == b.stdout, "same seed+concept must reproduce byte-identical report"
    # force an impossible threshold -> nonzero exit
    c = subprocess.run(base + ["--max-top3", "0.0001"],
                       capture_output=True, text=True, cwd=REPO, env=env)
    assert c.returncode == 1 and "STATIC CHECKS: FAIL" in c.stdout, c.stdout
    # unknown concept -> nonzero exit
    d = subprocess.run([sys.executable, SC_PATH, "--concept", "nope", "--n", "5"],
                       capture_output=True, text=True, cwd=REPO, env=env)
    assert d.returncode == 1
    print("PASS cli: exit 0 on pass, exit 1 on threshold fail / unknown concept, deterministic")


if __name__ == "__main__":
    test_dedupe()
    test_top3()
    test_golds()
    test_report_exit_logic()
    test_cli()
    print("ALL PASS")
