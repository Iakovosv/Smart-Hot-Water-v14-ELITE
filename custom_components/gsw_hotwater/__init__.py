"""GSW Smart Hot Water - Home Assistant custom integration.

Installs the bundled automation blueprint and keeps it up to date on startup.
Configuration is intentionally UI-driven (blueprint inputs + your own helpers),
so no YAML or config flow is required.
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .installer import install_blueprint, read_version

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = []


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Install/refresh the blueprint on Home Assistant startup."""
    result = install_blueprint(hass.config.config_dir, force=True)
    if result.get("ok"):
        _LOGGER.info(
            "GSW Smart Hot Water: blueprint v%s installed at %s",
            result.get("version"),
            result.get("path"),
        )
    else:
        _LOGGER.error(
            "GSW Smart Hot Water: blueprint install failed (%s)",
            result.get("reason"),
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up via config entry (UI)."""
    hass.data.setdefault(DOMAIN, {})
    install_blueprint(hass.config.config_dir, force=True)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True
