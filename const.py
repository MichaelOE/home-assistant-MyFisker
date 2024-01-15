"""Constants for the My Fisker integration."""

DOMAIN = "my_fisker"

API_TIMEOUT = 10
DEFAULT_SCAN_INTERVAL = 60

TOKEN_URL = "https://auth.fiskerdps.com/auth/login"
WSS_URL = "wss://gw.cec-euprd.fiskerinc.com/mobile"

CLIMATE_CONTROL_SEAT_HEAT = {
    0: ["Unknown", "mdi:help-rhombus-outline"],
    1: ["High", "mdi:car-seat-heater"],
    2: ["Medium", "mdi:car-seat-heater"],
    3: ["Low", "mdi:car-seat-heater"],
    4: ["Off", "mdi:car-seat-heater"],
}
