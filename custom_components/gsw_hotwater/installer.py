"""Blueprint installer for GSW Smart Hot Water.

Pure-Python helper with no Home Assistant imports, so it can be unit-tested
standalone. It copies the bundled automation blueprints into the Home Assistant
configuration directory and tracks the installed version.
"""
from __future__ import annotations

import json
import os
import tempfile
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


def _write_atomic(path: Path, text: str) -> None:
    """Write text to path atomically (temp file in the same dir + os.replace).

    A plain copy over a live file can be observed half-written by a concurrent
    reader; Home Assistant reads blueprints at startup, so a torn file can make
    an automation's blueprint fail to load.
    """
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def install_blueprints(config_dir: str | Path, force: bool = True) -> dict:
    """Copy all bundled blueprints into <config_dir>/blueprints/automation/gsw_hotwater/.

    Files whose content is already identical are left untouched (no needless
    rewrite of a file Home Assistant may be reading). Changed files are backed
    up to ``<name>.bak`` and written atomically. Returns a dict describing the
    result; never raises for the normal "already up to date" case.
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
    changed: list[str] = []
    for name in BLUEPRINTS:
        source_text = blueprint_source(name).read_text(encoding="utf-8")
        target = target_dir / name
        current = target.read_text(encoding="utf-8") if target.exists() else None
        if current == source_text:
            continue
        if current is not None:
            _write_atomic(target.with_suffix(target.suffix + ".bak"), current)
        _write_atomic(target, source_text)
        changed.append(name)

    version_text = json.dumps({"version": version})
    current_version_text = version_file.read_text(encoding="utf-8") if version_file.exists() else None
    if current_version_text != version_text:
        _write_atomic(version_file, version_text)

    return {"ok": True, "changed": bool(changed), "version": version,
            "path": str(target_dir), "files": list(BLUEPRINTS), "updated": changed}


# Backwards-compatible single-file helper.
def install_blueprint(config_dir: str | Path, force: bool = True) -> dict:
    """Alias kept for compatibility; installs all bundled blueprints."""
    return install_blueprints(config_dir, force=force)
