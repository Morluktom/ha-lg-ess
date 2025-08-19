"""The LG ESS integration."""

from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import (
    LgEssHomeDataUpdateCoordinator,
    LgEssCommonDataUpdateCoordinator,
    LgEssSettingsDataUpdateCoordinator,
    LgEssSystemInfoDataUpdateCoordinator,
)
from .lg_ess import (
    LgEss,
    LgEssAuthException,
    LgEssException,
)

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

    try:
        lgEss = await LgEss.create(None, entry.data["password"], entry.data["host"])
    except LgEssException as e:
        _LOGGER.exception("Error setting up ESS api")
        raise ConfigEntryNotReady from e

    # Initialize all coordinators
    home_coordinator = LgEssHomeDataUpdateCoordinator(hass, lgEss, entry)
    common_coordinator = LgEssCommonDataUpdateCoordinator(hass, lgEss, entry)
    settings_coordinator = LgEssSettingsDataUpdateCoordinator(hass, lgEss, entry)
    system_info_coordinator = LgEssSystemInfoDataUpdateCoordinator(hass, lgEss, entry)

    coordinators = {
        "home_coordinator": home_coordinator,
        "common_coordinator": common_coordinator,
        "settings_coordinator": settings_coordinator,
        "system_info_coordinator": system_info_coordinator,
    }

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
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinators": coordinators,
        "lgEss": lgEss,
    }

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
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"]
    api = hass.data[DOMAIN][entry.entry_id]["lgEss"]

    # Unload all platforms first
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await api.destruct()

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
