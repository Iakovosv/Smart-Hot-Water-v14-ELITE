"""Branch-coverage check for the GSW Smart Hot Water blueprint.

Run with `python3 tests/test_branch_coverage.py`. Needs Home Assistant, so it
SKIPs cleanly when the package is absent (like the other HA-dependent checks).



Instead of asserting "the scenarios I thought of passed", this enumerates every
decision point (if / choose / repeat-until) directly from the substituted
blueprint config and then checks, against the REAL Home Assistant script trace,
which decisions were actually reached and with which outcome.

A decision is "covered" when the trace shows it was evaluated. It is
"two-sided" when both True and False were observed across the battery, which is
what proves the guard actually guards something.
"""
import asyncio
import datetime as dt
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from homeassistant import loader
    from homeassistant.components.automation import config as ac
    from homeassistant.components.blueprint import models
    from homeassistant.config_entries import ConfigEntries
    from homeassistant.core import Context, HomeAssistant
    from homeassistant.helpers import area_registry as ar
    from homeassistant.helpers import config_validation as cv
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er
    from homeassistant.helpers import trace as ha_trace
    from homeassistant.helpers.script import Script
    from homeassistant.setup import async_setup_component
    from homeassistant.util.yaml import loader as yloader
except ModuleNotFoundError:
    print("  SKIP - Home Assistant is not installed; "
          "branch-coverage check skipped.")
    sys.exit(0)

BP = str(ROOT / "custom_components" / "gsw_hotwater" / "blueprints"
         / "gsw_smart_hot_water.yaml")

INPUTS = {
    "boiler_switch": "switch.boiler",
    "water_temp_sensor": "sensor.water",
    "outdoor_temp_sensor": "sensor.out",
    "max_water_temp": 75,
    "status_entity": "input_select.status",
    "last_reason": "input_text.reason",
    "boiler_status_entity": "input_select.boiler",
    "boost_target_temp": "input_number.boost_target",
    "boost_minutes": "input_number.boost_minutes",
    "boost_button": "input_button.boost",
    "progress_entity": "input_number.progress",
    "last_on_entity": "input_datetime.last_on",
    "time_left_entity": "input_number.time_left",
    "time_left_pct_entity": "input_number.time_left_pct",
    "notify_target": "notify.mobile",
    "require_presence": False,
}

DEFAULT_STATES = {
    "switch.boiler": "off", "sensor.water": "30", "sensor.out": "15",
    "input_boolean.gsw_smart_hotwater_enable": "on",
    "input_boolean.water_temperature_check": "off",
    "input_select.status": "Idle", "input_select.boiler": "Αναμονή",
    "input_text.reason": "", "input_number.boost_target": "60",
    "input_number.boost_minutes": "60", "input_number.progress": "0",
    "input_number.time_left": "0", "input_number.time_left_pct": "0",
    "input_datetime.last_on": "2026-01-01 00:00:00",
    "binary_sensor.solar": "off",
    "sensor.solar_t": "10", "person.a": "home", "zone.home": "1",
}


# ---------------------------------------------------------------- config walk
def enumerate_decisions(cfg):
    """Return {path: kind} for every decision point in the config."""
    found = {}

    def walk(seq, prefix):
        for i, step in enumerate(seq or []):
            base = f"{prefix}/{i}" if prefix else str(i)
            if isinstance(step, dict):
                if "if" in step:
                    found[f"{base}/if"] = "if"
                    walk(step.get("then"), f"{base}/then")
                    walk(step.get("else"), f"{base}/else")
                if "choose" in step:
                    for k, choice in enumerate(step["choose"] or []):
                        found[f"{base}/choose/{k}/conditions"] = "conditions"
                        walk(choice.get("sequence"), f"{base}/choose/{k}/sequence")
                    if step.get("default") is not None:
                        walk(step["default"], f"{base}/default")
                if "repeat" in step:
                    found[f"{base}/repeat"] = "repeat"
                    rep = step["repeat"]
                    if isinstance(rep, dict):
                        walk(rep.get("sequence"), f"{base}/repeat/sequence")
                        if "until" in rep:
                            found[f"{base}/repeat/until"] = "until"
                if "sequence" in step:
                    walk(step["sequence"], f"{base}/sequence")
                if "parallel" in step:
                    walk(step["parallel"], f"{base}/parallel")
    walk(cfg.get("actions"), "")
    return found


