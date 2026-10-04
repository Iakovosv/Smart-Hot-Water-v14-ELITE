"""Blueprint installer for GSW Smart Hot Water.

Pure-Python helper with no Home Assistant imports, so it can be unit-tested
standalone. It copies the bundled automation blueprints into the Home Assistant
configuration directory and tracks the installed version.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

DOMAIN = "gsw_hotwater"
BLUEPRINT_RELATIVE_DIR = Path("blueprints") / "automation" / DOMAIN

# Bundled blueprints: main controller + independent safety watchdog.
BLUEPRINTS = (
    "gsw_smart_hot_water.yaml",
    "gsw_boiler_safety.yaml",
)

_PACKAGE_DIR = Path(__file__).resolve().parent
_SOURCE_DIR = _PACKAGE_DIR / "blueprints"
_VERSION_FILE = _PACKAGE_DIR / "version.json"


def read_version() -> str:
    """Return the bundled integration/blueprint version."""
    if _VERSION_FILE.exists():
        return json.loads(_VERSION_FILE.read_text(encoding="utf-8")).get("version", "0")
    return "0"


def blueprint_source(name: str) -> Path:
    """Return the path of a bundled blueprint file."""
    return _SOURCE_DIR / name


def install_blueprints(config_dir: str | Path, force: bool = True) -> dict:
    """Copy all bundled blueprints into <config_dir>/blueprints/automation/gsw_hotwater/.

    Returns a dict describing the result. Never raises for the normal
    "already installed, same version" case.
    """
    config_dir = Path(config_dir)
    target_dir = config_dir / BLUEPRINT_RELATIVE_DIR
    version = read_version()

    missing = [n for n in BLUEPRINTS if not blueprint_source(n).exists()]
    if missing:
        return {"ok": False, "reason": "bundled_blueprint_missing", "missing": missing}

    installed_version = None
    version_file = target_dir / "version.json"
    if version_file.exists():
        try:
            installed_version = json.loads(version_file.read_text(encoding="utf-8")).get("version")
        except (OSError, ValueError):
            installed_version = None

    if installed_version == version and not force and target_dir.exists():
        return {"ok": True, "changed": False, "version": version,
                "path": str(target_dir), "files": list(BLUEPRINTS)}

    target_dir.mkdir(parents=True, exist_ok=True)
    for name in BLUEPRINTS:
        shutil.copyfile(blueprint_source(name), target_dir / name)
    version_file.write_text(json.dumps({"version": version}), encoding="utf-8")

    return {"ok": True, "changed": True, "version": version,
            "path": str(target_dir), "files": list(BLUEPRINTS)}


# Backwards-compatible single-file helper.
def install_blueprint(config_dir: str | Path, force: bool = True) -> dict:
    """Alias kept for compatibility; installs all bundled blueprints."""
    return install_blueprints(config_dir, force=force)
