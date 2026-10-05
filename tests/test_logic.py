"""Functional tests for the GSW Smart Hot Water blueprint logic.

Evaluates the exact Jinja expressions used in the blueprint against a tiny
Home Assistant state simulator, so we test real behaviour without a full HA.

Run: python3 tests/test_logic.py
"""
from __future__ import annotations

import sys
from datetime import datetime, time as dtime
from pathlib import Path

import yaml
from jinja2 import Environment

ROOT = Path(__file__).resolve().parent.parent
BLUEPRINT = ROOT / "custom_components" / "gsw_hotwater" / "blueprints" / "gsw_smart_hot_water.yaml"

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


yaml.SafeLoader.add_constructor("!input", lambda l, n: _InputTag(l.construct_scalar(n)))


def _make_env(states_map: dict, attrs_map: dict, now_dt: datetime) -> Environment:
    env = Environment()

    def states(entity_id):
        return states_map.get(entity_id, "unknown")

    def is_state(entity_id, state):
        return states_map.get(entity_id) == state

    def state_attr(entity_id, attr):
        return attrs_map.get(entity_id, {}).get(attr)

    def now():
        return now_dt

    def today_at(value):
        if isinstance(value, str):
            h, m, s = (value.split(":") + ["0", "0"])[:3]
            return now_dt.replace(hour=int(h), minute=int(m), second=int(s), microsecond=0)
        return value

    env.globals.update(states=states, is_state=is_state, state_attr=state_attr,
                       now=now, today_at=today_at)
    return env


# The exact expressions from the blueprint -------------------------------- #

PRESENCE = """{% if not require_presence_val %}
  {{ true }}
{% else %}
  {% set ns = namespace(here=false) %}
  {% if user_1_zones_list | length > 0 %}
    {% for z in user_1_zones_list %}
      {% if states(user_1_entity) in ['home', state_attr(z, 'friendly_name'), z.split('.')[-1]] %}
        {% set ns.here = true %}
      {% endif %}
    {% endfor %}
  {% endif %}
  {% if user_2_entity not in ['', none] and user_2_zones_list | length > 0 %}
    {% for z in user_2_zones_list %}
      {% if states(user_2_entity) in ['home', state_attr(z, 'friendly_name'), z.split('.')[-1]] %}
        {% set ns.here = true %}
      {% endif %}
    {% endfor %}
  {% endif %}
  {{ ns.here }}
{% endif %}"""

SOLAR = """{% if solar_mode_val == 'off' %}
  {{ false }}
{% elif solar_mode_val == 'flag' %}
  {{ is_state(solar_flag_entity, 'on') if solar_flag_entity not in ['', none] else false }}
{% elif solar_mode_val == 'temperature' %}
  {{ (states(solar_temp_sensor_entity) | float(-999)) > solar_temp_threshold_val if solar_temp_sensor_entity not in ['', none] else false }}
{% elif solar_mode_val == 'both' %}
  {% set f = is_state(solar_flag_entity, 'on') if solar_flag_entity not in ['', none] else false %}
  {% set t = (states(solar_temp_sensor_entity) | float(-999)) > solar_temp_threshold_val if solar_temp_sensor_entity not in ['', none] else false %}
  {{ f or t }}
{% else %}
  {{ false }}
{% endif %}"""

TRIGGER_MATCH = "{{ trigger_id == ('sched_' ~ idx) }}"

TARGET = """{% if sched_temp | float(0) > 0 %}
  {{ sched_temp }}
{% else %}
  {{ cold_temp if now_out < cold_threshold_val else warm_temp }}
{% endif %}"""

DEFROST = """{% if not defrost_enabled or trigger_id != 'defrost_t' %}
  {{ false }}
{% else %}
  {% set now_t = now().time() %}
  {% set start = today_at(defrost_start).time() %}
  {% set end = today_at(defrost_end).time() %}
  {% set o = o if outdoor_temp_sensor_entity not in ['', none] else -999 %}
  {% set in_window = (start <= now_t <= end) if start <= end else (now_t >= start or now_t <= end) %}
  {{ in_window
     and w <= defrost_water
     and (outdoor_temp_sensor_entity in ['', none] or o <= defrost_outdoor)
     and not is_state(water_temp_check_entity, 'on')
     and not (max_water_temp_val | float(0) > 0 and w >= (max_water_temp_val | float(0)))
     and water_temp_state not in ['unknown','unavailable','none','']
     and not boiler_on }}
{% endif %}"""

