from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

from .coordinators.home import LgEssHomeDataUpdateCoordinator
from .coordinators.common import LgEssCommonDataUpdateCoordinator
from .coordinators.batt_settings import LgEssSettingsDataUpdateCoordinator
from .coordinators.system_info import LgEssSystemInfoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


# Entity definitions: (coordinator_key, sensor_key, unit, device_class, state_class, icon)
ENTITY_DEFINITIONS = [
    # Load sensors
    (
        "home_coordinator",
        "load_power",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:home",
    ),
    # Battery sensors
    (
        "home_coordinator",
        "bat_user_soc",
        PERCENTAGE,
        SensorDeviceClass.BATTERY,
        SensorStateClass.MEASUREMENT,
        "mdi:battery",
    ),
    (
        "home_coordinator",
        "bat_status",
        None,
        SensorDeviceClass.ENUM,
        None,
        "mdi:battery-heart",
    ),
    (
        "home_coordinator",
        "batt_directional",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:battery-charging-outline",
    ),
    (
        "common_coordinator",
        "bat_energy_charge_today",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-plus",
    ),
    (
        "common_coordinator",
        "bat_energy_discharge_today",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-minus",
    ),
    (
        "common_coordinator",
        "bat_energy_charge_month",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-plus",
    ),
    (
        "common_coordinator",
        "bat_energy_discharge_month",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-minus",
    ),
    # Battery detailed information from PMS/BMS
    (
        "system_info_coordinator",
        "battery_capacity",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY_STORAGE,
        None,
        "mdi:battery-high",
    ),
    (
        "system_info_coordinator",
        "battery_type",
        None,
        None,
        None,
        "mdi:information-outline",
    ),
    (
        "system_info_coordinator",
        "battery_install_date",
        None,
        None,
        None,
        "mdi:calendar",
    ),
    (
        "system_info_coordinator",
        "battery_nameplate_energy_1",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        None,
        "mdi:battery-outline",
    ),
    (
        "system_info_coordinator",
        "battery_cycle_count_1",
        None,
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:counter",
    ),
    (
        "system_info_coordinator",
        "battery_remaining_cap_1",
        "Ah",
        None,
        None,
        "mdi:battery-medium",
    ),
    (
        "system_info_coordinator",
        "battery_discharge_rate_1",
        PERCENTAGE,
        None,
        SensorStateClass.MEASUREMENT,
        "mdi:battery-arrow-down-outline",
    ),
    (
        "system_info_coordinator",
        "battery_charge_energy_1",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-plus-outline",
    ),
    (
        "system_info_coordinator",
        "battery_discharge_energy_1",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-minus-outline",
    ),
    (
        "system_info_coordinator",
        "battery_charge_cap_1",
        "Ah",
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-charging-80",
    ),
    (
        "system_info_coordinator",
        "battery_discharge_cap_1",
        "Ah",
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-arrow-down",
    ),
    (
        "system_info_coordinator",
        "battery_deep_discharge_count_1",
        None,
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-alert",
    ),
    (
        "system_info_coordinator",
        "battery_overcharge_count_1",
        None,
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-alert-variant",
    ),
    # Battery Unit 2 (if present)
    (
        "system_info_coordinator",
        "battery_nameplate_energy_2",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        None,
        "mdi:battery-outline",
    ),
    (
        "system_info_coordinator",
        "battery_cycle_count_2",
        None,
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:counter",
    ),
    (
        "system_info_coordinator",
        "battery_remaining_cap_2",
        "Ah",
        None,
        None,
        "mdi:battery-medium",
    ),
    (
        "system_info_coordinator",
        "battery_discharge_rate_2",
        PERCENTAGE,
        None,
        SensorStateClass.MEASUREMENT,
        "mdi:battery-arrow-down-outline",
    ),
    (
        "system_info_coordinator",
        "battery_charge_energy_2",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-plus-outline",
    ),
    (
        "system_info_coordinator",
        "battery_discharge_energy_2",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-minus-outline",
    ),
    (
        "system_info_coordinator",
        "battery_charge_cap_2",
        "Ah",
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-charging-80",
    ),
    (
        "system_info_coordinator",
        "battery_discharge_cap_2",
        "Ah",
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-arrow-down",
    ),
    (
        "system_info_coordinator",
        "battery_deep_discharge_count_2",
        None,
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-alert",
    ),
    (
        "system_info_coordinator",
        "battery_overcharge_count_2",
        None,
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-alert-variant",
    ),
    # Battery Serial Numbers and Pack Dates
    (
        "system_info_coordinator",
        "battery_a_serials",
        None,
        None,
        None,
        "mdi:identifier",
    ),
    (
        "system_info_coordinator",
        "battery_b_serials",
        None,
        None,
        None,
        "mdi:identifier",
    ),
    (
        "system_info_coordinator",
        "battery_a_pack_dates",
        None,
        None,
        None,
        "mdi:calendar-range",
    ),
    (
        "system_info_coordinator",
        "battery_b_pack_dates",
        None,
        None,
        None,
        "mdi:calendar-range",
    ),
    # Grid sensors
    (
        "home_coordinator",
        "grid_directional",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:transmission-tower",
    ),
    (
        "common_coordinator",
        "grid_frequency",
        UnitOfFrequency.HERTZ,
        SensorDeviceClass.FREQUENCY,
        SensorStateClass.MEASUREMENT,
        "mdi:sine-wave",
    ),
    (
        "common_coordinator",
        "grid_voltage",
        UnitOfElectricPotential.VOLT,
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
        "mdi:flash",
    ),
    (
        "common_coordinator",
        "grid_energy_feed_in_today",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:transmission-tower-export",
    ),
    (
        "common_coordinator",
        "grid_energy_feed_in_month",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:transmission-tower-export",
    ),
    (
        "common_coordinator",
        "grid_energy_purchase_today",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:transmission-tower-import",
    ),
    (
        "common_coordinator",
        "grid_energy_purchase_month",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:transmission-tower-import",
    ),
    # PV sensors
    (
        "common_coordinator",
        "pv1_voltage",
        UnitOfElectricPotential.VOLT,
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
        "mdi:flash",
    ),
    (
        "common_coordinator",
        "pv2_voltage",
        UnitOfElectricPotential.VOLT,
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
        "mdi:flash",
    ),
    (
        "common_coordinator",
        "pv3_voltage",
        UnitOfElectricPotential.VOLT,
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
        "mdi:flash",
    ),
    (
        "common_coordinator",
        "pv1_current",
        UnitOfElectricCurrent.AMPERE,
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
        "mdi:current-dc",
    ),
    (
        "common_coordinator",
        "pv2_current",
        UnitOfElectricCurrent.AMPERE,
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
        "mdi:current-dc",
    ),
    (
        "common_coordinator",
        "pv3_current",
        UnitOfElectricCurrent.AMPERE,
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
        "mdi:current-dc",
    ),
    (
        "common_coordinator",
        "pv1_power",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:solar-panel",
    ),
    (
        "common_coordinator",
        "pv2_power",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:solar-panel",
    ),
    (
        "common_coordinator",
        "pv3_power",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:solar-panel",
    ),
    (
        "common_coordinator",
        "pv_capacity",
        "kWp",
        None,
        None,
        "mdi:solar-panel",
    ),
    (
        "common_coordinator",
        "pv_energy_today",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:solar-panel",
    ),
    (
        "common_coordinator",
        "pv_energy_month",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:solar-panel",
    ),
    (
        "home_coordinator",
        "pv_total_power",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:solar-panel",
    ),
    # PMS System Information
    (
        "system_info_coordinator",
        "pms_model",
        None,
        None,
        None,
        "mdi:information-outline",
    ),
    (
        "system_info_coordinator",
        "pms_serialno",
        None,
        None,
        None,
        "mdi:barcode",
    ),
    (
        "system_info_coordinator",
        "pms_ac_input_power",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        None,
        "mdi:power-plug",
    ),
    (
        "system_info_coordinator",
        "pms_ac_output_power",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:power-socket-eu",
    ),
    (
        "system_info_coordinator",
        "pms_install_date",
        None,
        None,
        None,
        "mdi:calendar-check",
    ),
    # Version Information
    (
        "system_info_coordinator",
        "pms_version",
        None,
        None,
        None,
        "mdi:package-variant",
    ),
    (
        "system_info_coordinator",
        "pms_build_date",
        None,
        None,
        None,
        "mdi:clock-outline",
    ),
    (
        "system_info_coordinator",
        "pcs_version",
        None,
        None,
        None,
        "mdi:package-variant-closed",
    ),
    (
        "system_info_coordinator",
        "bms_version",
        None,
        None,
        None,
        "mdi:chip",
    ),
    (
        "system_info_coordinator",
        "bms_unit1_version",
        None,
        None,
        None,
        "mdi:chip",
    ),
    (
        "system_info_coordinator",
        "bms_unit2_version",
        None,
        None,
        None,
        "mdi:chip",
    ),
    # Status and operational sensors
    ("home_coordinator", "operation_mode", None, None, None, "mdi:cog"),
    (
        "home_coordinator",
        "self_consumption_rate",
        PERCENTAGE,
        None,
        SensorStateClass.MEASUREMENT,
        "mdi:percent",
    ),
]


