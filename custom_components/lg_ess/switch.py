"""Switch platform for LG ESS integration."""

from __future__ import annotations

import logging
from typing import Any

import asyncio

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN

from .coordinator import (
    LgEssHomeDataUpdateCoordinator,
    LgEssCommonDataUpdateCoordinator,
    LgEssSettingsDataUpdateCoordinator,
    LgEssSystemInfoDataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)


# Switch entity definitions: (coordinator_key, class_name, key, device_class, icon, data_key)
SWITCH_ENTITY_DEFINITIONS = [
    (
        "operation_mode",
        SwitchDeviceClass.SWITCH,
        "mdi:power",
    ),
    (
        "winter_mode",
        SwitchDeviceClass.SWITCH,
        "mdi:snowflake",
    ),
    (
        "backup_mode",
        SwitchDeviceClass.SWITCH,
        "mdi:battery-40",
    ),
    (
        "auto_charge",
        SwitchDeviceClass.SWITCH,
        "mdi:battery-charging-30",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the LG ESS switch platform."""
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"]

    entities = []

    # Create switch entities from definitions
    for (
        key,
        device_class,
        icon,
    ) in SWITCH_ENTITY_DEFINITIONS:
        coordinator = None
        for coord in coordinators.values():
            if key in coord.data:
                coordinator = coord
                break

        if coordinator:
            entities.append(LgEssSwitch(coordinator, entry, key, device_class, icon))

        else:
            _LOGGER.warning(
                "Coordinator not found for entity %s",
                key,
            )

    async_add_entities(entities)


class LgEssSwitch(CoordinatorEntity, SwitchEntity):
    """Base class for LG ESS switches."""

    def __init__(
        self,
        coordinator: LgEssHomeDataUpdateCoordinator
        | LgEssCommonDataUpdateCoordinator
        | LgEssSettingsDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
        device_class: SwitchDeviceClass | None = None,
        icon: str | None = None,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._key = key
        self._data_key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_class = device_class
        self._attr_device_info = coordinator.device_info
        self._attr_has_entity_name = True
        self._attr_translation_key = key
        self._optimistic_state = None
        if icon:
            self._attr_icon = icon

    @property
    def available(self) -> bool:
        """Return if entity is available."""

        return self.coordinator.last_update_success

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            self._optimistic_state = True
            # UI sofort aktualisieren
            self.async_write_ha_state()

            await self._async_turn_on()
            await asyncio.sleep(0.5)
            await self.coordinator.async_request_refresh()
            self._optimistic_state = None
        except Exception as err:
            self._optimistic_state = None
            _LOGGER.error("Failed to turn on %s: %s", self.name, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            self._optimistic_state = False
            # UI sofort aktualisieren
            self.async_write_ha_state()
            await self._async_turn_off()
            await asyncio.sleep(0.5)
            await self.coordinator.async_request_refresh()
            self._optimistic_state = None
        except Exception as err:
            self._optimistic_state = None
            _LOGGER.error("Failed to turn off %s: %s", self.name, err)

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is enabled."""
        if self.coordinator.data is None:
            return None

        # Optimistic state
        if self._optimistic_state is not None:
            return self._optimistic_state

        # Get status
        state = self.coordinator.data.get(self._data_key)

        if state is None:
            return None

        # Support different formats
        if isinstance(state, str):
            return state.lower() in ("on", "true", "1", "enabled", "start")
        else:
            return bool(state)

    async def _async_turn_on(self) -> None:
        """Switch on function."""

        data_key = self._data_key
        if data_key == "operation_mode":
            await self.coordinator.async_set_operation_mode("start")
        elif data_key == "winter_mode":
            await self.coordinator.async_set_winter_mode(True)
        elif data_key == "backup_mode":
            await self.coordinator.async_set_backup_mode(True)
        elif data_key == "auto_charge":
            await self.coordinator.async_set_charge_from_grid(True)

    async def _async_turn_off(self) -> None:
        """Switch off function."""

        data_key = self._data_key
        if data_key == "operation_mode":
            await self.coordinator.async_set_operation_mode("stop")
        elif data_key == "winter_mode":
            await self.coordinator.async_set_winter_mode(False)
        elif data_key == "backup_mode":
            await self.coordinator.async_set_backup_mode(False)
        elif data_key == "auto_charge":
            await self.coordinator.async_set_charge_from_grid(False)