MAX_TEMP = "{{ max_water > 0 and water_now >= max_water }}"

PROGRESS = "{{ ([[ (hb_current / hb_target * 100) | round(0), 100 ] | min, 0] | max if hb_target > 0 else 0) | int }}"

HEAT_BELOW = "{{ water_now < (heat_below | float(0)) }}"

REASON_TEXT = "sched {{ idx }}: {{ reason }}"

# Reverse countdown: minutes left = max - elapsed, clamped to [0, max].
TIME_LEFT_MIN = "{{ [ [ (max_time - elapsed), 0 ] | max, max_time ] | min | round(1) }}"

# Reverse countdown percent = remaining / max * 100, clamped to [0, 100].
TIME_LEFT_PCT = "{{ ([[ (((max_time) - (elapsed)) / ([max_time, 1] | max) * 100) | round(0), 100 ] | min, 0] | max) | int }}"

# Full gate chain, in the same order as the blueprint's schedule decision.
DECIDE = """{% if not master_on %}master_off
{% elif not presence_ok %}no_presence
{% elif water_state in ['unknown','unavailable','none',''] %}sensor_bad
{% elif check_on %}blocked_check
{% elif max_temp %}max_temp
{% elif solar_skip %}solar_skip
{% elif water_val >= heat_below %}temp_ok
{% elif boiler_on %}already_on
{% else %}heat{% endif %}"""


def render(env: Environment, template: str, **ctx):
    return env.from_string(template).render(**ctx).strip()


def test_presence() -> None:
    print("test_presence (home zone + custom zones + optional user 2)")
    zones = ["zone.douleia", "zone.naxos", "zone.home"]
    attrs = {"zone.home": {"friendly_name": "Jack home"},
             "zone.douleia": {"friendly_name": "Δουλεία Ιάκωβος"},
             "zone.naxos": {"friendly_name": "Νάξος"}}

    # 1. At home -> person state is literal 'home' (the bug we fixed)
    env = _make_env({"person.iakovos": "home", "person.thalia": "not_home"}, attrs,
                    datetime(2026, 1, 1, 6, 0))
    r = render(env, PRESENCE, user_1_entity="person.iakovos", user_1_zones_list=zones,
               user_2_entity="person.thalia", user_2_zones_list=[], require_presence_val=True)
    check(r == "True", "home zone detected via literal 'home'")

    # 2. In a custom zone -> friendly name match
    env = _make_env({"person.iakovos": "Δουλεία Ιάκωβος"}, attrs, datetime(2026, 1, 1, 6, 0))
    r = render(env, PRESENCE, user_1_entity="person.iakovos", user_1_zones_list=zones,
               user_2_entity="", user_2_zones_list=[], require_presence_val=True)
    check(r == "True", "custom zone detected via friendly name")

    # 3. Custom zone via slug (some setups expose the slug)
    env = _make_env({"person.iakovos": "naxos"}, attrs, datetime(2026, 1, 1, 6, 0))
    r = render(env, PRESENCE, user_1_entity="person.iakovos", user_1_zones_list=zones,
               user_2_entity="", user_2_zones_list=[], require_presence_val=True)
    check(r == "True", "custom zone detected via slug")

    # 4. Nobody present
    env = _make_env({"person.iakovos": "not_home", "person.thalia": "not_home"}, attrs,
                    datetime(2026, 1, 1, 6, 0))
    r = render(env, PRESENCE, user_1_entity="person.iakovos", user_1_zones_list=zones,
               user_2_entity="person.thalia", user_2_zones_list=zones, require_presence_val=True)
    check(r == "False", "nobody present -> false")

    # 5. User 2 present in their own zone
    env = _make_env({"person.iakovos": "not_home", "person.thalia": "Νάξος"}, attrs,
                    datetime(2026, 1, 1, 6, 0))
    r = render(env, PRESENCE, user_1_entity="person.iakovos", user_1_zones_list=zones,
               user_2_entity="person.thalia", user_2_zones_list=["zone.naxos"],
               require_presence_val=True)
    check(r == "True", "optional user 2 present -> true")

    # 6. Presence disabled
    env = _make_env({"person.iakovos": "not_home"}, attrs, datetime(2026, 1, 1, 6, 0))
    r = render(env, PRESENCE, user_1_entity="person.iakovos", user_1_zones_list=zones,
               user_2_entity="", user_2_zones_list=[], require_presence_val=False)
    check(r == "True", "require_presence off -> always true")
    # empty zones list -> nobody can match -> false (heating stays off)
    r = render(env, PRESENCE, user_1_entity="person.iakovos", user_1_zones_list=[],
               user_2_entity="", user_2_zones_list=[], require_presence_val=True)
    check(r == "False", "empty zones + presence on -> false (safe)")


