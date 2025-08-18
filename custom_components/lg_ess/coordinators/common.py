"""DataUpdateCoordinator for LG ESS Common data integration."""

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


class LgEssCommonDataUpdateCoordinator(LgEssBaseCoordinator):
    """Class to manage fetching common data from the LG ESS API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name="LG ESS Common",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update common data via direct HTTP API calls."""
        try:
            if not self._session:
                await self.async_setup()

            data = {}

            # Get common data (detailed information)
            common_data = await self.async_get_common_data()

            if common_data:
                # PV data
                if "PV" in common_data:
                    pv = common_data["PV"]
                    data.update(
                        {
                            "pv_brand": pv.get("brand", ""),
                            "pv_capacity": self.safe_number_convert(
                                pv.get("capacity", 0)
                            ),
                            "pv1_voltage": self.safe_number_convert(
                                pv.get("pv1_voltage", 0)
                            ),
                            "pv2_voltage": self.safe_number_convert(
                                pv.get("pv2_voltage", 0)
                            ),
                            "pv3_voltage": self.safe_number_convert(
                                pv.get("pv3_voltage", 0)
                            ),
                            "pv1_power": self.safe_number_convert(
                                pv.get("pv1_power", 0)
                            ),
                            "pv2_power": self.safe_number_convert(
                                pv.get("pv2_power", 0)
                            ),
                            "pv3_power": self.safe_number_convert(
                                pv.get("pv3_power", 0)
                            ),
                            "pv1_current": self.safe_number_convert(
                                pv.get("pv1_current", 0)
                            ),
                            "pv2_current": self.safe_number_convert(
                                pv.get("pv2_current", 0)
                            ),
                            "pv3_current": self.safe_number_convert(
                                pv.get("pv3_current", 0)
                            ),
                            "pv_energy_today": self.safe_number_convert(
                                pv.get("today_pv_generation_sum", 0)
                            ),
                            "pv_energy_month": self.safe_number_convert(
                                pv.get("today_month_pv_generation_sum", 0)
                            ),
                        }
                    )

                # Battery data
                if "BATT" in common_data:
                    batt = common_data["BATT"]
                    data.update(
                        {
                            "bat_energy_discharge_today": self.safe_number_convert(
                                batt.get("today_batt_discharge_enery", 0)
                            ),
                            "bat_energy_charge_today": self.safe_number_convert(
                                batt.get("today_batt_charge_energy", 0)
                            ),
                            "bat_energy_charge_month": self.safe_number_convert(
                                batt.get("month_batt_charge_energy", 0)
                            ),
                            "bat_energy_discharge_month": self.safe_number_convert(
                                batt.get("month_batt_discharge_energy", 0)
                            ),
                        }
                    )

                # Grid data
                if "GRID" in common_data:
                    grid = common_data["GRID"]
                    data.update(
                        {
                            "grid_voltage": self.safe_number_convert(
                                grid.get("a_phase", 0)
                            ),
                            "grid_frequency": self.safe_number_convert(
                                grid.get("freq", 0)
                            ),
                            "grid_energy_feed_in_today": self.safe_number_convert(
                                grid.get("today_grid_feed_in_energy", 0)
                            ),
                            "grid_energy_purchase_today": self.safe_number_convert(
                                grid.get("today_grid_power_purchase_energy", 0)
                            ),
                            "grid_energy_feed_in_month": self.safe_number_convert(
                                grid.get("month_grid_feed_in_energy", 0)
                            ),
                            "grid_energy_purchase_month": self.safe_number_convert(
                                grid.get("month_grid_power_purchase_energy", 0)
                            ),
                        }
                    )

                # Load data
                if "LOAD" in common_data:
                    load = common_data["LOAD"]
                    data.update(
                        {
                            "load_consumption_today": self.safe_number_convert(
                                load.get("today_load_consumption_sum", 0)
                            ),
                            "load_consumption_month": self.safe_number_convert(
                                load.get("month_load_consumption_sum", 0)
                            ),
                            "pv_direct_today": self.safe_number_convert(
                                load.get("today_pv_direct_consumption_enegy", 0)
                            ),
                            "pv_direct_month": self.safe_number_convert(
                                load.get("month_pv_direct_consumption_energy", 0)
                            ),
                        }
                    )

            return data

        except Exception as err:
            _LOGGER.error("Error communicating with LG ESS Common: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
