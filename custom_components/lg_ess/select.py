"""Select entities for LG ESS integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

from .coordinator import (
    LgEssHomeDataUpdateCoordinator,
    LgEssCommonDataUpdateCoordinator,
    LgEssSettingsDataUpdateCoordinator,
    LgEssSystemInfoDataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)


# Select entity definitions: (key, icon, options)
SELECT_ENTITY_DEFINITIONS = [
    (
        "charging_mode",
        "mdi:battery-charging",
        ["fast_charge", "battery_care", "weather_forecast"],
    ),
    # Add more select entities here as needed
    # ("home_coordinator", "operation_mode", "mdi:cog", "operation_mode", ["normal", "eco", "backup"]),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LG ESS select entities based on a config entry."""
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"]

    entities = []

    # Create select entities from definitions
    for (
        key,
        icon,
        options,
    ) in SELECT_ENTITY_DEFINITIONS:
        coordinator = None
        for coordstr in coordinators:
            coord = coordinators.get(coordstr)
            if key in coord.data:
                coordinator = coord
                break

        if coordinator:
            description = SelectEntityDescription(
                key=key,
                icon=icon,
                translation_key=key,
                options=options,
            )
            entities.append(LgEssSelect(coordinator, description, entry))
        else:
            _LOGGER.warning(
                "Coordinator not found for entity %s",
                key,
            )

    async_add_entities(entities, True)


class LgEssSelect(CoordinatorEntity, SelectEntity):
    """Representation of a LG ESS select entity."""

    def __init__(
        self,
        coordinator: LgEssHomeDataUpdateCoordinator
        | LgEssCommonDataUpdateCoordinator
        | LgEssSettingsDataUpdateCoordinator,
        description: SelectEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info
        self._attr_options = description.options
        self._attr_translation_key = description.translation_key
        self._attr_has_entity_name = True

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if not self.coordinator.data:
            return None

        data_key = self.entity_description.key

        # Fallback: read directly from data
        raw_value = self.coordinator.data.get(data_key)
        if raw_value in self.options:
            return raw_value

        # Default: first option
        return self.options[0] if self.options else None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in self.options:
            raise ServiceValidationError(
                f"Invalid option '{option}'. Valid options: {self.options}"
            )

        data_key = self.entity_description.key

        try:
            # Route to the corresponding coordinator methods
            if data_key == "charging_mode":
                await self.coordinator.async_set_charging_mode(option)
            else:
                _LOGGER.warning("No handler for select option: %s", data_key)
                raise ServiceValidationError(f"Option '{data_key}' not implemented")

        except Exception as err:
            _LOGGER.error("Failed to set %s to %s: %s", data_key, option, err)
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
        # data_key = self.entity_description.key

        # Add context-specific attributes
        # if data_key == "charging_mode":
        #     attributes.update(
        #         {
        #             "is_charging": self.coordinator.data.get(
        #                 "direction_is_battery_charging", 0
        #             ),
        #             "charging_from_grid": self.coordinator.data.get(
        #                 "direction_is_charging_from_grid", 0
        #             ),
        #            "pv_power": self.coordinator.data.get("pv_total_power", 0),
        #        }
        #     )

        return attributes if attributes else None