def test_solar() -> None:
    print("test_solar (off / flag / temperature / both)")
    attrs = {}
    base = dict(solar_flag_entity="input_boolean.solar_ok",
                solar_temp_sensor_entity="sensor.temperature_esp_outside_temperature",
                solar_temp_threshold_val=45)

    cases = [
        ("off", {}, False),
        ("flag", {"input_boolean.solar_ok": "on"}, True),
        ("flag", {"input_boolean.solar_ok": "off"}, False),
        ("temperature", {"sensor.temperature_esp_outside_temperature": "50"}, True),
        ("temperature", {"sensor.temperature_esp_outside_temperature": "30"}, False),
        ("both", {"sensor.temperature_esp_outside_temperature": "50"}, True),
        ("both", {"input_boolean.solar_ok": "on"}, True),
        ("both", {"sensor.temperature_esp_outside_temperature": "10", "input_boolean.solar_ok": "off"}, False),
        # strict "above": exactly at threshold does NOT skip
        ("temperature", {"sensor.temperature_esp_outside_temperature": "45"}, False),
        ("temperature", {"sensor.temperature_esp_outside_temperature": "46"}, True),
    ]
    for mode, states_map, expected in cases:
        env = _make_env(states_map, attrs, datetime(2026, 1, 1, 6, 0))
        r = render(env, SOLAR, solar_mode_val=mode, **base)
        check(r == str(expected), f"solar mode={mode} states={states_map} -> {expected}")

    # Empty optional entities -> never skip (heating still works)
    empty = dict(solar_flag_entity="", solar_temp_sensor_entity="",
                 solar_temp_threshold_val=45)
    for mode in ("flag", "temperature", "both"):
        env = _make_env({}, attrs, datetime(2026, 1, 1, 6, 0))
        r = render(env, SOLAR, solar_mode_val=mode, **empty)
        check(r == "False", f"solar mode={mode} with empty entities -> no skip")


def test_panel_vs_water() -> None:
    print("test_panel_vs_water (panel above threshold suppresses heating)")
    attrs = {}
    base = dict(solar_flag_entity="input_boolean.solar_ok",
                solar_temp_sensor_entity="sensor.panel",
                solar_temp_threshold_val=45)

    # water 40 (< heat_below 45) but panel 50 (> 45) -> skip heating
    e = _make_env({"sensor.panel": "50"}, attrs, datetime(2026, 1, 1, 6, 0))
    check(render(e, SOLAR, solar_mode_val="temperature", **base) == "True",
          "water below threshold but panel above -> skip")
    # panel not above threshold -> heat
    e = _make_env({"sensor.panel": "40"}, attrs, datetime(2026, 1, 1, 6, 0))
    check(render(e, SOLAR, solar_mode_val="temperature", **base) == "False",
          "panel not above threshold -> heat")
    # panel sensor missing/unavailable -> never skip
    e = _make_env({"sensor.panel": "unavailable"}, attrs, datetime(2026, 1, 1, 6, 0))
    check(render(e, SOLAR, solar_mode_val="temperature", **base) == "False",
          "panel unavailable -> heat")