# ---------------------------------------------------------------- HA plumbing
async def make_hass():
    hass = HomeAssistant("")
    await hass.async_start()
    cv._hass.hass = hass
    loader.async_setup(hass)
    await hass.async_block_till_done()
    hass.config_entries = ConfigEntries(hass, {})
    await er.async_load(hass)
    await dr.async_load(hass)
    await ar.async_load(hass)
    d = hass.config.path("blueprints", "automation", "gsw")
    os.makedirs(d, exist_ok=True)
    shutil.copy(BP, os.path.join(d, "gsw_smart_hot_water.yaml"))
    await async_setup_component(hass, "input_number", {"input_number": {
        "boost_target": {"min": 25, "max": 70}, "boost_minutes": {"min": 5, "max": 180},
        "progress": {"min": 0, "max": 100}, "time_left": {"min": 0, "max": 1000},
        "time_left_pct": {"min": 0, "max": 100}}})
    await async_setup_component(hass, "input_select", {"input_select": {
        "status": {"options": ["Idle", "Boost", "Target reached", "Blocked",
                               "Defrost", "Heating"]},
        "boiler": {"options": ["Αναμονή", "Θέρμανση", "Έτοιμο"]}}})
    await async_setup_component(hass, "input_text", {"input_text": {"reason": {"max": 255}}})
    await async_setup_component(hass, "input_datetime", {"input_datetime": {
        "last_on": {"has_date": True, "has_time": True}}})
    await asyncio.sleep(0.02)
    return hass


def register_services(hass):
    async def sw_on(c):
        e = c.data.get("entity_id")
        for x in ([e] if isinstance(e, str) else (e or [])):
            hass.states.async_set(x, "on")

    async def sw_off(c):
        e = c.data.get("entity_id")
        for x in ([e] if isinstance(e, str) else (e or [])):
            hass.states.async_set(x, "off")

    async def reason(c):
        hass.states.async_set("input_text.reason", str(c.data.get("value", "")))

    hass.services.async_register("switch", "turn_on", sw_on)
    hass.services.async_register("switch", "turn_off", sw_off)
    hass.services.async_register("input_text", "set_value", reason)
    for dom, svc in (("input_select", "select_option"), ("input_number", "set_value"),
                     ("input_datetime", "set_datetime"), ("notify", "mobile"),
                     ("notify", "persistent_notification")):
        hass.services.async_register(dom, svc, lambda c: None)


def _shorten(cfg):
    def walk(o):
        if isinstance(o, dict):
            d = o.get("delay")
            if isinstance(d, dt.timedelta):
                o["delay"] = dt.timedelta(seconds=0.1)
            elif isinstance(d, dict) and any(k in d for k in
                                             ("seconds", "minutes", "hours",
                                              "milliseconds", "days")):
                o["delay"] = dt.timedelta(seconds=0.1)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(cfg)


def build_cfg(hass, extra_inputs):
    extra_inputs = dict(extra_inputs or {})
    minimal = extra_inputs.pop("_minimal", False)
    full = hass.config.path("blueprints", "automation", "gsw",
                            "gsw_smart_hot_water.yaml")
    bp = models.Blueprint(yloader.load_yaml(full), path=full,
                          schema=ac.AUTOMATION_BLUEPRINT_SCHEMA)
    merged = {k: (s.get("default", "") if isinstance(s, dict) else "")
              for k, s in bp.inputs.items()}
    if not minimal:
        merged.update(INPUTS)
    else:
        merged.update({"boiler_switch": "switch.boiler",
                       "water_temp_sensor": "sensor.water"})
    merged.update(extra_inputs)
    cfg = models.BlueprintInputs(
        bp, {"use_blueprint": {"path": "gsw/gsw_smart_hot_water.yaml",
                               "input": merged}}).async_substitute()
    _shorten(cfg)
    return ac.PLATFORM_SCHEMA(cfg)


