"""Config flow for GSW Smart Hot Water.

There is nothing to configure - adding the integration simply installs/updates
the bundled blueprints. A config flow is still required so Home Assistant
actually loads the integration and calls setup (a bare async_setup is not
called unless the integration is referenced in configuration.yaml).
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigFlow

from .const import DOMAIN
from .installer import install_blueprint


class GswHotWaterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Single-instance flow that installs the bundled blueprints."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            install_blueprint(self.hass.config.config_dir, force=True)
            return self.async_create_entry(title="GSW Smart Hot Water", data={})

        return self.async_show_form(step_id="user")