def test_trigger_match() -> None:
    print("test_trigger_match (exact-time trigger selects the right schedule)")
    env = _make_env({}, {}, datetime(2026, 1, 1, 16, 3))
    check(render(env, TRIGGER_MATCH, trigger_id="sched_1", idx=1) == "True",
          "sched_1 trigger matches schedule 1")
    check(render(env, TRIGGER_MATCH, trigger_id="sched_1", idx=2) == "False",
          "sched_1 trigger does not match schedule 2")
    check(render(env, TRIGGER_MATCH, trigger_id="defrost_t", idx=1) == "False",
          "defrost trigger does not match a schedule")
    check(render(env, TRIGGER_MATCH, trigger_id="sched_6", idx=6) == "True",
          "sched_6 trigger matches schedule 6")


def test_target() -> None:
    print("test_target (cold/warm + explicit override)")
    env = _make_env({}, {}, datetime(2026, 1, 1, 6, 0))
    check(render(env, TARGET, sched_temp=0, now_out=10, cold_temp=58, warm_temp=50,
                 cold_threshold_val=16) == "58", "cold outdoor -> cold target")
    check(render(env, TARGET, sched_temp=0, now_out=20, cold_temp=58, warm_temp=50,
                 cold_threshold_val=16) == "50", "warm outdoor -> warm target")
    check(render(env, TARGET, sched_temp=62, now_out=10, cold_temp=58, warm_temp=50,
                 cold_threshold_val=16) == "62", "explicit schedule temp overrides")


def test_defrost() -> None:
    print("test_defrost (exact trigger, window, empty outdoor sensor)")
    base = dict(defrost_enabled=True, trigger_id="defrost_t",
                defrost_start="03:00:00", defrost_end="05:00:00", defrost_water=4,
                defrost_outdoor=2, w=3, o=1, max_water_temp_val=75,
                outdoor_temp_sensor_entity="sensor.outdoor",
                water_temp_check_entity="", water_temp_state="3.0", boiler_on=False)
    env = _make_env({}, {}, datetime(2026, 1, 1, 4, 0))
    check(render(env, DEFROST, **base) == "True", "inside window + cold -> true")
    env = _make_env({}, {}, datetime(2026, 1, 1, 6, 0))
    check(render(env, DEFROST, **base) == "False", "outside window -> false")
    # wrong trigger -> defrost must not run
    env = _make_env({}, {}, datetime(2026, 1, 1, 4, 0))
    check(render(env, DEFROST, **dict(base, trigger_id="sched_1")) == "False",
          "non-defrost trigger -> false")
    check(render(env, DEFROST, **dict(base, defrost_enabled=False)) == "False",
          "defrost disabled -> false")
    # past-midnight window 23:00 -> 02:00
    pm = dict(base, defrost_start="23:00:00", defrost_end="02:00:00")
    env = _make_env({}, {}, datetime(2026, 1, 1, 0, 30))
    check(render(env, DEFROST, **pm) == "True", "past-midnight window 00:30 -> true")
    env = _make_env({}, {}, datetime(2026, 1, 1, 12, 0))
    check(render(env, DEFROST, **pm) == "False", "past-midnight window 12:00 -> false")
    # no outdoor sensor -> outdoor gate ignored, defrost still works
    no_out = dict(base, outdoor_temp_sensor_entity="")
    env = _make_env({}, {}, datetime(2026, 1, 1, 4, 0))
    check(render(env, DEFROST, **no_out) == "True",
          "empty outdoor sensor -> gate ignored -> true")
    # water sensor unknown -> no defrost (never heat blind)
    bad = dict(base, water_temp_state="unknown")
    env = _make_env({}, {}, datetime(2026, 1, 1, 4, 0))
    check(render(env, DEFROST, **bad) == "False", "unknown water sensor -> false")


