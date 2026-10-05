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
        check({"sched_1", "sched_2", "sched_3", "sched_4", "sched_5", "sched_6",
               "defrost_t", "boost"} <= ids,
              "main blueprint has exact-time triggers for 6 schedules + defrost + boost")
        platforms = {t.get("platform") for t in triggers if isinstance(t, dict)}
        check("time_pattern" not in platforms,
              "no polling trigger - schedules fire at exact times only")
        for t in triggers:
            if isinstance(t, dict) and t.get("platform") == "time":
                check("at" in t, f"time trigger '{t.get('id')}' has an 'at' time")
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

    # Schedules: 6 independent slots, each with its own exact trigger time
    if "schedule_1_enabled" in inputs:
        for i in range(1, 7):
            for suffix in ("enabled", "time", "temp"):
                check(f"schedule_{i}_{suffix}" in inputs,
                      f"schedule_{i}_{suffix} input exists")
        check("notify_target" in inputs, "optional notify_target input exists")
        check("last_reason" in inputs, "optional last_reason input exists")
        check("boiler_status_entity" in inputs, "optional boiler_status_entity input exists")
        check("time_left_entity" in inputs, "optional time_left_entity input exists")
        check("time_left_pct_entity" in inputs, "optional time_left_pct_entity input exists")


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


SAMPLE_INPUTS = {
    "boiler_switch": "switch.boiler",
    "water_temp_sensor": "sensor.water",
    "max_water_temp": 75,
    "status_entity": "input_select.status",
    "progress_entity": "input_number.progress",
    "last_reason": "input_text.reason",
    "last_on_entity": "input_datetime.last_on",
    "time_left_entity": "input_number.left",
    "time_left_pct_entity": "input_number.left_pct",
    "boiler_status_entity": "input_select.boiler",
    "notify_target": "notify.mobile",
    "outdoor_temp_sensor": "sensor.out",
    "solar_flag": "binary_sensor.solar",
    "solar_temp_sensor": "sensor.solar_t",
    "user_1": "person.a",
    "user_1_zones": ["zone.home"],
    "user_2": "person.b",
    "user_2_zones": ["zone.work"],
}


def test_ha_blueprint_save() -> None:
    """Run HA's own save-time validation, if Home Assistant is installed.

    This is the strongest check: it exercises the exact substitution +
    voluptuous schema HA uses when the blueprint is saved from the UI, for
    every optional field left empty, filled, and mixed. Skipped (ok) when HA
    is not available, so the suite still runs standalone.
    """
    print("test_ha_blueprint_save (real HA substitution + schema)")
    try:
        import asyncio  # noqa: PLC0415

        from homeassistant.components.automation import config as ac  # noqa: PLC0415
        from homeassistant.components.blueprint import models  # noqa: PLC0415
        from homeassistant.core import HomeAssistant  # noqa: PLC0415
        from homeassistant.helpers import config_validation as cv  # noqa: PLC0415
        from homeassistant.util.yaml import loader as yloader  # noqa: PLC0415
        import voluptuous as vol  # noqa: PLC0415
    except ImportError:
        print("  ok   - Home Assistant not installed, skipped")
        return

    async def run() -> list[str]:
        cv._hass.hass = HomeAssistant("")
        problems: list[str] = []
        for name in BLUEPRINTS:
            path = str(BLUEPRINT_DIR / name)
            bp = models.Blueprint(yloader.load_yaml(path), path=path,
                                  schema=ac.AUTOMATION_BLUEPRINT_SCHEMA)
            for mode in ("empty", "filled", "mixed"):
                inputs = {}
                for key, spec in bp.inputs.items():
                    default = spec.get("default", "") if isinstance(spec, dict) else ""
                    if mode == "empty":
                        inputs[key] = default
                    elif mode == "filled":
                        inputs[key] = SAMPLE_INPUTS.get(key, default)
                    else:
                        inputs[key] = (SAMPLE_INPUTS.get(key, default)
                                       if len(key) % 2 else default)
                bi = models.BlueprintInputs(
                    bp, {"use_blueprint": {"path": path, "input": inputs}})
                try:
                    ac.PLATFORM_SCHEMA(bi.async_substitute())
                except vol.Invalid as exc:
                    problems.append(f"{name} [{mode}]: {exc}")
        return problems

    problems = asyncio.run(run())
    check(not problems, f"HA save validation passes for all scenarios "
                        f"({len(BLUEPRINTS)} blueprints x 3 input modes)")
    for p in problems:
        print(f"        {p}")


