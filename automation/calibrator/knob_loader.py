#!/usr/bin/env python3
"""
knob_loader.py — Phase 0, PR 1 of the auto-calibrator plan (design §2a).

Difficulty knobs for loop concepts live in knobs/<concept>.json instead of inline
literals in the generator bodies. Each param carries:
  value      — what the calibrator LLM may edit (a [lo,hi] range or a choice pool)
  type       — "randint" | "choice" | "const"
  envelope   — hard bounds the value may NEVER exceed (enforced HERE, in code,
               not in any prompt)
  knob_class — §5 taxonomy: "num" (number-size — anti-pattern knob), "C"
               (constraint-count), "S" (structure/method)

Two rule sets are enforced mechanically:
  load time  (ConceptKnobs): every value must sit inside its envelope, types and
             classes must be valid — a hand-edited bad JSON fails fast.
  edit time  (apply_edit): the only sanctioned write path. Rejects edits that
             leave the envelope, rejects ANY widening of a "num"-class value
             ("difficulty via constraints, never number size" becomes a
             validation error, not a prompt instruction), rejects edits to
             locked concepts.

Draw semantics are EXACTLY the inline originals — K.randint -> random.randint,
K.choice -> random.choice on an identical pool — using the same global `random`
module, so identical seeds produce identical problems. Proven by
tests/test_knob_equivalence.py against a fixture generated from the
pre-refactor generator.

The generators' math is untouched; nothing outside knobs/*.json is editable
through this module.
"""
import json
import os
import random

KNOB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knobs")
VALID_TYPES = {"randint", "choice", "const"}
VALID_CLASSES = {"num", "C", "S"}


class KnobError(ValueError):
    """Malformed knob config (bad shape, type, class, or envelope violation)."""


class KnobEditError(KnobError):
    """A proposed edit violates the envelope / knob-class / locked rules."""


def _numeric_atoms(x):
    """Flatten all numbers out of a (possibly nested) value."""
    if isinstance(x, bool):
        return []
    if isinstance(x, (int, float)):
        return [x]
    if isinstance(x, (list, tuple)):
        out = []
        for e in x:
            out.extend(_numeric_atoms(e))
        return out
    return []


def _validate_param(concept, name, spec):
    """Shape + envelope validation for one param spec. Raises KnobError."""
    where = f"{concept}.{name}"
    for key in ("value", "type", "envelope", "knob_class"):
        if key not in spec:
            raise KnobError(f"{where}: missing required key '{key}'")
    t, v, env, kc = spec["type"], spec["value"], spec["envelope"], spec["knob_class"]
    if t not in VALID_TYPES:
        raise KnobError(f"{where}: type {t!r} not in {sorted(VALID_TYPES)}")
    if kc not in VALID_CLASSES:
        raise KnobError(f"{where}: knob_class {kc!r} not in {sorted(VALID_CLASSES)}")

    if t in ("randint", "const"):
        if not (isinstance(v, (list, tuple)) and len(v) == 2
                and all(isinstance(e, int) and not isinstance(e, bool) for e in v)
                and v[0] <= v[1]):
            raise KnobError(f"{where}: {t} value must be [lo, hi] ints with lo<=hi, got {v!r}")
        lo, hi = env
        if not (lo <= v[0] and v[1] <= hi):
            raise KnobError(f"{where}: value {list(v)} exceeds envelope {list(env)}")
    else:  # choice
        if not (isinstance(v, (list, tuple)) and len(v) >= 1):
            raise KnobError(f"{where}: choice value must be a non-empty list, got {v!r}")
        if isinstance(env, (list, tuple)) and len(env) > 0 and all(isinstance(e, str) for e in env):
            # categorical envelope: every option must be a member of the allowed set
            bad = [e for e in v if e not in env]
            if bad:
                raise KnobError(f"{where}: options {bad!r} not in categorical envelope {list(env)}")
        else:
            # numeric envelope [lo, hi]: every numeric atom of every option must fit
            lo, hi = env
            atoms = _numeric_atoms(v)
            if not atoms:
                raise KnobError(f"{where}: numeric envelope {list(env)} but no numeric options in {v!r}")
            out = [a for a in atoms if not (lo <= a <= hi)]
            if out:
                raise KnobError(f"{where}: values {out} exceed envelope {list(env)}")


def _tupled(v):
    """Convert inner lists to tuples so unpacking matches the inline originals."""
    return [tuple(e) if isinstance(e, list) else e for e in v]


