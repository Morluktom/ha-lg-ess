"""DataUpdateCoordinator for LG ESS Home data integration."""

from __future__ import annotations

import asyncio
import logging
import json
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .base import LgEssBaseCoordinator
from ..const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class LgEssHomeDataUpdateCoordinator(LgEssBaseCoordinator):
    """Class to manage fetching home data from the LG ESS API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name="LG ESS Home",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update home data via direct HTTP API calls."""
        try:
            if not self._session:
                await self.async_setup()

            data = {}

            # Get home statistics (main power data)
            home_data = await self.async_get_home_data()

            if home_data and "statistics" in home_data:
                stats = home_data["statistics"]
                data.update(
                    {
                        "pv_total_power": self.safe_number_convert(
                            stats.get("pcs_pv_total_power", 0)
                        ),
                        "bat_dc_power": self.safe_number_convert(
                            stats.get("batconv_power", 0)
                        ),
                        "bat_status": self.safe_number_convert(
                            stats.get("bat_status", 0)
                        ),
                        "bat_user_soc": self.safe_number_convert(
                            stats.get("bat_user_soc", 0)
                        ),
                        "load_power": self.safe_number_convert(
                            stats.get("load_power", 0)
                        ),
                        "load_today": self.safe_number_convert(
                            stats.get("load_today", 0)
                        ),
                        "grid_power": self.safe_number_convert(
                            stats.get("grid_power", 0)
                        ),
                        "self_consumption_rate": self.safe_number_convert(
                            stats.get("current_day_self_consumption", 0)
                        ),
                        "pv_energy_today": self.safe_number_convert(
                            stats.get("current_pv_generation_sum", 0)
                        ),
                    }
                )

            # Get direction information
            if home_data and "direction" in home_data:
                direction = home_data["direction"]
                data.update(
                    {
                        "direction_is_direct_consuming": self.safe_bool(
                            direction.get("is_direct_consuming_", 0)
                        ),
                        "direction_is_battery_charging": self.safe_bool(
                            direction.get("is_battery_charging_", 0)
                        ),
                        "direction_is_battery_discharging": self.safe_bool(
                            direction.get("is_battery_discharging_", 0)
                        ),
                        "direction_is_grid_selling": self.safe_bool(
                            direction.get("is_grid_selling_", 0)
                        ),
                        "direction_is_grid_buying": self.safe_bool(
                            direction.get("is_grid_buying_", 0)
                        ),
                        "direction_is_charging_from_grid": self.safe_bool(
                            direction.get("is_charging_from_grid_", 0)
                        ),
                    }
                )

            # Get operation mode
            if home_data and "operation" in home_data:
                operation = home_data["operation"]
                data.update(
                    {
                        "operation_status": operation.get("status", "unknown"),
                        "operation_mode": operation.get("mode", 0),
                    }
                )

            # Calculate directional sensors
            self._calculate_directional_sensors(data)

            # Add system online status
            data["system_online"] = True
            data["pv_generating"] = data.get("pv_total_power", 0) > 0

            return data

        except Exception as err:
            _LOGGER.error("Error communicating with LG ESS Home: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def _calculate_directional_sensors(self, data: dict[str, Any]) -> None:
        """Calculate directional sensors (positive/negative values based on direction)."""
        try:
            # Battery directional (positive = charging, negative = discharging)
            bat_power = data.get("bat_dc_power", 0)
            is_charging = data.get("direction_is_battery_charging", 0)
            is_discharging = data.get("direction_is_battery_discharging", 0)

            if is_charging:
                data["batt_directional"] = abs(bat_power)
            elif is_discharging:
                data["batt_directional"] = -abs(bat_power)
            else:
                data["batt_directional"] = 0

            # Grid directional (positive = import, negative = export)
            grid_power = data.get("grid_power", 0)
            is_buying = data.get("direction_is_grid_buying", 0)
            is_selling = data.get("direction_is_grid_selling", 0)

            if is_buying:
                data["grid_directional"] = abs(grid_power)
            elif is_selling:
                data["grid_directional"] = -abs(grid_power)
            else:
                data["grid_directional"] = 0

            # Remove original power values to avoid confusion
            data.pop("bat_dc_power", None)
            data.pop("grid_power", None)

        except Exception as err:
            _LOGGER.warning("Failed to calculate directional sensors: %s", err)