def test_progress() -> None:
    print("test_progress (clamped 0-100)")
    env = _make_env({}, {}, datetime(2026, 1, 1, 6, 0))
    check(render(env, PROGRESS, hb_current=30, hb_target=60) == "50", "30/60 -> 50%")
    check(render(env, PROGRESS, hb_current=80, hb_target=60) == "100", "over target -> 100%")
    check(render(env, PROGRESS, hb_current=0, hb_target=0) == "0", "zero target -> 0%")


def test_heat_below() -> None:
    print("test_heat_below (heat only when water is below the threshold)")
    env = _make_env({}, {}, datetime(2026, 1, 1, 6, 0))
    # heat_below 45: below 45 -> heat, at/above 45 -> no heat
    check(render(env, HEAT_BELOW, water_now=44.9, heat_below=45) == "True",
          "44.9 below 45 -> heat")
    check(render(env, HEAT_BELOW, water_now=45, heat_below=45) == "False",
          "exactly 45 -> no heat")
    check(render(env, HEAT_BELOW, water_now=45.1, heat_below=45) == "False",
          "45.1 above 45 -> no heat")
    check(render(env, HEAT_BELOW, water_now=40, heat_below=45) == "True",
          "40 below 45 -> heat")


def test_boost_and_defrost_gate() -> None:
    print("test_boost_and_defrost_gate (safety max blocks boost + defrost)")
    env = _make_env({}, {}, datetime(2026, 1, 1, 6, 0))
    check(render(env, MAX_TEMP, water_now=76, max_water=75) == "True",
          "boost water 76 >= max 75 -> blocked")
    check(render(env, MAX_TEMP, water_now=75, max_water=75) == "True",
          "boost water exactly 75 -> blocked")
    check(render(env, MAX_TEMP, water_now=74.9, max_water=75) == "False",
          "boost water below max -> allowed")
    check(render(env, MAX_TEMP, water_now=90, max_water=0) == "False",
          "max 0 disables the safety cap")
    base = dict(defrost_enabled=True, trigger_id="defrost_t",
                defrost_start="03:00:00", defrost_end="05:00:00", defrost_water=80,
                defrost_outdoor=2, w=78, o=1, max_water_temp_val=75,
                outdoor_temp_sensor_entity="sensor.outdoor",
                water_temp_check_entity="input_boolean.check", boiler_on=False,
                water_temp_state="78")
    e = _make_env({"sensor.outdoor": "1", "input_boolean.check": "off"}, {},
                  datetime(2026, 1, 1, 3, 30))
    check(render(e, DEFROST, **base) == "False",
          "defrost water 78 >= safety max 75 -> no defrost")
    base["max_water_temp_val"] = 0
    check(render(e, DEFROST, **base) == "True",
          "safety max 0 -> defrost allowed")


