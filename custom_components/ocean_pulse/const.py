"""Constants for the Ocean Pulse integration."""

DOMAIN = "ocean_pulse"

DEVICE_MANUCFACTURER = "Fisker"
DEVICE_MODEL = "Ocean (via Ocean Pulse)"

API_TIMEOUT = 10
DEFAULT_SCAN_INTERVAL = 60

URL_BASE = "https://www.oceanlinkpulse.com"

CONF_PAIRING_CODE = "pairing_code"
CONF_BASE_URL = "base_url"
CONF_VIN = "vin"

HANDLER_COMMAND = "remote_command"
COMMAND_DOORS_UNLOCK = "doors_unlock"
COMMAND_DOORS_LOCK = "doors_lock"
COMMAND_TRUNK_OPEN = "trunk_open"
COMMAND_TRUNK_CLOSE = "trunk_close"
COMMAND_CALIFORNIA_MODE = "california_mode"

TRIM_EXTREME_ULTRA_BATT_CAPACITY = 106
TRIM_SPORT_BATT_CAPACITY = 75

LIST_CLIMATE_CONTROL_SEAT_HEAT = ["Unknown", "High", "Medium", "Low", "Off"]
LIST_CLIMATE_CONTROL_STEERING_WHEEL_HEAT = ["Unknown", "Off", "On"]

CLIMATE_CONTROL_SEAT_HEAT = {
    0: ["Unknown", "mdi:help-rhombus-outline"],
    1: ["High", "mdi:car-seat-heater"],
    2: ["Medium", "mdi:car-seat-heater"],
    3: ["Low", "mdi:car-seat-heater"],
    4: ["Off", "mdi:car-seat-heater"],
}

CLIMATE_CONTROL_STEERING_WHEEL_HEAT = {
    False: ["Off", "mdi:car-door"],
    True: ["On", "mdi:car-door"],
}

GEAR_IN_PARK = {
    False: ["Driving", "mdi:car-door"],
    True: ["Parked", "mdi:car-door"],
}

DOOR_LOCK = {
    False: ["Closed", "mdi:car-door"],
    True: ["Open", "mdi:car-door"],
}
