"""Base DataUpdateCoordinator for LG ESS integration."""

from __future__ import annotations

import logging
import json
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    DEFAULT_SCAN_INTERVAL,
)

from .lg_ess import (
    LgEss,
    LgEssAuthException,
    LgEssException,
    LgEssChargingModes,
    LgEssOperationModes,
)

_LOGGER = logging.getLogger(__name__)


class LgEssBaseCoordinator(DataUpdateCoordinator):
    """Base class for LG ESS coordinators with shared functionality."""

    _lgEss: LgEss

    def __init__(
        self,
        hass: HomeAssistant,
        lgEss: LgEss,
        logger,
        name: str,
        update_interval: timedelta,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        self.hass = hass
        self.entry = config_entry
        self._host = config_entry.data[CONF_HOST]
        self._password = config_entry.data[CONF_PASSWORD]
        self._session = None
        self._auth_key = None
        self._lgEss = lgEss

        # Device info for all entities
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name="LG ESS",
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=None,
            configuration_url=f"https://{self._host}",
        )

        super().__init__(
            hass,
            logger,
            name=name,
            update_interval=update_interval,
            config_entry=config_entry,
        )

    def safe_number_convert(self, value):
        """Konvertiert einen Wert sicher zu einer Zahl."""
        # Bereits eine Zahl?
        if isinstance(value, (int, float)):
            return value

        # Versuche String zu Zahl zu konvertieren
        if isinstance(value, str):
            try:
                # Erst versuchen als int
                if "." not in value:
                    return int(value)
                else:
                    return float(value)
            except ValueError:
                return None
        return None

    def safe_bool(self, value):
        """Safely convert value to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value > 0
        if isinstance(value, str):
            return value.lower() in ("true", "1", "on", "yes")
        return False

    # Control methods using direct API calls _get_home_data_get_home_data
    async def async_set_winter_mode(self, enabled: bool) -> None:
        """Set winter mode."""
        try:
            await self._lgEss.set_winter_mode(enabled)

            await self.async_request_refresh()
        except LgEssException as err:
            _LOGGER.error("%s", err)
        except Exception as err:
            _LOGGER.error("Failed to set winter mode: %s", err)
            raise err

    async def async_set_operation_mode(self, mode: str) -> None:
        """Set operation mode."""
        try:
            if mode == "start":
                opMode = LgEssOperationModes.START
            else:
                opMode = LgEssOperationModes.STOP

            await self._lgEss.set_operation_mode(mode)

            await self.async_request_refresh()
        except LgEssException as err:
            _LOGGER.error("%s", err)
        except Exception as err:
            _LOGGER.error("Failed to set operation mode: %s", err)
            raise err

    async def async_set_backup_mode(self, enabled: bool) -> None:
        """Set backup mode."""
        try:
            await self._lgEss.set_backup_mode(enabled)

            await self.async_request_refresh()
        except LgEssException as err:
            _LOGGER.error("%s", err)
        except Exception as err:
            _LOGGER.error("Failed to set backup mode: %s", err)
            raise err

    async def async_set_charge_from_grid(self, enabled: bool) -> None:
        """Set charge from grid."""
        try:
            await self._lgEss.set_charge_from_grid(enabled)

            await self.async_request_refresh()
        except LgEssException as err:
            _LOGGER.error("%s", err)
        except Exception as err:
            _LOGGER.error("Failed to set charge from grid mode: %s", err)
            raise err

    async def async_set_charging_mode(self, mode: str) -> None:
        """Set charging mode."""
        try:
            if mode == "fast_charge":
                chargingMode = LgEssChargingModes.FAST_CHARGE
            elif mode == "battery_care":
                chargingMode = LgEssChargingModes.BATTERY_CARE
            elif mode == "weather_forecast":
                chargingMode = LgEssChargingModes.WEATHER_FORECAST
            else:
                chargingMode = LgEssChargingModes.BATTERY_CARE

            await self._lgEss.set_charging_mode(chargingMode)

            await self.async_request_refresh()
        except LgEssException as err:
            _LOGGER.error("%s", err)
        except Exception as err:
            _LOGGER.error("Failed to set charging mode: %s", err)
            raise err

    async def async_set_backup_soc(self, value: int) -> None:
        """Set backup soc."""
        try:
            await self._lgEss.set_backup_soc(value)

            await self.async_request_refresh()
        except LgEssException as err:
            _LOGGER.error("%s", err)
        except Exception as err:
            _LOGGER.error("Failed to set backup soc setting: %s", err)
            raise err


class LgEssSettingsDataUpdateCoordinator(LgEssBaseCoordinator):
    """Class to manage fetching settings data from the LG ESS API."""

    def __init__(self, hass: HomeAssistant, lgEss: LgEss, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            lgEss,
            _LOGGER,
            name="LG ESS Settings",
            # Settings ändern sich selten, daher längerer Intervall
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL * 3),
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update settings data via direct HTTP API calls."""
        try:
            data = {}

            # Get Battery settings
            setting_bat = await self._lgEss.get_setting_battery()

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


class LgEssCommonDataUpdateCoordinator(LgEssBaseCoordinator):
    """Class to manage fetching common data from the LG ESS API."""

    def __init__(self, hass: HomeAssistant, lgEss: LgEss, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            lgEss,
            _LOGGER,
            name="LG ESS Common",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update common data via direct HTTP API calls."""
        try:
            data = {}

            # Get common data (detailed information)
            common_data = await self._lgEss.get_common_data()

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


class LgEssHomeDataUpdateCoordinator(LgEssBaseCoordinator):
    """Class to manage fetching home data from the LG ESS API."""

    def __init__(self, hass: HomeAssistant, lgEss: LgEss, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            lgEss,
            _LOGGER,
            name="LG ESS Home",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update home data via direct HTTP API calls."""
        try:
            data = {}

            # Get home statistics (main power data)
            home_data = await self._lgEss.get_home_data()

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


class LgEssSystemInfoDataUpdateCoordinator(LgEssBaseCoordinator):
    """Class to manage fetching system information data from the LG ESS API."""

    def __init__(self, hass: HomeAssistant, lgEss: LgEss, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            lgEss,
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
            data = {}

            # Get system information data
            system_data = await self._lgEss.get_system_info()

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
