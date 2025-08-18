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

from .const import DOMAIN

from .coordinators.home import LgEssHomeDataUpdateCoordinator
from .coordinators.common import LgEssCommonDataUpdateCoordinator
from .coordinators.batt_settings import LgEssSettingsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


# Switch entity definitions: (coordinator_key, class_name, key, device_class, icon, data_key)
SWITCH_ENTITY_DEFINITIONS = [
    (
        "home_coordinator",
        "LgEssOperationModeSwitch",
        "operation_mode",
        SwitchDeviceClass.SWITCH,
        "mdi:power",
        "operation_status",
    ),
    (
        "settings_coordinator",
        "LgEssWinterModeSwitch",
        "winter_mode",
        SwitchDeviceClass.SWITCH,
        "mdi:snowflake",
        "winter_status",
    ),
    (
        "settings_coordinator",
        "LgEssBackupModeSwitch",
        "backup_mode",
        SwitchDeviceClass.SWITCH,
        "mdi:battery-40",
        "backup_status",
    ),
    (
        "settings_coordinator",
        "LgEssChargeFromGridSwitch",
        "auto_charge",
        SwitchDeviceClass.SWITCH,
        "mdi:battery-charging-30",
        "auto_charge_status",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the LG ESS switch platform."""
    coordinators = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Create switch entities from definitions
    for (
        coordinator_key,
        class_name,
        key,
        device_class,
        icon,
        data_key,
    ) in SWITCH_ENTITY_DEFINITIONS:
        coordinator = coordinators.get(coordinator_key)
        if coordinator:
            # Dynamically create the correct switch class
            if class_name == "LgEssOperationModeSwitch":
                entities.append(
                    LgEssOperationModeSwitch(
                        coordinator, entry, key, device_class, icon, data_key
                    )
                )
            elif class_name == "LgEssWinterModeSwitch":
                entities.append(
                    LgEssWinterModeSwitch(
                        coordinator, entry, key, device_class, icon, data_key
                    )
                )
            elif class_name == "LgEssBackupModeSwitch":
                entities.append(
                    LgEssBackupModeSwitch(
                        coordinator, entry, key, device_class, icon, data_key
                    )
                )
            elif class_name == "LgEssChargeFromGridSwitch":
                entities.append(
                    LgEssChargeFromGridSwitch(
                        coordinator, entry, key, device_class, icon, data_key
                    )
                )
            else:
                _LOGGER.warning("Unknown switch class: %s", class_name)
        else:
            _LOGGER.warning(
                "Coordinator %s not found for entity %s",
                coordinator_key,
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
        data_key: str | None = None,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._key = key
        self._data_key = data_key or key
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
            await self._async_turn_off()
            await asyncio.sleep(0.5)
            await self.coordinator.async_request_refresh()
            self._optimistic_state = None
        except Exception as err:
            self._optimistic_state = None
            _LOGGER.error("Failed to turn off %s: %s", self.name, err)

    async def _async_turn_on(self) -> None:
        """Turn the switch on - to be implemented by subclasses."""
        raise NotImplementedError

    async def _async_turn_off(self) -> None:
        """Turn the switch off - to be implemented by subclasses."""
        raise NotImplementedError


class LgEssOperationModeSwitch(LgEssSwitch):
    """Switch to control LG ESS operation mode (Normal/Emergency)."""

    def __init__(
        self,
        coordinator: LgEssHomeDataUpdateCoordinator
        | LgEssCommonDataUpdateCoordinator
        | LgEssSettingsDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
        device_class: SwitchDeviceClass,
        icon: str,
        data_key: str,
    ) -> None:
        """Initialize the operation mode switch."""
        super().__init__(coordinator, entry, key, device_class, icon, data_key)

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        if self.coordinator.data is None:
            return None

        # Check if system is in normal operation mode (not emergency/maintenance)
        operation_status = self.coordinator.data.get(self._data_key)
        return operation_status == "start" if operation_status else None

    async def _async_turn_on(self) -> None:
        """Set operation mode to normal."""
        await self.coordinator.async_set_operation_mode("start")

    async def _async_turn_off(self) -> None:
        """Set operation mode to standby."""
        await self.coordinator.async_set_operation_mode("stop")


class LgEssWinterModeSwitch(LgEssSwitch):
    """Switch to control LG ESS winter mode."""

    def __init__(
        self,
        coordinator: LgEssHomeDataUpdateCoordinator
        | LgEssCommonDataUpdateCoordinator
        | LgEssSettingsDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
        device_class: SwitchDeviceClass,
        icon: str,
        data_key: str,
    ) -> None:
        """Initialize the winter mode switch."""
        super().__init__(coordinator, entry, key, device_class, icon, data_key)

    @property
    def is_on(self) -> bool | None:
        """Return true if winter mode is enabled."""
        if self.coordinator.data is None:
            return None

        # Optimistic state
        if self._optimistic_state is not None:
            return self._optimistic_state

        # Get status
        winter_mode = self.coordinator.data.get(self._data_key)

        if winter_mode is None:
            return None

        # Support different formats
        if isinstance(winter_mode, str):
            return winter_mode.lower() in ("on", "true", "1", "enabled")
        else:
            return bool(winter_mode)

    async def _async_turn_on(self) -> None:
        """Enable winter mode."""
        await self.coordinator.async_set_winter_mode(True)

    async def _async_turn_off(self) -> None:
        """Disable winter mode."""
        await self.coordinator.async_set_winter_mode(False)


class LgEssBackupModeSwitch(LgEssSwitch):
    """Switch to control LG ESS backup mode."""

    def __init__(
        self,
        coordinator: LgEssHomeDataUpdateCoordinator
        | LgEssCommonDataUpdateCoordinator
        | LgEssSettingsDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
        device_class: SwitchDeviceClass,
        icon: str,
        data_key: str,
    ) -> None:
        """Initialize the backup mode switch."""
        super().__init__(coordinator, entry, key, device_class, icon, data_key)

    @property
    def is_on(self) -> bool | None:
        """Return true if backup mode is enabled."""
        if self.coordinator.data is None:
            return None

        # Check various possible keys
        backup_mode = self.coordinator.data.get(self._data_key)

        if backup_mode is None:
            return None

        # Support different formats
        if isinstance(backup_mode, str):
            return backup_mode.lower() in ("on", "true", "1", "enabled")
        else:
            return bool(backup_mode)

    async def _async_turn_on(self) -> None:
        """Enable backup mode."""
        await self.coordinator.async_set_backup_mode(True)

    async def _async_turn_off(self) -> None:
        """Disable backup mode."""
        await self.coordinator.async_set_backup_mode(False)


class LgEssChargeFromGridSwitch(LgEssSwitch):
    """Switch to control LG ESS charge from grid."""

    def __init__(
        self,
        coordinator: LgEssHomeDataUpdateCoordinator
        | LgEssCommonDataUpdateCoordinator
        | LgEssSettingsDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
        device_class: SwitchDeviceClass,
        icon: str,
        data_key: str,
    ) -> None:
        """Initialize the charge from grid switch."""
        super().__init__(coordinator, entry, key, device_class, icon, data_key)

    @property
    def is_on(self) -> bool | None:
        """Return true if charge from grid is enabled."""
        if self.coordinator.data is None:
            return None

        # Check various possible keys
        auto_charge = self.coordinator.data.get(self._data_key)

        if auto_charge is None:
            return None

        # Support different formats
        if isinstance(auto_charge, str):
            return auto_charge.lower() in ("on", "true", "1", "enabled")
        else:
            return bool(auto_charge)

    async def _async_turn_on(self) -> None:
        """Enable charge from grid."""
        await self.coordinator.async_set_charge_from_grid(True)

    async def _async_turn_off(self) -> None:
        """Disable charge from grid."""
        await self.coordinator.async_set_charge_from_grid(False)
