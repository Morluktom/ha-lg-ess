"""DataUpdateCoordinator for LG ESS System Information integration."""

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


class LgEssSystemInfoDataUpdateCoordinator(LgEssBaseCoordinator):
    """Class to manage fetching system information data from the LG ESS API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name="LG ESS System Info",
            update_interval=timedelta(
                seconds=DEFAULT_SCAN_INTERVAL * 4
            ),  # Update less frequently
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update system information data via direct HTTP API calls."""
        try:
            if not self._session:
                await self.async_setup()

            data = {}

            # Get system information data
            system_data = await self.async_get_system_info()

            if system_data:
                # PMS data
                if "pms" in system_data:
                    pms = system_data["pms"]
                    data.update(
                        {
                            "pms_model": pms.get("model", ""),
                            "pms_serialno": pms.get("serialno", ""),
                            "pms_ac_input_power": self.safe_number_convert(
                                pms.get("ac_input_power", 0)
                            ),
                            "pms_ac_output_power": self.safe_number_convert(
                                pms.get("ac_output_power", 0)
                            ),
                            "pms_install_date": pms.get("install_date", ""),
                        }
                    )

                # Battery data
                if "batt" in system_data:
                    batt = system_data["batt"]
                    data.update(
                        {
                            "battery_capacity": self.safe_number_convert(
                                batt.get("capacity", 0)
                            ),
                            "battery_type": batt.get("type", ""),
                            "battery_install_date": batt.get("install_date", ""),
                            # Battery Unit 1
                            "battery_nameplate_energy_1": self.safe_number_convert(
                                batt.get("nameplate_energy_1", 0)
                            ),
                            "battery_cycle_count_1": self.safe_number_convert(
                                batt.get("hbc_cycle_count_1", 0)
                            ),
                            "battery_remaining_cap_1": self.safe_number_convert(
                                batt.get("hbc_remaining_cap_1", 0)
                            ),
                            "battery_discharge_rate_1": self.safe_number_convert(
                                batt.get("hbc_dischg_rate_1", 0)
                            ),
                            "battery_charge_energy_1": self.safe_number_convert(
                                batt.get("hbc_chg_energy_1", 0)
                            ),
                            "battery_discharge_energy_1": self.safe_number_convert(
                                batt.get("hbc_dischg_energy_1", 0)
                            ),
                            "battery_charge_cap_1": self.safe_number_convert(
                                batt.get("hbc_chg_cap_1", 0)
                            ),
                            "battery_discharge_cap_1": self.safe_number_convert(
                                batt.get("hbc_dischg_cap_1", 0)
                            ),
                            "battery_deep_discharge_count_1": self.safe_number_convert(
                                batt.get("hbc_deep_dischg_cnt_1", 0)
                            ),
                            "battery_overcharge_count_1": self.safe_number_convert(
                                batt.get("hbc_over_chg_cnt_1", 0)
                            ),
                            # Battery Unit 2
                            "battery_nameplate_energy_2": self.safe_number_convert(
                                batt.get("nameplate_energy_2", 0)
                            ),
                            "battery_cycle_count_2": self.safe_number_convert(
                                batt.get("hbc_cycle_count_2", 0),
                            ),
                            "battery_remaining_cap_2": self.safe_number_convert(
                                batt.get("hbc_remaining_cap_2", 0)
                            ),
                            "battery_discharge_rate_2": self.safe_number_convert(
                                batt.get("hbc_dischg_rate_2", 0)
                            ),
                            "battery_charge_energy_2": self.safe_number_convert(
                                batt.get("hbc_chg_energy_2", 0)
                            ),
                            "battery_discharge_energy_2": self.safe_number_convert(
                                batt.get("hbc_dischg_energy_2", 0)
                            ),
                            "battery_charge_cap_2": self.safe_number_convert(
                                batt.get("hbc_chg_cap_2", 0)
                            ),
                            "battery_discharge_cap_2": self.safe_number_convert(
                                batt.get("hbc_dischg_cap_2", 0)
                            ),
                            "battery_deep_discharge_count_2": self.safe_number_convert(
                                batt.get("hbc_deep_dischg_cnt_2", 0)
                            ),
                            "battery_overcharge_count_2": self.safe_number_convert(
                                batt.get("hbc_over_chg_cnt_2", 0)
                            ),
                            # Battery Serial Numbers and Pack Dates
                            "battery_a_serials": batt.get("hbc_a_serials", ""),
                            "battery_b_serials": batt.get("hbc_b_serials", ""),
                            "battery_a_pack_dates": batt.get("hbc_a_pack_dates", ""),
                            "battery_b_pack_dates": batt.get("hbc_b_pack_dates", ""),
                        }
                    )

                # Version data
                if "version" in system_data:
                    version = system_data["version"]
                    data.update(
                        {
                            "pms_version": version.get("pms_version", ""),
                            "pms_build_date": version.get("pms_build_date", ""),
                            "pcs_version": version.get("pcs_version", ""),
                            "bms_version": version.get("bms_version", "").strip(),
                            "bms_unit1_version": version.get(
                                "bms_unit1_version", ""
                            ).strip(),
                            "bms_unit2_version": version.get(
                                "bms_unit2_version", ""
                            ).strip(),
                        }
                    )

            return data

        except Exception as err:
            _LOGGER.error("Error communicating with LG ESS System Info: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
