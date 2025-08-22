"""Binary sensors for LG ESS integration with multiple coordinators."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

from .coordinator import (
    LgEssHomeDataUpdateCoordinator,
    LgEssCommonDataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)


# Binary sensor entity definitions: (key, device_class, icon, translation_key)
BINARY_SENSOR_ENTITY_DEFINITIONS = [
    # Energy directions (from home coordinator)
    (
        "direction_is_direct_consuming",
        BinarySensorDeviceClass.POWER,
        "mdi:solar-power-variant",
        "direct_consuming",
    ),
    (
        "direction_is_battery_charging",
        BinarySensorDeviceClass.BATTERY_CHARGING,
        "mdi:battery-charging",
        "battery_charging",
    ),
    (
        "direction_is_battery_discharging",
        BinarySensorDeviceClass.BATTERY,
        "mdi:battery-minus",
        "battery_discharging",
    ),
    (
        "direction_is_grid_selling",
        BinarySensorDeviceClass.POWER,
        "mdi:transmission-tower-export",
        "grid_selling",
    ),
    (
        "direction_is_grid_buying",
        BinarySensorDeviceClass.POWER,
        "mdi:transmission-tower-import",
        "grid_buying",
    ),
    (
        "direction_is_charging_from_grid",
        BinarySensorDeviceClass.BATTERY_CHARGING,
        "mdi:battery-charging-outline",
        "charging_from_grid",
    ),
    # System status (from home coordinator)
    (
        "pv_generating",
        BinarySensorDeviceClass.POWER,
        "mdi:solar-panel",
        "pv_generating",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LG ESS binary sensor based on a config entry."""
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"]

    entities = []

    # Create binary sensor entities from definitions
    for (
        key,
        device_class,
        icon,
        translation_key,
    ) in BINARY_SENSOR_ENTITY_DEFINITIONS:
        coordinator = None
        for coord in coordinators.values():
            if key in coord.data:
                coordinator = coord
                break

        if coordinator:
            description = BinarySensorEntityDescription(
                key=key,
                device_class=device_class,
                icon=icon,
                translation_key=translation_key,
                has_entity_name=True,
            )
            entities.append(LgEssBinarySensor(coordinator, description, entry))
        else:
            _LOGGER.warning(
                "Coordinator not found for entity %s",
                key,
            )

    async_add_entities(entities, True)


class LgEssBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a LG ESS binary sensor."""

    def __init__(
        self,
        coordinator: LgEssHomeDataUpdateCoordinator | LgEssCommonDataUpdateCoordinator,
        description: BinarySensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return None

        data_key = self.entity_description.key

        # Special logic for calculated sensors
        if data_key == "system_online":
            # System is online when data is available
            return True

        elif data_key == "pv_generating":
            # PV generates when power > 0
            pv_power = self.coordinator.data.get("pv_total_power", 0)
            return pv_power > 0

        elif data_key == "winter_mode_active":
            # Winter mode from settings data
            winter_mode = self.coordinator.data.get("winter_mode", "off")
            return winter_mode == "on"

        elif data_key == "backup_mode_active":
            # Backup mode from settings data
            backup_mode = self.coordinator.data.get("backup_mode", "off")
            return backup_mode == "on"

        elif data_key == "auto_charge_active":
            # Auto charge from settings data
            auto_charge = self.coordinator.data.get("auto_charge", "off")
            return auto_charge == "on" or auto_charge == "1"

        # Standard: direct values from data (0/1 or True/False)
        raw_value = self.coordinator.data.get(data_key)

        if raw_value is None:
            return None

        # Convert different formats to bool
        if isinstance(raw_value, bool):
            return raw_value
        elif isinstance(raw_value, (int, float)):
            return raw_value > 0
        elif isinstance(raw_value, str):
            return raw_value.lower() in ("on", "true", "1", "yes", "active")

        return bool(raw_value)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return None

        # Additional attributes depending on sensor type
        attributes = {}

        return attributes if attributes else None
