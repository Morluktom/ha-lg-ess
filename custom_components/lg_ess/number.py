"""Number entities for LG ESS integration."""

from __future__ import annotations

import logging
from typing import Any

import asyncio

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

from .lg_ess import (
    LgEss,
    LgEssAuthException,
    LgEssException,
)

from .coordinator import (
    LgEssHomeDataUpdateCoordinator,
    LgEssCommonDataUpdateCoordinator,
    LgEssSettingsDataUpdateCoordinator,
    LgEssSystemInfoDataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)


# Number entity definitions: (coordinator_key, key, icon, translation_key, unit, min_value, max_value, step, mode)
NUMBER_ENTITY_DEFINITIONS = [
    (
        "settings_coordinator",
        "backup_soc",
        "mdi:battery-heart-variant",
        "backup_soc",
        PERCENTAGE,
        0,
        100,
        5,
        NumberMode.BOX,
    ),
    # Add more number entities here as needed
    # ("settings_coordinator", "winter_temp_threshold", "mdi:thermometer", "winter_temp_threshold", "°C", -20, 20, 1, NumberMode.BOX),
    # ("settings_coordinator", "charge_time_start", "mdi:clock-start", "charge_time_start", None, 0, 23, 1, NumberMode.BOX),
    # ("settings_coordinator", "charge_time_end", "mdi:clock-end", "charge_time_end", None, 0, 23, 1, NumberMode.BOX),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LG ESS number entities based on a config entry."""
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"]

    entities = []

    # Create number entities from definitions
    for (
        coordinator_key,
        key,
        icon,
        translation_key,
        unit,
        min_value,
        max_value,
        step,
        mode,
    ) in NUMBER_ENTITY_DEFINITIONS:
        coordinator = coordinators.get(coordinator_key)
        if coordinator:
            description = NumberEntityDescription(
                key=key,
                icon=icon,
                translation_key=translation_key,
                native_unit_of_measurement=unit,
                native_min_value=min_value,
                native_max_value=max_value,
                native_step=step,
                mode=mode,
            )
            entities.append(LgEssNumber(coordinator, description, entry))
        else:
            _LOGGER.warning(
                "Coordinator %s not found for entity %s",
                coordinator_key,
                key,
            )

    async_add_entities(entities, True)


class LgEssNumber(CoordinatorEntity, NumberEntity):
    """Representation of a LG ESS number entity."""

    def __init__(
        self,
        coordinator: LgEssHomeDataUpdateCoordinator
        | LgEssCommonDataUpdateCoordinator
        | LgEssSettingsDataUpdateCoordinator,
        description: NumberEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info
        self._attr_translation_key = description.translation_key
        self._attr_has_entity_name = True

        # Optimistic updates for better UI responsiveness
        self._optimistic_value = None

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        # Optimistic value takes precedence
        if self._optimistic_value is not None:
            return self._optimistic_value

        if not self.coordinator.data:
            return None

        data_key = self.entity_description.key

        # Mapping of different number types to data sources
        if data_key == "backup_soc":
            # Backup reserve SOC
            return self.coordinator.data.get("backup_soc", 0)

        # Fallback: read directly from data
        raw_value = self.coordinator.data.get(data_key)
        if raw_value is not None:
            try:
                return float(raw_value)
            except (ValueError, TypeError):
                pass

        # Default: minimum value
        return self.native_min_value

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        if not self.native_min_value <= value <= self.native_max_value:
            raise ServiceValidationError(
                f"Value {value} is out of range ({self.native_min_value}-{self.native_max_value})"
            )

        data_key = self.entity_description.key

        try:
            # Optimistic update for immediate UI change
            self._optimistic_value = value
            self.async_write_ha_state()

            # Route to corresponding coordinator methods
            if data_key == "backup_soc":
                await self.coordinator.async_set_backup_soc(int(value))
            else:
                _LOGGER.warning("No handler for number setting: %s", data_key)
                raise ServiceValidationError(f"Setting '{data_key}' not implemented")

            # Reset optimistic value after successful API call
            self._optimistic_value = None

            # Refresh after short delay
            await asyncio.sleep(0.5)
            await self.coordinator.async_request_refresh()

        except Exception as err:
            # Reset optimistic value on error
            self._optimistic_value = None
            self.async_write_ha_state()
            _LOGGER.error("Failed to set %s to %s: %s", data_key, value, err)
            raise ServiceValidationError(f"Failed to set {data_key}: {err}") from err

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

        attributes = {}
        data_key = self.entity_description.key

        # Add context-specific attributes
        if data_key.startswith("battery_"):
            attributes.update(
                {
                    "current_soc": self.coordinator.data.get("bat_user_soc", 0),
                    "battery_power": self.coordinator.data.get("bat_dc_power", 0),
                }
            )

        elif data_key.startswith("grid_"):
            attributes.update(
                {
                    "grid_power": self.coordinator.data.get("grid_power", 0),
                    "grid_voltage": self.coordinator.data.get("grid_voltage", 0),
                    "grid_frequency": self.coordinator.data.get("grid_frequency", 0),
                }
            )

        elif "time" in data_key:
            # For time settings: add current time
            from datetime import datetime

            attributes["current_time"] = datetime.now().strftime("%H:%M")

        elif data_key == "winter_temp_threshold":
            attributes.update(
                {
                    "winter_mode_active": self.coordinator.data.get(
                        "winter_mode", "off"
                    ),
                    "battery_winter_status": self.coordinator.data.get(
                        "battery_winter_status", "off"
                    ),
                }
            )

        return attributes if attributes else None