class ConceptKnobs:
    """Read-only draw interface for one concept's knob file."""

    def __init__(self, concept, cfg, bank=None):
        self.concept = concept
        self._bank = bank
        self.locked = bool(cfg.get("locked", False))
        if "params" not in cfg or not isinstance(cfg["params"], dict):
            raise KnobError(f"{concept}: knob file needs a 'params' object")
        self.params = cfg["params"]
        for pname, spec in self.params.items():
            _validate_param(concept, pname, spec)

    def _spec(self, param, expect):
        spec = self.params.get(param)
        if spec is None:
            raise KnobError(f"{self.concept}: unknown knob param {param!r}")
        if spec["type"] != expect:
            raise KnobError(f"{self.concept}.{param}: is type {spec['type']!r}, accessed as {expect!r}")
        return spec

    def randint(self, param):
        """Draw exactly like the inline original: random.randint(lo, hi)."""
        lo, hi = self._spec(param, "randint")["value"]
        v = random.randint(lo, hi)
        self._note(param, v)
        return v

    def choice(self, param):
        """Draw exactly like the inline original: random.choice(pool)."""
        v = random.choice(_tupled(self._spec(param, "choice")["value"]))
        self._note(param, v)
        return v

    def const(self, param):
        """Return the configured value verbatim (no RNG consumed).

        NOT recorded in the draw log: const values are identical for every
        row, so they can never produce a per-knob-VALUE pass-rate curve
        (param_vs_passrate), and memoizing generators (complex_modulus_power)
        read them only on the first call — recording would stamp row 1 only.
        """
        return self._spec(param, "const")["value"]

    def _note(self, param, value):
        if self._bank is not None:
            self._bank._record(self.concept, param, value)


class KnobBank:
    """Lazy per-concept loader: K["concept"].randint("param")."""

    def __init__(self, knob_dir=None):
        self.knob_dir = knob_dir or KNOB_DIR
        self._cache = {}
        self._draw_log = None

    def __getitem__(self, concept):
        if concept not in self._cache:
            path = os.path.join(self.knob_dir, concept + ".json")
            try:
                with open(path) as f:
                    cfg = json.load(f)
            except FileNotFoundError:
                raise KnobError(f"no knob file for concept {concept!r} at {path}")
            self._cache[concept] = ConceptKnobs(concept, cfg, bank=self)
        return self._cache[concept]

    # ── draw recording (Phase 0 PR-2, design §2b) ─────────────────────────
    # Value-only logging so gen_clean can stamp each generated row's drawn
    # knob values into metadata ("knobs": {param: value}). Consumes NO RNG and
    # changes NO draw semantics — the PR-1 seed-equivalence guarantee holds.

    def start_draw_log(self):
        """Begin recording draws. Call before invoking one generator."""
        self._draw_log = {}

    def take_draw_log(self):
        """Return draws since start_draw_log() as {concept: {param: value}} and stop."""
        log, self._draw_log = self._draw_log, None
        return log or {}

    def _record(self, concept, param, value):
        if self._draw_log is not None:
            if isinstance(value, tuple):
                value = list(value)  # JSON-friendly
            self._draw_log.setdefault(concept, {})[param] = value


def apply_edit(concept, param, new_value, knob_dir=None, dry_run=False):
    """The ONLY sanctioned write path for knob edits (the calibrator's applier).

    Enforced rules (all in code, none in prompts):
      1. locked concepts reject every edit
      2. the new value must validate against its envelope (and shape/type)
      3. "num"-class values may never be WIDENED: for ranges, the new [lo,hi]
         must sit inside the current one; for pools, no new option may fall
         outside the current numeric min/max. (§4/§5: big numbers make
         too-hard ghosts that teach tedium, not method.)

    Returns the updated param spec; raises KnobEditError on any violation.
    With dry_run=True, validates without writing.
    """
    d = knob_dir or KNOB_DIR
    path = os.path.join(d, concept + ".json")
    try:
        with open(path) as f:
            cfg = json.load(f)
    except FileNotFoundError:
        raise KnobEditError(f"no knob file for concept {concept!r} at {path}")

    if cfg.get("locked"):
        raise KnobEditError(f"{concept}: knob file is locked; edits rejected")
    params = cfg.get("params", {})
    if param not in params:
        raise KnobEditError(f"{concept}: unknown knob param {param!r} "
                            f"(editable: {sorted(params)})")

    spec = params[param]
    old = spec["value"]
    candidate = dict(spec)
    candidate["value"] = new_value
    try:
        _validate_param(concept, param, candidate)  # envelope + shape, in code
    except KnobError as e:
        raise KnobEditError(str(e))

    if spec["knob_class"] == "num":
        if spec["type"] in ("randint", "const"):
            if new_value[0] < old[0] or new_value[1] > old[1]:
                raise KnobEditError(
                    f"{concept}.{param}: 'num'-class range may not be widened "
                    f"({list(old)} -> {list(new_value)}); difficulty via "
                    f"constraint/step count, never number size (CLAUDE.md §4)")
        else:  # choice pool
            old_atoms = _numeric_atoms(old)
            new_atoms = _numeric_atoms(new_value)
            if min(new_atoms) < min(old_atoms) or max(new_atoms) > max(old_atoms):
                raise KnobEditError(
                    f"{concept}.{param}: 'num'-class pool may not gain values "
                    f"outside [{min(old_atoms)}, {max(old_atoms)}]; difficulty "
                    f"via constraint/step count, never number size (CLAUDE.md §4)")

    if not dry_run:
        cfg["params"][param]["value"] = new_value
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(cfg, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    return cfg["params"][param]
