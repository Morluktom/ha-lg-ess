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
UPDATE_INTERVAL_FAST: Final = 10  # seconds for switch updates
UPDATE_INTERVAL_NORMAL: Final = 30  # seconds for sensor updates
DEFAULT_SCAN_INTERVAL: Final = 30


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
