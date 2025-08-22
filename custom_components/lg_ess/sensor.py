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

from .coordinator import (
    LgEssHomeDataUpdateCoordinator,
    LgEssCommonDataUpdateCoordinator,
    LgEssSlowUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)


# Sensor definitions: (sensor_key, unit, device_class, state_class, icon)
SENSOR_ENTITY_DEFINITIONS = [
    # Load sensors
    (
        "load_power",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:home",
    ),
    (
        "load_consumption_today",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:home",
    ),
    (
        "load_consumption_month",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:home",
    ),
    # Battery sensors
    (
        "bat_user_soc",
        PERCENTAGE,
        SensorDeviceClass.BATTERY,
        SensorStateClass.MEASUREMENT,
        "mdi:battery",
    ),
    (
        "bat_status",
        None,
        SensorDeviceClass.ENUM,
        None,
        "mdi:battery-heart",
    ),
    (
        "batt_directional",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:battery-charging-outline",
    ),
    (
        "bat_energy_charge_today",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-plus",
    ),
    (
        "bat_energy_discharge_today",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-minus",
    ),
    (
        "bat_energy_charge_month",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-plus",
    ),
    (
        "bat_energy_discharge_month",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-minus",
    ),
    # Battery detailed information from PMS/BMS
    (
        "battery_capacity",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY_STORAGE,
        None,
        "mdi:battery-high",
    ),
    (
        "battery_type",
        None,
        None,
        None,
        "mdi:information-outline",
    ),
    (
        "battery_install_date",
        None,
        None,
        None,
        "mdi:calendar",
    ),
    (
        "battery_nameplate_energy_1",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        None,
        "mdi:battery-outline",
    ),
    (
        "battery_cycle_count_1",
        None,
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:counter",
    ),
    (
        "battery_remaining_cap_1",
        "Ah",
        None,
        None,
        "mdi:battery-medium",
    ),
    (
        "battery_discharge_rate_1",
        PERCENTAGE,
        None,
        SensorStateClass.MEASUREMENT,
        "mdi:battery-arrow-down-outline",
    ),
    (
        "battery_charge_energy_1",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-plus-outline",
    ),
    (
        "battery_discharge_energy_1",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-minus-outline",
    ),
    (
        "battery_charge_cap_1",
        "Ah",
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-charging-80",
    ),
    (
        "battery_discharge_cap_1",
        "Ah",
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-arrow-down",
    ),
    (
        "battery_deep_discharge_count_1",
        None,
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-alert",
    ),
    (
        "battery_overcharge_count_1",
        None,
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-alert-variant",
    ),
    # Battery Unit 2 (if present)
    (
        "battery_nameplate_energy_2",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        None,
        "mdi:battery-outline",
    ),
    (
        "battery_cycle_count_2",
        None,
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:counter",
    ),
    (
        "battery_remaining_cap_2",
        "Ah",
        None,
        None,
        "mdi:battery-medium",
    ),
    (
        "battery_discharge_rate_2",
        PERCENTAGE,
        None,
        SensorStateClass.MEASUREMENT,
        "mdi:battery-arrow-down-outline",
    ),
    (
        "battery_charge_energy_2",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-plus-outline",
    ),
    (
        "battery_discharge_energy_2",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-minus-outline",
    ),
    (
        "battery_charge_cap_2",
        "Ah",
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-charging-80",
    ),
    (
        "battery_discharge_cap_2",
        "Ah",
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-arrow-down",
    ),
    (
        "battery_deep_discharge_count_2",
        None,
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-alert",
    ),
    (
        "battery_overcharge_count_2",
        None,
        None,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:battery-alert-variant",
    ),
    # Battery Serial Numbers and Pack Dates
    (
        "battery_a_serials",
        None,
        None,
        None,
        "mdi:identifier",
    ),
    (
        "battery_b_serials",
        None,
        None,
        None,
        "mdi:identifier",
    ),
    (
        "battery_a_pack_dates",
        None,
        None,
        None,
        "mdi:calendar-range",
    ),
    (
        "battery_b_pack_dates",
        None,
        None,
        None,
        "mdi:calendar-range",
    ),
    # Grid sensors
    (
        "grid_directional",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:transmission-tower",
    ),
    (
        "grid_frequency",
        UnitOfFrequency.HERTZ,
        SensorDeviceClass.FREQUENCY,
        SensorStateClass.MEASUREMENT,
        "mdi:sine-wave",
    ),
    (
        "grid_voltage",
        UnitOfElectricPotential.VOLT,
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
        "mdi:flash",
    ),
    (
        "grid_energy_feed_in_today",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:transmission-tower-export",
    ),
    (
        "grid_energy_feed_in_month",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:transmission-tower-export",
    ),
    (
        "grid_energy_purchase_today",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:transmission-tower-import",
    ),
    (
        "grid_energy_purchase_month",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:transmission-tower-import",
    ),
    # PV sensors
    (
        "pv1_voltage",
        UnitOfElectricPotential.VOLT,
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
        "mdi:flash",
    ),
    (
        "pv2_voltage",
        UnitOfElectricPotential.VOLT,
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
        "mdi:flash",
    ),
    (
        "pv3_voltage",
        UnitOfElectricPotential.VOLT,
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
        "mdi:flash",
    ),
    (
        "pv1_current",
        UnitOfElectricCurrent.AMPERE,
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
        "mdi:current-dc",
    ),
    (
        "pv2_current",
        UnitOfElectricCurrent.AMPERE,
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
        "mdi:current-dc",
    ),
    (
        "pv3_current",
        UnitOfElectricCurrent.AMPERE,
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
        "mdi:current-dc",
    ),
    (
        "pv1_power",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:solar-panel",
    ),
    (
        "pv2_power",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:solar-panel",
    ),
    (
        "pv3_power",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:solar-panel",
    ),
    (
        "pv_capacity",
        "kWp",
        None,
        None,
        "mdi:solar-panel",
    ),
    (
        "pv_energy_today",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:solar-panel",
    ),
    (
        "pv_energy_month",
        UnitOfEnergy.KILO_WATT_HOUR,
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "mdi:solar-panel",
    ),
    (
        "pv_total_power",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:solar-panel",
    ),
    # PMS System Information
    (
        "pms_model",
        None,
        None,
        None,
        "mdi:information-outline",
    ),
    (
        "pms_serialno",
        None,
        None,
        None,
        "mdi:barcode",
    ),
    (
        "pms_ac_input_power",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        None,
        "mdi:power-plug",
    ),
    (
        "pms_ac_output_power",
        UnitOfPower.KILO_WATT,
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        "mdi:power-socket-eu",
    ),
    (
        "pms_install_date",
        None,
        None,
        None,
        "mdi:calendar-check",
    ),
    # Version Information
    (
        "pms_version",
        None,
        None,
        None,
        "mdi:package-variant",
    ),
    (
        "pms_build_date",
        None,
        None,
        None,
        "mdi:clock-outline",
    ),
    (
        "pcs_version",
        None,
        None,
        None,
        "mdi:package-variant-closed",
    ),
    (
        "bms_version",
        None,
        None,
        None,
        "mdi:chip",
    ),
    (
        "bms_unit1_version",
        None,
        None,
        None,
        "mdi:chip",
    ),
    (
        "bms_unit2_version",
        None,
        None,
        None,
        "mdi:chip",
    ),
    # Status and operational sensors
    ("operation_mode", None, None, None, "mdi:cog"),
    (
        "self_consumption_rate",
        PERCENTAGE,
        None,
        SensorStateClass.MEASUREMENT,
        "mdi:percent",
    ),
    # Calculated sensors
    (
        "self_consumption_rate_month",
        PERCENTAGE,
        None,
        SensorStateClass.MEASUREMENT,
        "mdi:percent",
    ),
    (
        "grid_independence_rate",
        PERCENTAGE,
        None,
        SensorStateClass.MEASUREMENT,
        "mdi:home-battery",
    ),
    (
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
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"]

    entities = []

    # Create regular sensors from entity definitions
    for (
        sensor_key,
        unit,
        device_class,
        state_class,
        icon,
    ) in SENSOR_ENTITY_DEFINITIONS:
        coordinator = None
        for coord in coordinators.values():
            if sensor_key in coord.data:
                coordinator = coord
                break

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
        else:
            _LOGGER.warning(
                "Coordinator not found for entity %s",
                sensor_key,
            )

    async_add_entities(entities)


class LgEssSensor(CoordinatorEntity, SensorEntity):
    """Base LG ESS sensor."""

    def __init__(
        self,
        coordinator: LgEssHomeDataUpdateCoordinator
        | LgEssCommonDataUpdateCoordinator
        | LgEssSlowUpdateCoordinator,
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

        return self.coordinator.data.get(self._key)

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