async def run_scenario(trigger, inputs=None, states=None, seq=None,
                       live=None):
    """Run one scenario; return the raw trace dict {path: [results]}."""
    hass = await make_hass()
    st = dict(DEFAULT_STATES)
    st.update(states or {})
    for e, s in st.items():
        hass.states.async_set(e, s)
    register_services(hass)
    cfg = build_cfg(hass, inputs)
    tok = ha_trace.trace_cv.set({})
    script = Script(hass, cfg["actions"], "probe", "automation",
                    variables=cfg["variables"])
    task = asyncio.create_task(script.async_run(
        run_variables={"trigger": {"id": trigger, "platform": "time"}},
        context=Context()))
    await asyncio.sleep(1.2)
    for v in (seq or []):
        hass.states.async_set("sensor.water", str(v))
        await asyncio.sleep(0.25)
    if seq:
        await asyncio.sleep(1.0)
    if live:
        live(hass)
        await asyncio.sleep(1.0)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):  # noqa: BLE001
        pass
    tr = ha_trace.trace_cv.get() or {}
    ha_trace.trace_cv.reset(tok)
    snapshot = {p: [(e._result or {}) for e in els] for p, els in tr.items()}
    await hass.async_stop()
    return snapshot


def merge_into(acc, snap):
    for p, results in snap.items():
        acc.setdefault(p, []).extend(results)


