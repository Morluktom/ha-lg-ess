"""DataUpdateCoordinator for LG ESS Settings data integration."""

from __future__ import annotations

import asyncio
import logging
import json
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from .base import LgEssBaseCoordinator
from ..const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class LgEssSettingsDataUpdateCoordinator(LgEssBaseCoordinator):
    """Class to manage fetching settings data from the LG ESS API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name="LG ESS Settings",
            # Settings ändern sich selten, daher längerer Intervall
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL * 3),
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update settings data via direct HTTP API calls."""
        try:
            if not self._session:
                await self.async_setup()

            data = {}

            # Get Battery settings
            setting_bat = await self.async_get_setting_battery()

            if setting_bat:
                data.update(
                    {
                        "winter_mode": setting_bat.get("winter_setting", "off"),
                        "winter_status": setting_bat.get("winter_setting", "off"),
                        "backup_mode": setting_bat.get("backup_setting", "off"),
                        "backup_status": setting_bat.get("backup_setting", "off"),
                        "auto_charge": setting_bat.get("auto_charge", "off"),
                        "auto_charge_status": setting_bat.get(
                            "charging_from_grid_to_keep_soc", "0"
                        ),
                        "charging_mode": setting_bat.get("alg_setting"),
                        "backup_soc": self.safe_number_convert(
                            setting_bat.get("backup_soc")
                        ),
                    }
                )

            return data

        except Exception as err:
            _LOGGER.error("Error communicating with LG ESS Settings: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
