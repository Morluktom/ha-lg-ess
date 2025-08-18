"""The LG ESS integration."""

from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinators.home import LgEssHomeDataUpdateCoordinator
from .coordinators.common import LgEssCommonDataUpdateCoordinator
from .coordinators.batt_settings import LgEssSettingsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.NUMBER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LG ESS from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize all coordinators
    home_coordinator = LgEssHomeDataUpdateCoordinator(hass, entry)
    common_coordinator = LgEssCommonDataUpdateCoordinator(hass, entry)
    settings_coordinator = LgEssSettingsDataUpdateCoordinator(hass, entry)

    coordinators = {
        "home_coordinator": home_coordinator,
        "common_coordinator": common_coordinator,
        "settings_coordinator": settings_coordinator,
    }

    # Setup all coordinators
    setup_errors = []

    for name, coordinator in coordinators.items():
        try:
            await coordinator.async_setup()
            _LOGGER.debug("Successfully setup %s", name)
        except Exception as err:
            _LOGGER.error("Failed to setup %s: %s", name, err)
            setup_errors.append(f"{name}: {err}")

    # Wenn alle Coordinatoren fehlschlagen, Setup abbrechen
    if len(setup_errors) == len(coordinators):
        _LOGGER.error("All coordinators failed to setup: %s", setup_errors)
        # Cleanup bereits initialisierte Coordinators
        for coordinator in coordinators.values():
            try:
                await coordinator.async_close()
            except Exception:
                pass
        return False

    # Erste Aktualisierung für alle erfolgreichen Coordinators
    refresh_errors = []

    for name, coordinator in coordinators.items():
        try:
            await coordinator.async_config_entry_first_refresh()
            _LOGGER.debug("Successfully refreshed %s", name)
        except Exception as err:
            _LOGGER.warning("Failed first refresh for %s: %s", name, err)
            refresh_errors.append(f"{name}: {err}")

    # Mindestens ein Coordinator muss erfolgreich sein
    successful_coordinators = len(coordinators) - len(refresh_errors)
    if successful_coordinators == 0:
        _LOGGER.error(
            "No coordinator could perform initial refresh: %s", refresh_errors
        )
        # Cleanup
        for coordinator in coordinators.values():
            try:
                await coordinator.async_close()
            except Exception:
                pass
        return False

    # Store coordinators in hass data
    hass.data[DOMAIN][entry.entry_id] = coordinators

    # Log successful setup
    _LOGGER.info(
        "LG ESS setup completed: %d/%d coordinators successful",
        successful_coordinators,
        len(coordinators),
    )

    # Set up all platforms
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception as err:
        _LOGGER.error("Failed to setup platforms: %s", err)
        # Cleanup coordinators
        for coordinator in coordinators.values():
            try:
                await coordinator.async_close()
            except Exception:
                pass
        hass.data[DOMAIN].pop(entry.entry_id, None)
        return False

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinators = hass.data[DOMAIN][entry.entry_id]

    # Unload all platforms first
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Close all coordinator sessions
    close_errors = []
    for name, coordinator in coordinators.items():
        try:
            await coordinator.async_close()
            _LOGGER.debug("Successfully closed %s", name)
        except Exception as err:
            _LOGGER.warning("Failed to close %s: %s", name, err)
            close_errors.append(f"{name}: {err}")

    if close_errors:
        _LOGGER.warning("Some coordinators failed to close cleanly: %s", close_errors)

    # Remove from hass data if unload was successful
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.info("LG ESS entry unloaded successfully")

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.info("Reloading LG ESS integration")

    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry format to new format."""
    _LOGGER.debug("Migrating LG ESS config entry from version %s", entry.version)

    if entry.version == 1:
        # Migration logic here if needed in the future
        # For now, just update version
        new_data = {**entry.data}
        new_options = {**entry.options}

        hass.config_entries.async_update_entry(
            entry, data=new_data, options=new_options, version=2
        )

        _LOGGER.info("Migrated LG ESS config entry to version 2")

    return True