# Calculated sensors: (coordinator_key, sensor_key, unit, device_class, state_class, icon)
CALCULATED_SENSORS = [
    (
        "common_coordinator",
        "self_consumption_rate_month",
        PERCENTAGE,
        None,
        SensorStateClass.MEASUREMENT,
        "mdi:percent",
    ),
    (
        "common_coordinator",
        "grid_independence_rate",
        PERCENTAGE,
        None,
        SensorStateClass.MEASUREMENT,
        "mdi:home-battery",
    ),
    (
        "common_coordinator",
        "grid_independence_rate_month",
        PERCENTAGE,
        None,
        SensorStateClass.MEASUREMENT,
        "mdi:home-battery",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the LG ESS sensor platform."""
    coordinators = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Create regular sensors from entity definitions
    for (
        coordinator_key,
        sensor_key,
        unit,
        device_class,
        state_class,
        icon,
    ) in ENTITY_DEFINITIONS:
        coordinator = coordinators.get(coordinator_key)
        if coordinator:
            entities.append(
                LgEssSensor(
                    coordinator,
                    entry,
                    sensor_key,
                    unit,
                    device_class,
                    state_class,
                    icon,
                )
            )

    # Create calculated sensors
    for (
        coordinator_key,
        sensor_key,
        unit,
        device_class,
        state_class,
        icon,
    ) in CALCULATED_SENSORS:
        coordinator = coordinators.get(coordinator_key)
        if coordinator:
            entities.append(
                LgEssCalculatedSensor(
                    coordinator,
                    entry,
                    sensor_key,
                    unit,
                    device_class,
                    state_class,
                    icon,
                )
            )

    async_add_entities(entities)


class LgEssSensor(CoordinatorEntity, SensorEntity):
    """Base LG ESS sensor."""

    def __init__(
        self,
        coordinator: LgEssHomeDataUpdateCoordinator
        | LgEssCommonDataUpdateCoordinator
        | LgEssSettingsDataUpdateCoordinator
        | LgEssSystemInfoDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
        icon: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_has_entity_name = True
        self._attr_translation_key = key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_device_info = coordinator.device_info
        if icon:
            self._attr_icon = icon

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None

        value = self.coordinator.data.get(self._key)

        # Convert Wh to kWh and round to 3 decimal places
        if value is not None:
            if (
                self._key in ["pv_capacity"]
                or self._key in ["pv_energy_today"]
                or self._key in ["pv_energy_month"]
                or self._key in ["grid_energy_feed_in_today"]
                or self._key in ["grid_energy_feed_in_month"]
                or self._key in ["grid_energy_purchase_today"]
                or self._key in ["grid_energy_purchase_month"]
                or self._key in ["bat_energy_charge_today"]
                or self._key in ["bat_energy_discharge_today"]
                or self._key in ["bat_energy_charge_month"]
                or self._key in ["bat_energy_discharge_month"]
                or self._key in ["load_power"]
                or self._key in ["batt_directional"]
                or self._key in ["grid_directional"]
                or self._key in ["pv1_power"]
                or self._key in ["pv2_power"]
                or self._key in ["pv3_power"]
                or self._key in ["pv_total_power"]
                or self._key in ["battery_nameplate_energy_1"]
                or self._key in ["battery_remaining_cap_1"]
                or self._key in ["battery_charge_energy_1"]
                or self._key in ["battery_discharge_energy_1"]
                or self._key in ["battery_nameplate_energy_2"]
                or self._key in ["battery_remaining_cap_2"]
                or self._key in ["battery_charge_energy_2"]
                or self._key in ["battery_discharge_energy_2"]
                or self._key in ["pms_ac_input_power"]
            ):
                return round(float(value) / 1000, 3)

            if self._key in ["battery_capacity"]:
                return round(float(value) / 10, 1)

        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.coordinator.data is None:
            return None

        attributes = {}

        # Add timestamp of last update
        if hasattr(self.coordinator, "last_update_success_time"):
            attributes["last_updated"] = self.coordinator.last_update_success_time

        # Add specific attributes based on sensor type
        if self._key == "statistics_bat_user_soc":
            # Add battery capacity info if available
            if "battery_capacity_total" in self.coordinator.data:
                attributes["total_capacity"] = self.coordinator.data[
                    "battery_capacity_total"
                ]
            if "battery_capacity_remaining" in self.coordinator.data:
                attributes["remaining_capacity"] = self.coordinator.data[
                    "battery_capacity_remaining"
                ]

        elif self._key == "operation_mode":
            # Add operational status details
            if "system_status" in self.coordinator.data:
                attributes["system_status"] = self.coordinator.data["system_status"]

        return attributes if attributes else None


class LgEssCalculatedSensor(LgEssSensor):
    """LG ESS calculated sensor for derived values."""

    @property
    def native_value(self) -> Any:
        """Return calculated sensor value."""
        if self.coordinator.data is None:
            return None

        if self._key == "grid_independence_rate":
            # Calculate grid independence: (Load - Grid Import) / Load * 100
            load_power = self.coordinator.data.get("load_consumption_today", 0)
            grid_power = self.coordinator.data.get("grid_energy_purchase_today", 0)

            if load_power and load_power > 0:
                # Positive grid power means import
                import_power = max(0, grid_power)
                independent_power = load_power - import_power
                rate = (independent_power / load_power) * 100
                return max(0, min(100, round(rate, 1)))
            return 0
        elif self._key == "grid_independence_rate_month":
            # Calculate grid independence: (Load - Grid Import) / Load * 100
            load_power = self.coordinator.data.get("load_consumption_month", 0)
            grid_power = self.coordinator.data.get("grid_energy_purchase_month", 0)

            if load_power and load_power > 0:
                # Positive grid power means import
                import_power = max(0, grid_power)
                independent_power = load_power - import_power
                rate = (independent_power / load_power) * 100
                return max(0, min(100, round(rate, 1)))
            return 0
        elif self._key == "self_consumption_rate_month":
            # Calculate self consumption rate: (PV - Grid Export) / PV * 100
            pv = self.coordinator.data.get("pv_energy_month", 0)
            grid = self.coordinator.data.get("grid_energy_feed_in_month", 0)

            if pv and pv > 0:
                rate = ((pv - grid) / pv) * 100
                return max(0, min(100, round(rate, 1)))
            return 0

        return super().native_value
