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
