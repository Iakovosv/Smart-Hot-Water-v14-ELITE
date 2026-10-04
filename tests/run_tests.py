"""Validation tests for GSW Smart Hot Water.

Runs without Home Assistant or pytest: `python3 tests/run_tests.py`.

Checks:
  1. The blueprint YAML parses and has the required top-level structure.
  2. Every `!input <name>` reference matches a declared blueprint input.
  3. Every declared input has a name and a selector.
  4. All Jinja templates parse (catches unclosed if/for, bad syntax).
  5. The installer copies the blueprint and is idempotent.
  6. manifest.json / version.json are valid and consistent.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

import yaml
from jinja2 import Environment

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "custom_components" / "gsw_hotwater"
BLUEPRINT_DIR = PKG / "blueprints"
BLUEPRINTS = ["gsw_smart_hot_water.yaml", "gsw_boiler_safety.yaml"]

FAILURES: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        print(f"  ok   - {msg}")
    else:
        print(f"  FAIL - {msg}")
        FAILURES.append(msg)


class _InputTag:
    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:  # pragma: no cover
        return f"<input:{self.name}>"


def _input_constructor(loader, node):
    return _InputTag(loader.construct_scalar(node))


yaml.SafeLoader.add_constructor("!input", _input_constructor)


def load_blueprint(name: str) -> dict:
    return yaml.load((BLUEPRINT_DIR / name).read_text(encoding="utf-8"),
                     Loader=yaml.SafeLoader)


def walk(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)
    else:
        yield obj


def test_structure(bp: dict, name: str = "") -> None:
    print("test_structure")
    check("blueprint" in bp, "has top-level 'blueprint' key")
    meta = bp.get("blueprint", {})
    check(meta.get("domain") == "automation", "domain is 'automation'")
    check(bool(meta.get("name")), "blueprint has a name")
    check(bp.get("mode") == "single", "mode is 'single' (no self-cancel)")
    check(bool(bp.get("trigger")), "has at least one trigger")
    check(bool(bp.get("action")), "has actions")
    if name == "gsw_smart_hot_water.yaml":
        triggers = bp.get("trigger", [])
        ids = {t.get("id") for t in triggers if isinstance(t, dict)}
        check({"tick", "boost"} <= ids, "main blueprint triggers include tick/boost")
    if name == "gsw_boiler_safety.yaml":
        check(not bp.get("condition"), "watchdog has no blocking top-level condition")


def test_inputs(bp: dict) -> None:
    print("test_inputs")
    declared = set(bp.get("blueprint", {}).get("input", {}).keys())
    referenced = set()
    for node in walk(bp.get("variables", {})):
        if isinstance(node, _InputTag):
            referenced.add(node.name)
    for node in walk(bp.get("action", [])):
        if isinstance(node, _InputTag):
            referenced.add(node.name)
    for node in walk(bp.get("trigger", [])):
        if isinstance(node, _InputTag):
            referenced.add(node.name)

    unknown = referenced - declared
    check(not unknown, f"all !input references declared (unknown: {sorted(unknown)})")

    unused = declared - referenced
    check(not unused, f"no unused inputs (unused: {sorted(unused)})")

    inputs = bp.get("blueprint", {}).get("input", {})
    for key, spec in inputs.items():
        check("name" in spec, f"input '{key}' has a name")
        check("selector" in spec, f"input '{key}' has a selector")

    # Schedules: 6 independent, minute-accurate slots (main blueprint only)
    if "schedule_1_enabled" in inputs:
        for i in range(1, 7):
            for suffix in ("enabled", "time", "temp"):
                check(f"schedule_{i}_{suffix}" in inputs,
                      f"schedule_{i}_{suffix} input exists")


def test_jinja(bp: dict) -> None:
    print("test_jinja")
    env = Environment()
    count = 0
    bad = []
    for node in walk(bp):
        if isinstance(node, str) and ("{{" in node or "{%" in node):
            count += 1
            try:
                env.parse(node)
            except Exception as exc:  # noqa: BLE001
                bad.append((node[:60], str(exc)))
    check(not bad, f"all {count} Jinja templates parse")
    for snippet, err in bad:
        print(f"        bad template: {snippet!r} -> {err}")


def test_installer() -> None:
    print("test_installer")
    sys.path.insert(0, str(PKG))
    import installer  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmp:
        r1 = installer.install_blueprints(tmp, force=True)
        check(r1.get("ok"), "first install succeeds")
        target_dir = Path(tmp) / "blueprints" / "automation" / "gsw_hotwater"
        for name in BLUEPRINTS:
            target = target_dir / name
            check(target.exists(), f"blueprint copied: {name}")
            check(target.read_text(encoding="utf-8") == (BLUEPRINT_DIR / name).read_text(encoding="utf-8"),
                  f"copied content matches source: {name}")
        r2 = installer.install_blueprints(tmp, force=False)
        check(r2.get("ok") and r2.get("changed") is False,
              "second install is a no-op (same version)")
        check(installer.read_version() != "0", "version is read from version.json")


def test_manifest() -> None:
    print("test_manifest")
    manifest = json.loads((PKG / "manifest.json").read_text(encoding="utf-8"))
    version = json.loads((PKG / "version.json").read_text(encoding="utf-8"))
    check(manifest.get("domain") == "gsw_hotwater", "manifest domain correct")
    check(manifest.get("version") == version.get("version"),
          "manifest version matches version.json")
    check(bool(manifest.get("codeowners")), "manifest has codeowners")
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    check(bool(hacs.get("name")), "hacs.json has a name")

    # HACS integration requirements
    for key in ("domain", "documentation", "issue_tracker", "codeowners", "name", "version"):
        check(key in manifest, f"manifest has '{key}' (HACS requirement)")
    check((ROOT / "brand" / "icon.png").exists(), "brand/icon.png exists (HACS requirement)")
    check((ROOT / "brand" / "icon@2x.png").exists(), "brand/icon@2x.png exists")

    # Config flow so HA actually loads the integration
    check(manifest.get("config_flow") is True, "manifest enables config_flow")
    check((PKG / "config_flow.py").exists(), "config_flow.py exists")
    check((PKG / "strings.json").exists(), "strings.json exists")
    for lang in ("en", "el"):
        tf = PKG / "translations" / f"{lang}.json"
        check(tf.exists(), f"translations/{lang}.json exists")
        json.loads(tf.read_text(encoding="utf-8"))  # must be valid JSON


def test_action_shape(bp: dict) -> None:
    print("test_action_shape")
    errors: list[str] = []

    def walk_sequence(steps, path="action"):
        if not isinstance(steps, list):
            errors.append(f"{path} is not a list")
            return
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                errors.append(f"{path}[{i}] is not a mapping")
                continue
            keys = set(step.keys())
            known = {"service", "action", "if", "choose", "repeat", "delay",
                     "wait_template", "wait_for_trigger", "stop", "variables",
                     "parallel", "sequence", "condition", "continue_on_timeout",
                     "alias", "enabled", "target", "data"}
            if not (keys & known):
                errors.append(f"{path}[{i}] has no recognised action key: {keys}")
            if "if" in step:
                if "then" not in step:
                    errors.append(f"{path}[{i}] if without then")
                else:
                    walk_sequence(step["then"], f"{path}[{i}].then")
                if "else" in step:
                    walk_sequence(step["else"], f"{path}[{i}].else")
            if "choose" in step:
                for j, opt in enumerate(step["choose"]):
                    if "conditions" not in opt or "sequence" not in opt:
                        errors.append(f"{path}[{i}].choose[{j}] missing conditions/sequence")
                    else:
                        walk_sequence(opt["sequence"], f"{path}[{i}].choose[{j}]")
                if "default" in step:
                    walk_sequence(step["default"], f"{path}[{i}].default")
            if "repeat" in step:
                if "sequence" not in step["repeat"]:
                    errors.append(f"{path}[{i}].repeat missing sequence")
                else:
                    walk_sequence(step["repeat"]["sequence"], f"{path}[{i}].repeat")
                if "until" not in step["repeat"] and "count" not in step["repeat"] \
                        and "while" not in step["repeat"] and "for_each" not in step["repeat"]:
                    errors.append(f"{path}[{i}].repeat missing until/count/while")

    walk_sequence(bp.get("action", []))
    check(not errors, "action steps have a valid shape")
    for e in errors:
        print(f"        {e}")


def test_no_forbidden_mentions() -> None:
    print("test_no_forbidden_mentions")
    pattern = re.compile(r"openhands", re.IGNORECASE)
    self_path = Path(__file__).resolve()
    offenders = []
    for path in ROOT.rglob("*"):
        if path.is_file() and ".git" not in path.parts and path.resolve() != self_path and path.suffix in {
            ".yaml", ".yml", ".py", ".md", ".json", ".txt"
        }:
            if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                offenders.append(str(path.relative_to(ROOT)))
    check(not offenders, f"no 'openhands' mentions (found: {offenders})")


def main() -> int:
    for name in BLUEPRINTS:
        print(f"\n===== Validating {name} =====")
        bp = load_blueprint(name)
        test_structure(bp, name)
        test_inputs(bp)
        test_jinja(bp)
        test_action_shape(bp)
    print("\n===== Integration =====")
    test_installer()
    test_manifest()
    test_no_forbidden_mentions()
    print()
    if FAILURES:
        print(f"RESULT: FAILED ({len(FAILURES)} checks)")
        return 1
    print("RESULT: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