BUILTIN_CARDS = {
    "markdown", "gauge", "tile", "entities", "history-graph",
    "statistics-graph", "button", "horizontal-stack", "vertical-stack",
    "grid", "heading", "section", "if", "custom", "conditional",
    # view types (not cards, but appear as "type" in the YAML)
    "sections", "masonry", "panel", "sidebar",
}


def test_dashboard_files() -> None:
    """The shipped dashboard/card YAML must parse and use only built-in cards."""
    print("test_dashboard_files")
    dash_dir = ROOT / "dashboard"
    files = sorted(dash_dir.rglob("*.yaml"))
    check(bool(files), "dashboard/ has YAML files")
    env = Environment()
    for path in files:
        rel = path.relative_to(ROOT)
        raw = path.read_text(encoding="utf-8")
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            check(False, f"{rel} parses ({exc})")
            continue
        check(isinstance(data, dict), f"{rel} parses to a mapping")

        types: set[str] = set()

        def walk(obj):
            if isinstance(obj, dict):
                t = obj.get("type")
                if isinstance(t, str):
                    types.add(t)
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)

        walk(data)
        # 'numeric-input' etc. are tile FEATURES, not card types - ignore them.
        card_types = types - {"numeric-input", "toggle", "slider",
                              "buttons", "select-options", "trend-graph"}
        unknown = {t for t in card_types if t not in BUILTIN_CARDS}
        check(not unknown, f"{rel}: only built-in cards (unknown: {sorted(unknown)})")

        bad = []
        for node in walk_strings(data):
            if "{{" in node or "{%" in node:
                try:
                    env.parse(node)
                except Exception as exc:  # noqa: BLE001
                    bad.append((node[:50], str(exc)))
        check(not bad, f"{rel}: all Jinja templates parse")
        for snippet, err in bad:
            print(f"        bad: {snippet!r} -> {err}")


def walk_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_strings(v)


class _Now:
    def __init__(self, ts):
        self._ts = ts

    def timestamp(self):
        return self._ts

    def strftime(self, fmt):
        import datetime

        return datetime.datetime.fromtimestamp(self._ts).strftime(fmt)


def test_countdown_render() -> None:
    """Render the countdown cards' templates and check the mm:ss math.

    The reverse timer is driven by the blueprint's input_number (already
    counting down), so the card shows that value as mm:ss. With 30 min
    remaining it must show 30:00, and it must never call as_timestamp on the
    (possibly time-only) input_datetime - the reported crash.
    """
    print("test_countdown_render")
    cards = sorted((ROOT / "dashboard" / "cards").glob("1[123]-*.yaml"))
    check(len(cards) == 3, "three conditional countdown cards exist")
    env = Environment()
    now_ts = 1_700_000_000.0
    sample = {
        "input_select.gsw_hotwater_status": "Heating",
        "input_number.gsw_time_left_minutes": "30",
        "input_number.gsw_time_left_pct": "50",
        "sensor.temperature_esp_temperature_esp": "48",
        "sensor.temperature_esp_outside_temperature": "52",
        "sensor.gw2000a_outdoor_temperature": "14",
    }
    for path in cards:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        content = data["card"]["content"]
        # The template must NOT call as_timestamp on the (possibly time-only)
        # input_datetime - that was the reported crash.
        check("as_timestamp(" not in content,
              f"{path.name} avoids as_timestamp (crash fix)")
        env.globals["states"] = lambda e: sample.get(e, "unknown")
        env.globals["now"] = lambda: _Now(now_ts)
        try:
            out = env.from_string(content).render()
        except Exception as exc:  # noqa: BLE001
            check(False, f"{path.name} renders ({exc})")
            continue
        # 30 min left = 30:00 (the input_number already counts down)
        check("30:00" in out,
              f"{path.name} shows 30:00 with 30 min remaining")

        # Conditional conditions must be OR (a single state condition with a
        # list of states), otherwise the card would never show.
        cond = data["conditions"][0]
        states = cond.get("state")
        if cond.get("condition") == "or":
            states = [c.get("state") for c in cond.get("conditions", [])]
        check(isinstance(states, list) and len(states) >= 2,
              f"{path.name} shows for Heating/Boost/Defrost (OR)")


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
    test_ha_blueprint_save()
    test_dashboard_files()
    test_countdown_render()
    print()
    if FAILURES:
        print(f"RESULT: FAILED ({len(FAILURES)} checks)")
        return 1
    print("RESULT: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