def test_scenarios() -> None:
    print("test_scenarios (full gate chain across combinations)")
    env = _make_env({}, {}, datetime(2026, 1, 1, 16, 3))

    def decide(**kw):
        base = dict(master_on=True, water_state="40.0", boiler_on=False,
                    check_on=False, presence_ok=True, solar_skip=False,
                    water_val=40.0, heat_below=45.0, max_temp=False)
        base.update(kw)
        return render(env, DECIDE, **base)

    cases = [
        ("all conditions good -> heat", {}, "heat"),
        ("master off -> master_off", {"master_on": False}, "master_off"),
        ("nobody home -> no_presence", {"presence_ok": False}, "no_presence"),
        ("sensor unknown -> sensor_bad", {"water_state": "unknown"}, "sensor_bad"),
        ("sensor unavailable -> sensor_bad", {"water_state": "unavailable"}, "sensor_bad"),
        ("sensor empty -> sensor_bad", {"water_state": ""}, "sensor_bad"),
        ("water check on -> blocked_check", {"check_on": True}, "blocked_check"),
        ("solar skip -> solar_skip", {"solar_skip": True}, "solar_skip"),
        ("water at threshold -> temp_ok", {"water_val": 45.0}, "temp_ok"),
        ("water above threshold -> temp_ok", {"water_val": 50.0}, "temp_ok"),
        ("water below threshold -> heat", {"water_val": 44.9}, "heat"),
        ("water exactly at threshold -> temp_ok", {"water_val": 45.0}, "temp_ok"),
        ("water at safety max -> max_temp", {"water_val": 75.0, "max_temp": True}, "max_temp"),
        ("safety max beats solar", {"water_val": 80.0, "max_temp": True,
                                    "solar_skip": True}, "max_temp"),
        ("boiler already on + water low -> already_on", {"boiler_on": True}, "already_on"),
        # priority: the earlier gate wins
        ("master off beats all", {"master_on": False, "presence_ok": False,
                                  "water_state": "unknown", "solar_skip": True,
                                  "boiler_on": True}, "master_off"),
        ("no presence beats sensor/check", {"presence_ok": False, "water_state": "",
                                            "check_on": True}, "no_presence"),
        ("sensor bad beats check/solar", {"water_state": "unknown", "check_on": True,
                                          "solar_skip": True}, "sensor_bad"),
        ("check beats solar/target", {"check_on": True, "solar_skip": True,
                                      "water_val": 10.0}, "blocked_check"),
        ("solar beats temp/boiler", {"solar_skip": True, "water_val": 10.0,
                                       "boiler_on": True}, "solar_skip"),
        ("temp_ok beats boiler", {"water_val": 60.0, "boiler_on": True}, "temp_ok"),
    ]
    for label, kw, expected in cases:
        got = decide(**kw)
        check(got == expected, f"{label} (got {got})")


def test_reason() -> None:
    print("test_reason (reason string recorded in input_text)")
    env = _make_env({}, {}, datetime(2026, 1, 1, 16, 3))
    check(render(env, REASON_TEXT, idx=2, reason="target_ok") == "sched 2: target_ok",
          "reason composed for schedule 2")
    check(render(env, REASON_TEXT, idx=6, reason="heating") == "sched 6: heating",
          "reason composed for schedule 6")
    check(render(env, REASON_TEXT, idx=1, reason="solar_skip") == "sched 1: solar_skip",
          "reason composed for schedule 1")


def test_time_left() -> None:
    print("test_time_left (reverse countdown minutes + percent)")
    env = _make_env({}, {}, datetime(2026, 1, 1, 16, 3))

    def mins(max_time, elapsed):
        return float(render(env, TIME_LEFT_MIN, max_time=max_time, elapsed=elapsed))

    # max 60 min
    check(mins(60, 0) == 60.0, "at start -> 60 min left")
    check(mins(60, 30) == 30.0, "half way -> 30 min left")
    check(mins(60, 60) == 0.0, "at end -> 0 min left")
    check(mins(60, 75) == 0.0, "past end -> clamped to 0")
    check(render(env, TIME_LEFT_PCT, max_time=60, elapsed=0) == "100",
          "at start -> 100% left")
    check(render(env, TIME_LEFT_PCT, max_time=60, elapsed=30) == "50",
          "half way -> 50% left")
    check(render(env, TIME_LEFT_PCT, max_time=60, elapsed=60) == "0",
          "at end -> 0% left")
    check(render(env, TIME_LEFT_PCT, max_time=60, elapsed=90) == "0",
          "past end -> clamped to 0%")
    check(render(env, TIME_LEFT_PCT, max_time=0, elapsed=5) == "0",
          "max 0 -> no division by zero")
    # cold vs warm weather gives different countdown
    check(mins(90, 0) == 90.0, "cold weather max 90 -> 90 min left")
    check(mins(30, 10) == 20.0, "warm weather max 30, 10 elapsed -> 20 min left")


def main() -> int:
    test_presence()
    test_solar()
    test_panel_vs_water()
    test_trigger_match()
    test_target()
    test_defrost()
    test_progress()
    test_heat_below()
    test_boost_and_defrost_gate()
    test_scenarios()
    test_reason()
    test_time_left()
    print()
    if FAILURES:
        print(f"RESULT: FAILED ({len(FAILURES)} checks)")
        return 1
    print("RESULT: ALL LOGIC CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
