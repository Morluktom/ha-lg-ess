"""Constants for the LG ESS integration."""

from typing import Final

DOMAIN: Final = "lg_ess"

# Configuration constants
CONF_PASSWORD: Final = "password"
CONF_HOST: Final = "host"

# Default values
DEFAULT_HOST: Final = "192.168.1.98"

# Device information
MANUFACTURER: Final = "LG Electronics"
MODEL: Final = "ESS Inverter"

# Update intervals
SCAN_INTERVAL_COMMON: Final = 30
SCAN_INTERVAL_SYSTEM_INFO: Final = 900

# Configuration constants
CONF_UPDATE_INTERVAL = "update_interval"

# Default values
DEFAULT_UPDATE_INTERVAL = 10  # Sekunden
MIN_UPDATE_INTERVAL = 5  # Minimum 5 Sekunden
MAX_UPDATE_INTERVAL = 20  # Maximum 20 Sekunden


# Keys always disable
KEYS_ALWAYS_DISABLE = [
    "battery_a_serials",
    "battery_a_pack_dates",
    "battery_b_serials",
    "battery_b_pack_dates",
]

# Keys battery 1
KEYS_BATTERY_1 = [
    "battery_nameplate_energy_1",
    "battery_cycle_count_1",
    "battery_remaining_cap_1",
    "battery_discharge_rate_1",
    "battery_charge_energy_1",
    "battery_discharge_energy_1",
    "battery_charge_cap_1",
    "battery_discharge_cap_1",
    "battery_deep_discharge_count_1",
    "battery_overcharge_count_1",
    "bms_unit1_version",
]

# Keys battery 2
KEYS_BATTERY_2 = [
    "battery_nameplate_energy_2",
    "battery_cycle_count_2",
    "battery_remaining_cap_2",
    "battery_discharge_rate_2",
    "battery_charge_energy_2",
    "battery_discharge_energy_2",
    "battery_charge_cap_2",
    "battery_discharge_cap_2",
    "battery_deep_discharge_count_2",
    "battery_overcharge_count_2",
    "bms_unit2_version",
]