# ------------------------------------------------------------------ battery
def battery():
    S = []

    def add(trigger, inputs=None, states=None, seq=None, live=None):
        S.append(dict(trigger=trigger, inputs=inputs or {},
                      states=states or {}, seq=seq, live=live))

    base_sched = {"require_presence": False, "schedule_1_enabled": True}

    # ---- boost paths
    add("boost", states={"input_number.boost_target": "60"}, seq=[40, 55, 62])
    add("boost", states={"input_number.boost_target": "60",
                         "input_boolean.gsw_smart_hotwater_enable": "off"})
    add("boost", states={"switch.boiler": "on"})
    add("boost", states={"sensor.water": "unknown"})
    add("boost", states={"input_boolean.water_temperature_check": "on"})
    add("boost", states={"sensor.water": "80"})
    add("boost", states={"sensor.water": "60", "input_number.boost_target": "40"})
    add("boost", states={"sensor.water": "45", "input_number.boost_target": "60"},
        live=lambda h: h.states.async_set("input_number.boost_target", "25"))
    add("boost", states={"sensor.water": "36"},
        live=lambda h: h.states.async_set("input_number.boost_minutes", "0.02"))
    add("boost", states={"sensor.water": "36"},
        live=lambda h: h.states.async_set("input_boolean.gsw_smart_hotwater_enable", "off"))
    add("boost", states={"sensor.water": "45"},
        live=lambda h: h.states.async_set("input_number.boost_target", "65"))
    # ---- schedules 1..6, each in isolation, heat then reach target
    for idx in range(1, 7):
        ins = {"require_presence": False}
        for k in range(1, 7):
            ins[f"schedule_{k}_enabled"] = (k == idx)
        add(f"sched_{idx}", inputs=ins, states={"sensor.water": "30"}, seq=[40, 60])
    add("sched_2", inputs={"require_presence": False, "schedule_1_enabled": True},
        states={"sensor.water": "30"}, seq=[40, 60])
    add("sched_1", inputs=base_sched,
        states={"input_boolean.gsw_smart_hotwater_enable": "off"})
    add("sched_1", inputs=base_sched, states={"sensor.water": "unavailable"})
    add("sched_1", inputs=base_sched, states={"input_boolean.water_temperature_check": "on"})
    add("sched_1", inputs=base_sched, states={"sensor.water": "80"})
    add("sched_1", inputs=base_sched, states={"sensor.water": "70"})
    add("sched_1", inputs=base_sched, states={"sensor.water": "30", "switch.boiler": "on"})
    # ---- solar modes
    solar_flag = {**base_sched, "solar_mode": "flag", "solar_flag": "binary_sensor.solar"}
    add("sched_1", inputs=solar_flag, states={"binary_sensor.solar": "on"})
    add("sched_1", inputs=solar_flag, states={"binary_sensor.solar": "off"})
    solar_temp = {**base_sched, "solar_mode": "temperature",
                  "solar_temp_sensor": "sensor.solar_t", "solar_temp_threshold": 25}
    add("sched_1", inputs=solar_temp, states={"sensor.solar_t": "40"})
    add("sched_1", inputs=solar_temp, states={"sensor.solar_t": "10"})
    solar_both = {**base_sched, "solar_mode": "both",
                  "solar_flag": "binary_sensor.solar",
                  "solar_temp_sensor": "sensor.solar_t", "solar_temp_threshold": 25}
    add("sched_1", inputs=solar_both,
        states={"binary_sensor.solar": "on", "sensor.solar_t": "5"})
    add("sched_1", inputs=solar_both,
        states={"binary_sensor.solar": "off", "sensor.solar_t": "40"})
    # ---- cold / warm auto target + explicit override
    add("sched_1", inputs=base_sched,
        states={"sensor.out": "10", "sensor.water": "55"}, seq=[56])
    add("sched_1", inputs=base_sched, states={"sensor.out": "20", "sensor.water": "55"})
    add("sched_1", inputs={**base_sched, "schedule_1_temp": 65},
        states={"sensor.out": "20", "sensor.water": "55"}, seq=[60])
    # ---- presence
    pres = {**base_sched, "require_presence": True, "user_1": "person.a",
            "user_1_zones": ["zone.home"]}
    add("sched_1", inputs=pres, states={"person.a": "not_home"})
    add("sched_1", inputs=pres, states={"person.a": "home"}, seq=[60])
    add("sched_1", inputs={**base_sched, "require_presence": True},
        states={"sensor.water": "30"}, seq=[60])
    pres2 = {**pres, "user_2": "person.b", "user_2_zones": ["zone.home"]}
    add("sched_1", inputs=pres2,
        states={"person.a": "not_home", "person.b": "not_home"})
    # ---- defrost
    dfr = {"require_presence": False, "defrost_enable": True,
           "defrost_start_time": "00:00:00", "defrost_end_time": "23:59:59",
           "defrost_water_temp": 40, "defrost_outdoor_temp": 20}
    add("defrost_t", inputs=dfr, states={"sensor.water": "30", "sensor.out": "2"})
    add("defrost_t", inputs={**dfr, "defrost_start_time": "03:00:00",
                             "defrost_end_time": "03:05:00"},
        states={"sensor.water": "30", "sensor.out": "2"})
    add("defrost_t", inputs={"require_presence": False, "defrost_enable": False},
        states={"sensor.water": "30", "sensor.out": "2"})
    add("defrost_t", inputs={**dfr, "defrost_water_temp": 4},
        states={"sensor.water": "30", "sensor.out": "2"})
    add("defrost_t", inputs=dfr,
        states={"sensor.water": "30", "sensor.out": "2",
                "input_boolean.gsw_smart_hotwater_enable": "off"})
    add("defrost_t", inputs=dfr,
        states={"sensor.water": "30", "sensor.out": "2", "switch.boiler": "on"})
    # ---- minimal configuration: optional helpers left empty must not crash,
    #      which flips every "helper is set" guard to its other branch.
    add("boost", inputs={"_minimal": True}, states={"sensor.water": "30"}, seq=[70])
    add("boost", inputs={"_minimal": True},
        states={"input_boolean.gsw_smart_hotwater_enable": "off"})
    add("boost", inputs={"_minimal": True}, states={"switch.boiler": "on"})
    add("sched_1", inputs={"_minimal": True, "schedule_1_enabled": True},
        states={"sensor.water": "30"}, seq=[70])
    add("sched_1", inputs={"_minimal": True, "schedule_1_enabled": True},
        states={"sensor.water": "30", "input_boolean.gsw_smart_hotwater_enable": "off"})
    add("sched_1", inputs={"_minimal": True, "schedule_1_enabled": True},
        states={"sensor.water": "30", "switch.boiler": "on"})
    add("boost", inputs={"_minimal": True}, states={"sensor.water": "30"}, seq=[80])
    add("boost", inputs={"_minimal": True},
        states={"sensor.water": "30", "input_number.boost_target": "40"}, seq=[45])
    add("sched_1", inputs={"_minimal": True, "schedule_1_enabled": True},
        states={"sensor.water": "30"}, seq=[80])
    add("sched_1", inputs={"_minimal": True, "schedule_1_enabled": True},
        states={"sensor.water": "30", "input_number.boost_target": "40"}, seq=[45])
    add("defrost_t", inputs={"_minimal": True, "defrost_enable": True,
                             "defrost_start_time": "00:00:00",
                             "defrost_end_time": "23:59:59",
                             "defrost_water_temp": 40,
                             "defrost_outdoor_temp": 20},
        states={"sensor.water": "30", "sensor.out": "2"})
    # ---- every scenario again with the optional helpers switched OFF, so the
    #      "helper is configured" guards take their other branch too.
    for case in list(S):
        S.append({**case, "inputs": {**case["inputs"], "_minimal": True}})
    # ---- explicit "these two helpers left empty" (they have defaults, so a
    #      plain minimal config would still keep them set).
    empty = {"progress_entity": "", "last_on_entity": ""}
    add("boost", inputs=empty, states={"sensor.water": "30"}, seq=[80])
    add("boost", inputs=empty, states={"sensor.water": "80"})
    add("sched_1", inputs={**empty, "schedule_1_enabled": True},
        states={"sensor.water": "30"}, seq=[80])
    add("sched_1", inputs={**empty, "schedule_1_enabled": True},
        states={"sensor.water": "30", "input_boolean.gsw_smart_hotwater_enable": "off"})
    add("sched_1", inputs={**empty, "schedule_1_enabled": True},
        states={"sensor.water": "80"})
    # ---- status / last_reason helpers left empty
    empty2 = {"status_entity": "", "last_reason": ""}
    add("boost", inputs=empty2, states={"sensor.water": "30"}, seq=[80])
    add("boost", inputs=empty2, states={"sensor.water": "80"})
    # already above target, with the status helper left empty
    add("boost", inputs=empty2,
        states={"sensor.water": "60", "input_number.boost_target": "40"})
    # a manual run: no recognised trigger id at all
    add("manual", states={"sensor.water": "30"})
    add("boost", inputs=empty2,
        states={"sensor.water": "30", "input_boolean.gsw_smart_hotwater_enable": "off"})
    add("sched_1", inputs={**empty2, "schedule_1_enabled": True},
        states={"sensor.water": "30"}, seq=[80])
    add("sched_1", inputs={**empty2, "schedule_1_enabled": True},
        states={"sensor.water": "30", "input_boolean.gsw_smart_hotwater_enable": "off"})
    add("sched_1", inputs={**empty2, "schedule_1_enabled": True},
        states={"sensor.water": "80"})
    add("defrost_t", inputs={**empty2, "defrost_enable": True,
                             "defrost_start_time": "00:00:00",
                             "defrost_end_time": "23:59:59",
                             "defrost_water_temp": 40,
                             "defrost_outdoor_temp": 20},
        states={"sensor.water": "30", "sensor.out": "2"})
    return S


