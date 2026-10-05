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
- Lovelace **conditional cards** use `entity`/`state` (frontend schema), NOT the
  automation `entity_id`. `state` may be a list (OR). The backend
  `condition.async_validate_condition_config` is the *wrong* validator for them.
- The reverse countdown is driven by `input_number.gsw_time_left_minutes`, which
  the blueprint already counts down; cards just format it as mm:ss.
- Optional helper entities (`gsw_time_left_minutes`, `gsw_time_left_pct`,
  `gsw_last_reason`, `gsw_solar_skip`, `gsw_boiler_status`) live in
  `helpers/gsw_hotwater.yaml`; without them the UI shows `unknown` / "Entity not found".

## Release flow
1. Bump `custom_components/gsw_hotwater/manifest.json` + `version.json`.
2. Add a changelog entry at the top of the root `README.md`.
3. Run the tests above.
4. Commit (include `Co-authored-by: openhands <openhands@all-hands.dev>`), push.
5. Create a GitHub release with `curl` against the releases API.
