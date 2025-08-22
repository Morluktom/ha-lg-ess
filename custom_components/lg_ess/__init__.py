"""The LG ESS integration."""

from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry

from .const import DOMAIN, KEYS_ALWAYS_DISABLE, KEYS_BATTERY_1, KEYS_BATTERY_2
from .coordinator import (
    LgEssHomeDataUpdateCoordinator,
    LgEssCommonDataUpdateCoordinator,
    LgEssSlowUpdateCoordinator,
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
    system_info_coordinator = LgEssSlowUpdateCoordinator(hass, lgEss, entry)

    coordinators = {
        "home_coordinator": home_coordinator,
        "common_coordinator": common_coordinator,
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

    # Disable useless Entrys
    await async_disable_useless_entries(hass, entry)

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


async def async_disable_useless_entries(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Disable useless entries."""
    # Check if we have already deactivated
    if not entry.data.get("entities_disabled", False):
        coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"]

        for coordinator in coordinators.values():
            # Check if battery 1 is present
            if "battery_nameplate_energy_1" in coordinator.data:
                value = coordinator.safe_number_convert(
                    coordinator.data["battery_nameplate_energy_1"]
                )
                batt1present = value > 0

            # Check if battery 2 is present
            if "battery_nameplate_energy_2" in coordinator.data:
                value = coordinator.safe_number_convert(
                    coordinator.data["battery_nameplate_energy_2"]
                )
                batt2present = value > 0

        # List of all sensors
        unique_ids = await list_sensor_unique_ids(hass, DOMAIN)

        unique_ids_to_disable = []
        unique_ids_to_disable.extend(KEYS_ALWAYS_DISABLE)

        if not batt1present:
            unique_ids_to_disable.extend(KEYS_BATTERY_1)

        if not batt2present:
            unique_ids_to_disable.extend(KEYS_BATTERY_2)

        for unique_id_to_disable in unique_ids_to_disable:
            for unique_id in unique_ids:
                if unique_id_to_disable in unique_id:
                    await async_disable_entity_by_unique_id(hass, unique_id, DOMAIN)
                    break

        # FSet a flag so we don't do this every time
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, "entities_disabled": True}
        )


async def async_disable_entity_by_unique_id(
    hass: HomeAssistant, unique_id: str, platform: str
):
    """Disables an entity based on its unique_id (and platform), if it exists."""
    registry = entity_registry.async_get(hass)

    for entry in registry.entities.values():
        if entry.platform == platform and entry.unique_id == unique_id:
            if entry.disabled:
                _LOGGER.debug(
                    "Entity %s (%s) is already disabled.", entry.entity_id, unique_id
                )
                return

            registry.async_update_entity(
                entry.entity_id,
                disabled_by=entity_registry.RegistryEntryDisabler.USER,
            )
            _LOGGER.info(
                "Entity %s (%s) has been disabled.", entry.entity_id, unique_id
            )
            return

    _LOGGER.debug(
        "No entity with unique_id %s found on platform %s.", unique_id, platform
    )


async def list_sensor_unique_ids(hass: HomeAssistant, domain: str) -> list:
    """List all sensor of this domain."""
    registry = entity_registry.async_get(hass)

    sensors = []

    for entity_id, entry in registry.entities.items():
        if (entry.platform == domain) and (
            entity_id.startswith(
                ("sensor.", "binary_sensor.", "switch", "number", "select")
            )
        ):
            sensors.append(entry.unique_id)

    return sensors
