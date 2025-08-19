import asyncio
import logging
import time

from aiohttp.client_exceptions import ContentTypeError

from json import JSONDecodeError
from enum import Enum

import aiohttp


class LgEssException(Exception):
    """Base exception for LG ESS errors."""

    pass


class LgEssAuthException(LgEssException):
    """Authentication exception for LG ESS."""

    pass


class LgEssChargingModes(Enum):
    """Charging modes for LG ESS."""

    BATTERY_CARE = 0
    FAST_CHARGE = 1
    WEATHER_FORECAST = 2


class LgEssOperationModes(Enum):
    """Operation modes for LG ESS."""

    START = 0
    STOP = 1


_LOGGER = logging.getLogger(__name__)


class LgEss:
    """LG ESS API client."""

    @classmethod
    async def create(cls, name=None, password=None, ip=None):
        """Create and initialize LG ESS instance."""
        ess = cls(name, password, ip)
        await ess.login()
        await ess.timesync()
        return ess

    def __init__(self, name, pw, host=None):
        """Initialize LG ESS client."""
        self._name = name
        self._password = pw
        self._host = host
        self._logged_in = False
        self._auth_key = None
        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False),
            timeout=aiohttp.ClientTimeout(
                connect=60, sock_read=60, sock_connect=60, total=180
            ),
        )

    async def login(self):
        """Authenticate with the LG ESS system."""
        login_url = f"https://{self._host}/v1/user/setting/login"
        login_data = {"password": self._password}

        async with self._session.put(login_url, json=login_data) as response:
            response_json = await response.json()

        if (
            "status" in response_json
            and response_json["status"] == "password mismatched"
        ):
            raise LgEssAuthException("wrong password")

        self._auth_key = response_json["auth_key"]
        self._logged_in = True

        return self._auth_key

    async def timesync(self, retry=1):
        """Time synchronisation with the LG ESS system."""
        timesync_url = f"https://{self._host}/v1/user/setting/timesync"
        timesync_info = {
            "auth_key": self._auth_key,
            "by": "phone",
            "date_time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        }

        async with self._session.put(timesync_url, json=timesync_info) as response:
            try:
                response_json = await response.json()
                assert response_json["status"] == "success", response_json
            except (JSONDecodeError, ContentTypeError):
                await asyncio.sleep(retry)  # Fixed: time.sleep -> asyncio.sleep
                return await self.login(retry=retry * 2)  # Fixed: _login -> login

    async def make_request(
        self, endpoint: str, method: str = "POST", data: dict = None, retries: int = 15
    ) -> dict:
        """Make authenticated request to LG ESS API."""
        url = f"https://{self._host}/v1{endpoint}"
        json_data = {"auth_key": self._auth_key}

        # Add additional data if provided
        if data:
            json_data.update(data)

        response_json = None
        response_status = None

        if method == "POST":
            async with self._session.post(url, json=json_data) as response:
                response_json = await response.json()
                response_status = response.status
        elif method == "PUT":
            async with self._session.put(url, json=json_data) as response:
                response_json = await response.json()
                response_status = response.status

        if response_status == 200 and (
            response_json != {"auth": "auth_key failed"}
            and response_json != {"auth": "auth failed"}
        ):
            return response_json

        _LOGGER.info("Authentication failed, retrying after %d seconds", retries)
        await asyncio.sleep(retries)
        await self.login()
        return await self.make_request(endpoint, method, data, retries=retries * 2)

    async def get_common_data(self) -> dict:
        """Update common data via direct HTTP API calls."""
        return await self.make_request("/user/essinfo/common")

    async def get_home_data(self) -> dict:
        """Update home data via direct HTTP API calls."""
        return await self.make_request("/user/essinfo/home")

    async def get_setting_battery(self) -> dict:
        """Update setting battery data via direct HTTP API calls."""
        return await self.make_request("/user/setting/batt")

    async def get_setting_network(self) -> dict:
        """Update setting network data via direct HTTP API calls."""
        return await self.make_request("/user/setting/network")

    async def get_system_info(self) -> dict:
        """Update system info data via direct HTTP API calls."""
        return await self.make_request("/user/setting/systeminfo")

    # Control methods using direct API calls
    async def set_operation_mode(self, mode: LgEssOperationModes) -> None:
        """Set operation mode."""
        try:
            endpoint = "/user/operation/status"
            data_payload = {"operation": mode.name.lower()}
            result = await self.make_request(endpoint, "PUT", data_payload)
            if result.get("status") != "success":
                raise LgEssException(f"Operation mode setting failed: {result}")

        except Exception as err:
            _LOGGER.error("Failed to set operation mode: %s", err)
            raise err

    async def set_winter_mode(self, enabled: bool) -> None:
        """Set winter mode."""
        try:
            endpoint = "/user/setting/batt"
            data_payload = {"wintermode": "on" if enabled else "off"}
            result = await self.make_request(endpoint, "PUT", data_payload)
            if result.get("status") != "success":
                raise LgEssException(f"Winter mode setting failed: {result}")

        except Exception as err:
            _LOGGER.error("Failed to set winter mode: %s", err)
            raise err

    async def set_backup_mode(self, enabled: bool) -> None:
        """Set backup mode."""
        try:
            endpoint = "/user/setting/batt"
            data_payload = {"backupmode": "on" if enabled else "off"}
            result = await self.make_request(endpoint, "PUT", data_payload)
            if result.get("status") != "success":
                raise LgEssException(f"Backup mode setting failed: {result}")

        except Exception as err:
            _LOGGER.error("Failed to set backup mode: %s", err)
            raise err

    async def set_charge_from_grid(self, enabled: bool) -> None:
        """Set charge from grid mode."""
        try:
            endpoint = "/user/setting/batt"
            data_payload = {"autocharge": "1" if enabled else "0"}
            result = await self.make_request(endpoint, "PUT", data_payload)
            if result.get("status") != "success":
                raise LgEssException(f"Charge from grid mode setting failed: {result}")

        except Exception as err:
            _LOGGER.error("Failed to set charge from grid mode: %s", err)
            raise err

    async def set_charging_mode(self, mode: LgEssChargingModes) -> None:
        """Set charging mode."""
        try:
            endpoint = "/user/setting/batt"
            data_payload = {"alg_setting": mode.value}
            result = await self.make_request(endpoint, "PUT", data_payload)
            if result.get("status") != "success":
                raise LgEssException(f"Charging mode setting failed: {result}")

        except Exception as err:
            _LOGGER.error("Failed to set charging mode: %s", err)
            raise err

    async def set_backup_soc(self, value: int) -> None:
        """Set backup SOC percentage."""
        try:
            endpoint = "/user/setting/batt"
            value = max(0, min(value, 100))
            data_payload = {"backup_soc": str(value)}
            result = await self.make_request(endpoint, "PUT", data_payload)
            if result.get("status") != "success":
                raise LgEssException(f"Backup SOC setting failed: {result}")

        except Exception as err:
            _LOGGER.error("Failed to set backup SOC: %s", err)
            raise err

    async def close(self):
        """Close the session properly."""
        if self._session and not self._session.closed:
            await self._session.close()

    def __del__(self):
        """Destructor - avoid warnings by not scheduling tasks."""
        # Don't schedule tasks in destructor as event loop might be closed
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    # Deprecated method for backward compatibility
    async def destruct(self):
        """Tear down connector - deprecated, use close() or async context manager."""
        _LOGGER.warning(
            "destruct() is deprecated, use close() or async context manager"
        )
        await self.close()
