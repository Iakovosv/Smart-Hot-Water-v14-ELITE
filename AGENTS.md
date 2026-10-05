# AGENTS.md

Persistent notes for AI agents working in this repository.

## What this repo is
A Home Assistant custom integration + blueprint for "smart hot water" (GSW).
Greek UI. Key paths:
- `custom_components/gsw_hotwater/blueprints/gsw_smart_hot_water.yaml` - main blueprint
- `custom_components/gsw_hotwater/blueprints/gsw_boiler_safety.yaml` - safety watchdog
- `helpers/gsw_hotwater.yaml` - helper entities (package)
- `dashboard/` - Lovelace cards (13 individual cards + full dashboard + vertical card)
- `tests/run_tests.py`, `tests/test_logic.py`

## How to verify changes (do ALL of these)
Run from repo root. Home Assistant **is installed** in the sandbox, so the
real-engine checks run (they self-skip if HA is absent).

```bash
python3 tests/run_tests.py      # 296 checks, blueprint + dashboard + real HA
python3 tests/test_logic.py     # blueprint logic checks
```

`run_tests.py` already includes the checks that matter:
- blueprint structure / inputs / Jinja / action shape
- **real HA blueprint substitution + schema** (`test_ha_blueprint_save`, 3 input modes)
- dashboard YAML parse, built-in card types, entity_id format
- **real HA template render** of every markdown card (`test_ha_card_render`)
  with a negative control that reproduces the old `as_timestamp '00:00:00'` crash
- conditional cards against the documented Lovelace schema

### Full-config check (strongest, end-to-end)
Assemble a throwaway HA config and let HA validate it:

```bash
rm -rf /tmp/haconfig && mkdir -p /tmp/haconfig/packages \
  /tmp/haconfig/blueprints/automation/gsw
cp helpers/gsw_hotwater.yaml /tmp/haconfig/packages/
cp custom_components/gsw_hotwater/blueprints/*.yaml /tmp/haconfig/blueprints/automation/gsw/
printf 'homeassistant:\n  packages: !include_dir_named packages\nautomation: !include automations.yaml\n' \
  > /tmp/haconfig/configuration.yaml
printf '[]\n' > /tmp/haconfig/automations.yaml
python3 -m homeassistant --config /tmp/haconfig --script check_config
```

A clean run prints only `Testing configuration at /tmp/haconfig` and exits 0.
Do NOT add `default_config:` - it triggers network installs of many packages.
Sanity-check the harness by adding a bogus domain; it must report
`Integration '...' not found`.

## Hard-won lessons
- **YAML/Jinja parse tests are not enough.** They pass on templates that crash
  at runtime. Always render templates with a real `HomeAssistant` instance.
- `input_datetime.water_heater_on` can be **time-only** (`00:00:00`).
  `as_timestamp("00:00:00")` raises `ValueError: not a valid date/time`.
  Never call `as_timestamp` on it; read the remaining-minutes helper instead.
- HA's template `as_timestamp`/`as_datetime` raise unless a `default` is given.
- HA gauge `severity` keys are **sorted by value**; the largest wins the top of
  the range. For a "hot = red" thermometer use `green < yellow < red`
  (e.g. water `0/35/50`). `green:45, yellow:30, red:0` paints hot water green.
- Card displays must round: `states('sensor.x') | float(0) | round(1)`, or the
  raw sensor prints 15 digits.
- Lovelace **conditional cards** use `entity`/`state` (frontend schema), NOT the
  automation `entity_id`. `state` may be a list (OR). The backend
  `condition.async_validate_condition_config` is the *wrong* validator for them.
- The reverse countdown is driven by `input_number.gsw_time_left_minutes`, which
  the blueprint already counts down; cards just format it as mm:ss.
- **`repeat/until` timing:** HA evaluates `until` **after** the sequence body,
  so a `delay` inside the body is NOT interrupted when the condition flips.
  Verified against `homeassistant/helpers/script.py` and empirically (a
  condition set true 1s into a 5s delay still waited the full 5s). The boost and
  scheduled loops poll every 30s, so heating stops within **≤30s** of the target
  being reached or the max time elapsing - not instantly. Boost now has an
  **already-hot pre-check** (v1.12.7): if the water is at/above the boost target
  it does not turn the relay on at all (status -> `Target reached`, reason
  `already_hot_boost`); the safety cap `max_water_temp` is pre-checked too.
  The scheduled path keeps its `< heat_below` guard.
- The integration **never** writes `automations.yaml`; it only refreshes the
  blueprint *definition*. Blueprint input values live in `automations.yaml` and
  survive updates (verified against the real HA engine).
- `installer.install_blueprints` must write **atomically** (temp + `os.replace`)
  and only when content changed. A plain copy over a live file can be read
  half-written by HA at startup, making an automation show empty/default inputs.
- Optional helper entities (`gsw_time_left_minutes`, `gsw_time_left_pct`,
  `gsw_last_reason`, `gsw_solar_skip`, `gsw_boiler_status`) live in
  `helpers/gsw_hotwater.yaml`; without them the UI shows `unknown` / "Entity not found".

## Release flow
1. Bump `custom_components/gsw_hotwater/manifest.json` + `version.json`.
2. Add a changelog entry at the top of the root `README.md`.
3. Run the tests above.
4. Commit and push (the repo forbids agent-identity strings in tracked files).
5. Create a GitHub release with `curl` against the releases API.