async def main():
    hass0 = await make_hass()
    cfg = build_cfg(hass0, {})
    decisions = enumerate_decisions(cfg)
    await hass0.async_stop()

    trace_acc = {}
    for case in battery():
        snap = await run_scenario(**case)
        merge_into(trace_acc, snap)

    # ---- evaluate coverage ----
    covered, twosided, missing = [], [], []
    onesided = []
    for path, kind in sorted(decisions.items()):
        # `conditions` / `repeat` / `until` are only visible as a prefix in the
        # trace (the concrete entry carries an index suffix), so match loosely.
        if kind in ("conditions", "repeat", "until"):
            hits = [r for p, res in trace_acc.items()
                    if p == path or p.startswith(path + "/") for r in res]
        else:
            hits = trace_acc.get(path, [])
        if not hits:
            missing.append((path, kind))
            continue
        covered.append(path)
        results = {bool(h.get("result")) for h in hits if "result" in h}
        choices = {h.get("choice") for h in hits if "choice" in h}
        if len(results) >= 2 or len(choices) >= 2:
            twosided.append(path)
        else:
            onesided.append((path, kind, sorted(str(x) for x in (results or choices))))

    # Provably unreachable: the schedule branch reaches `is_state(master,'on')`
    # only after the master-off `choose` above it already matched, so its False
    # side can never run. Redundant but harmless.
    unreachable = {"0/choose/1/sequence/0/choose/1/conditions"}
    onesided = [o for o in onesided if o[0] not in unreachable]

    print("=" * 78)
    print(f"  decision points in blueprint : {len(decisions)}")
    print(f"  reached by the battery       : {len(covered)}")
    print(f"  two-sided (both outcomes)    : {len(twosided)}")
    print(f"  one-sided only               : {len(onesided)}")
    print(f"  NEVER reached                : {len(missing)}")
    print("=" * 78)
    if onesided:
        print("\nONE-SIDED (guard never took the other branch):")
        for p, k, v in onesided:
            print(f"   {p}   [{k}] observed={v}")
    if missing:
        print("\nNEVER REACHED:")
        for p, k in missing:
            print(f"   {p}   [{k}]")
        print("\nCOVERAGE: INCOMPLETE")
        return 1
    if onesided:
        print("\nCOVERAGE: INCOMPLETE - one-sided decisions remain.")
        return 1
    print("\nCOVERAGE: every decision point was executed, and all but one "
          "redundant guard took both branches.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
