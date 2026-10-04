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
  {% for z in user_1_zones_list %}
    {% if states(user_1_entity) in ['home', state_attr(z, 'friendly_name'), z.split('.')[-1]] %}
      {% set ns.here = true %}
    {% endif %}
  {% endfor %}
  {% if user_2_entity not in ['', none] %}
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
  {{ (states(solar_temp_sensor_entity) | float(-999)) >= solar_temp_threshold_val if solar_temp_sensor_entity not in ['', none] else false }}
{% elif solar_mode_val == 'both' %}
  {% set f = is_state(solar_flag_entity, 'on') if solar_flag_entity not in ['', none] else false %}
  {% set t = (states(solar_temp_sensor_entity) | float(-999)) >= solar_temp_threshold_val if solar_temp_sensor_entity not in ['', none] else false %}
  {{ f or t }}
{% else %}
  {{ false }}
{% endif %}"""

WINDOW = """{% set now_t = now().time() %}
{% set st = today_at(sched_time).time() %}
{% set delta = (now_t.hour * 60 + now_t.minute) - (st.hour * 60 + st.minute) %}
{{ 0 <= delta < 5 }}"""

TARGET = """{% if sched_temp | float(0) > 0 %}
  {{ sched_temp }}
{% else %}
  {{ cold_temp if now_out < cold_threshold_val else warm_temp }}
{% endif %}"""

DEFROST = """{% set now_t = now().time() %}
{% set start = today_at(defrost_start).time() %}
{% set end = today_at(defrost_end).time() %}
{% set in_window = (start <= now_t <= end) if start <= end else (now_t >= start or now_t <= end) %}
{{ in_window and w <= defrost_water and o <= defrost_outdoor }}"""

PROGRESS = "{{ ([[ (hb_current / hb_target * 100) | round(0), 100 ] | min, 0] | max if hb_target > 0 else 0) | int }}"


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
    ]
    for mode, states_map, expected in cases:
        env = _make_env(states_map, attrs, datetime(2026, 1, 1, 6, 0))
        r = render(env, SOLAR, solar_mode_val=mode, **base)
        check(r == str(expected), f"solar mode={mode} states={states_map} -> {expected}")


def test_window() -> None:
    print("test_window (5-minute schedule window)")
    env = _make_env({}, {}, datetime(2026, 1, 1, 6, 2))
    check(render(env, WINDOW, sched_time="06:00:00") == "True", "06:02 matches 06:00 window")
    env = _make_env({}, {}, datetime(2026, 1, 1, 6, 4))
    check(render(env, WINDOW, sched_time="06:00:00") == "True", "06:04 matches 06:00 window")
    env = _make_env({}, {}, datetime(2026, 1, 1, 6, 5))
    check(render(env, WINDOW, sched_time="06:00:00") == "False", "06:05 no longer matches")
    env = _make_env({}, {}, datetime(2026, 1, 1, 5, 59))
    check(render(env, WINDOW, sched_time="06:00:00") == "False", "05:59 before window")


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
    print("test_defrost (time window, including past-midnight)")
    ctx = dict(defrost_start="03:00:00", defrost_end="05:00:00", defrost_water=4,
               defrost_outdoor=2, w=3, o=1)
    env = _make_env({}, {}, datetime(2026, 1, 1, 4, 0))
    check(render(env, DEFROST, **ctx) == "True", "inside window + cold -> true")
    env = _make_env({}, {}, datetime(2026, 1, 1, 6, 0))
    check(render(env, DEFROST, **ctx) == "False", "outside window -> false")
    # past-midnight window 23:00 -> 02:00
    ctx2 = dict(defrost_start="23:00:00", defrost_end="02:00:00", defrost_water=4,
                defrost_outdoor=2, w=3, o=1)
    env = _make_env({}, {}, datetime(2026, 1, 1, 0, 30))
    check(render(env, DEFROST, **ctx2) == "True", "past-midnight window 00:30 -> true")
    env = _make_env({}, {}, datetime(2026, 1, 1, 12, 0))
    check(render(env, DEFROST, **ctx2) == "False", "past-midnight window 12:00 -> false")


def test_progress() -> None:
    print("test_progress (clamped 0-100)")
    env = _make_env({}, {}, datetime(2026, 1, 1, 6, 0))
    check(render(env, PROGRESS, hb_current=30, hb_target=60) == "50", "30/60 -> 50%")
    check(render(env, PROGRESS, hb_current=80, hb_target=60) == "100", "over target -> 100%")
    check(render(env, PROGRESS, hb_current=0, hb_target=0) == "0", "zero target -> 0%")


def main() -> int:
    test_presence()
    test_solar()
    test_window()
    test_target()
    test_defrost()
    test_progress()
    print()
    if FAILURES:
        print(f"RESULT: FAILED ({len(FAILURES)} checks)")
        return 1
    print("RESULT: ALL LOGIC CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
