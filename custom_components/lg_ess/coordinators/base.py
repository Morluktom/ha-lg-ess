"""Base DataUpdateCoordinator for LG ESS integration."""

from __future__ import annotations

import asyncio
import logging
import json
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
)

_LOGGER = logging.getLogger(__name__)


class LgEssBaseCoordinator(DataUpdateCoordinator):
    """Base class for LG ESS coordinators with shared functionality."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger,
        name: str,
        update_interval: timedelta,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        self.hass = hass
        self.entry = config_entry
        self._host = config_entry.data[CONF_HOST]
        self._password = config_entry.data[CONF_PASSWORD]
        self._session = None
        self._auth_key = None

        # Device info for all entities
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name="LG ESS",
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=None,
            configuration_url=f"https://{self._host}",
        )

        super().__init__(
            hass,
            logger,
            name=name,
            update_interval=update_interval,
            config_entry=config_entry,
        )

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            # Create aiohttp session
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(
                connect=10, sock_read=10, sock_connect=10, total=30
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"Content-Type": "application/json", "Charset": "UTF-8"},
            )

            # Login to LG ESS
            await self._login()

            _LOGGER.info("Successfully connected to LG ESS at %s", self._host)

        except Exception as err:
            if self._session:
                await self._session.close()
            _LOGGER.error("Failed to setup LG ESS coordinator: %s", err)
            raise err

    async def _login(self) -> None:
        """Authenticate with the LG ESS system."""
        try:
            login_url = f"https://{self._host}/v1/user/setting/login"
            login_data = {"password": self._password}

            async with self._session.put(login_url, json=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("status") == "success":
                        self._auth_key = result.get("auth_key")
                        _LOGGER.debug("Authentication successful")
                    else:
                        raise Exception(f"Login failed: {result}")
                else:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")

        except Exception as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise err

    async def _make_request(
        self, endpoint: str, method: str = "POST", data: dict = None
    ) -> dict:
        """Make authenticated request to LG ESS API."""
        if not self._session:
            await self.async_setup()

        if not self._auth_key:
            await self._login()

        url = f"https://{self._host}/v1{endpoint}"

        headers = {"Content_Type": "application/json"}

        if self._auth_key:
            content = {"auth_key": self._auth_key}

        if data:
            content.update(data)

        try:
            if method == "POST":
                async with self._session.post(url, json=content) as response:
                    if (response.status == 401) or (
                        response.status == 405
                    ):  # Unauthorized, re-authenticate
                        await self._login()
                        async with self._session.post(
                            url, json=content
                        ) as retry_response:
                            return await retry_response.json()

                    elif response.status == 200:
                        return await response.json()
                    else:
                        _LOGGER.warning(
                            "Request failed: HTTP %s for %s", response.status, endpoint
                        )
                        self._auth_key = None
                        return None

            elif method == "PUT":
                async with self._session.put(
                    url, headers=headers, json=content
                ) as response:
                    if (response.status == 401) or (
                        response.status == 405
                    ):  # Unauthorized, re-authenticate
                        await self._login()
                        async with self._session.put(
                            url, headers=headers, json=content
                        ) as retry_response:
                            return await retry_response.json()
                    elif response.status == 200:
                        return await response.json()
                    else:
                        _LOGGER.warning(
                            "Request failed: HTTP %s for %s", response.status, endpoint
                        )
                        self._auth_key = None
                        return None

        except Exception as err:
            _LOGGER.error("Request to %s failed: %s", endpoint, err)
            return None

    def safe_number_convert(self, value):
        """Konvertiert einen Wert sicher zu einer Zahl."""
        # Bereits eine Zahl?
        if isinstance(value, (int, float)):
            return value

        # Versuche String zu Zahl zu konvertieren
        if isinstance(value, str):
            try:
                # Erst versuchen als int
                if "." not in value:
                    return int(value)
                else:
                    return float(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def safe_bool(value):
        """Safely convert value to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value > 0
        if isinstance(value, str):
            return value.lower() in ("true", "1", "on", "yes")
        return False

    async def async_close(self) -> None:
        """Close the session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def async_unload(self) -> None:
        """Unload the coordinator."""
        await self.async_close()

    # Update methods using direct API calls
    async def async_get_setting_battery(self) -> dict:
        """Update settings data via direct HTTP API calls."""

        setting_bat = await self._make_request("/user/setting/batt")

        if not setting_bat:
            # Keep previous data instead of returning None
            return self.data or {}

        _LOGGER.debug("/user/setting/batt: %s", json.dumps(setting_bat))

        return setting_bat

    async def async_get_common_data(self) -> dict:
        """Update common data via direct HTTP API calls."""

        common_data = await self._make_request("/user/essinfo/common")

        if not common_data:
            # Keep previous data instead of returning None
            return self.data or {}

        _LOGGER.debug("/user/essinfo/common: %s", json.dumps(common_data))

        return common_data

    async def async_get_home_data(self) -> dict:
        """Update home data via direct HTTP API calls."""

        home_data = await self._make_request("/user/essinfo/home")
        if not home_data:
            # Keep previous data instead of returning None
            return self.data or {}

        _LOGGER.debug("/user/essinfo/home: %s", json.dumps(home_data))

        return home_data

    async def async_get_system_info(self) -> dict:
        """Update system info via direct HTTP API calls."""

        system_info = await self._make_request("/user/setting/systeminfo")

        if not system_info:
            # Keep previous data instead of returning None
            return self.data or {}

        _LOGGER.debug("/user/setting/systeminfo: %s", json.dumps(system_info))

        return system_info

    async def async_get_setting_network(self) -> dict:
        """Update network info via direct HTTP API calls."""

        network_info = await self._make_request("/user/setting/network")
        if not network_info:
            # Keep previous data instead of returning None
            return self.data or {}

        _LOGGER.debug("/user/setting/network: %s", json.dumps(network_info))

        return network_info

    # Control methods using direct API calls _get_home_data_get_home_data
    async def async_set_winter_mode(self, enabled: bool) -> None:
        """Set winter mode."""
        try:
            endpoint = "/user/setting/batt"
            data_payload = {"wintermode": "on" if enabled else "off"}
            result = await self._make_request(endpoint, "PUT", data_payload)
            if result.get("status") != "success":
                raise Exception(f"Winter mode setting failed: {result}")

            await self.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set winter mode: %s", err)
            raise err

    async def async_set_operation_mode(self, mode: str) -> None:
        """Set operation mode."""
        try:
            endpoint = "/user/operation/status"
            data_payload = {"operation": {mode}}
            result = await self._make_request(endpoint, "PUT", data_payload)
            if result.get("status") != "success":
                raise Exception(f"Operation mode setting failed: {result}")

            await self.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set operation mode: %s", err)
            raise err

    async def async_set_backup_mode(self, enabled: bool) -> None:
        """Set backup mode."""
        try:
            endpoint = "/user/setting/batt"
            data_payload = {"backupmode": "on" if enabled else "off"}
            result = await self._make_request(endpoint, "PUT", data_payload)
            if result.get("status") != "success":
                raise Exception(f"Backup mode setting failed: {result}")

            await self.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set backup mode: %s", err)
            raise err

    async def async_set_charge_from_grid(self, enabled: bool) -> None:
        """Set charge from grid."""
        try:
            endpoint = "/user/setting/batt"
            data_payload = {"autocharge": "1" if enabled else "0"}
            result = await self._make_request(endpoint, "PUT", data_payload)
            if result.get("status") != "success":
                raise Exception(f"Charge from grid mode setting failed: {result}")

            await self.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set charge from grid mode: %s", err)
            raise err

    async def async_set_charging_mode(self, mode: str) -> None:
        """Set charging mode."""
        try:
            endpoint = "/user/setting/batt"
            value = 0
            if mode == "fast_charge":
                value = 1
            elif mode == "battery_care":
                value = 0
            elif mode == "weather_forecast":
                value = 2
            _LOGGER.warning("Mode %s Value: %s", mode, value)
            data_payload = {"alg_setting": value}
            result = await self._make_request(endpoint, "PUT", data_payload)
            if result.get("status") != "success":
                raise Exception(f"Charging mode setting failed: {result}")

            await self.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set charging mode: %s", err)
            raise err

    async def async_set_backup_soc(self, value: int) -> None:
        """Set backup soc."""
        try:
            endpoint = "/user/setting/batt"
            value = max(0, min(value, 100))
            valStr = str(value)
            data_payload = {"backup_soc": valStr}

            result = await self._make_request(endpoint, "PUT", data_payload)
            if result.get("status") != "success":
                raise Exception(f"Set backup soc setting failed: {result}")

            await self.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set backup soc setting: %s", err)
            raise err
