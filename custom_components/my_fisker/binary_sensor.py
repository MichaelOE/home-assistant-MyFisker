"""Platform for binary_sensor integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FiskerSensorEntityDescription
from .const import CLIMATE_CONTROL_STEERING_WHEEL_HEAT, DOMAIN, DOOR_LOCK, GEAR_IN_PARK
from .entities_binary_sensor import BINARY_SENSORS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.debug("Setup sensors")

    my_Fisker_data = hass.data[DOMAIN][entry.entry_id]

    coordinator = my_Fisker_data._coordinator

    entities: list[FiskerSensor] = []

    # for sensor in SENSORS:
    for idx in enumerate(coordinator.data):
        sens = get_sensor_by_key(idx[1])
        if sens is None:
            _LOGGER.warning(idx[1])
        else:
            entities.append(FiskerSensor(coordinator, idx, sens, my_Fisker_data))

    # Add entities to Home Assistant
    async_add_entities(entities)


class FiskerSensor(CoordinatorEntity):
    """Sensor used by all Fisker entities, inherits from CoordinatorEntity."""

    def __init__(self, coordinator, idx, sensor: FiskerSensorEntityDescription, client):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx = idx
        self._data = client
        self._coordinator = coordinator
        self.entity_description = sensor
        self._attr_unique_id = f"{self._coordinator.data['vin']}_{sensor.key}"
        self._attr_name = f"{self._coordinator._alias} {sensor.name}"

        _LOGGER.info(self._attr_unique_id)

        # if "climate_control_steering_wheel_heat" in self.entity_description.key:
        # self.options = LIST_CLIMATE_CONTROL_STEERING_WHEEL_HEAT
        # self.device_class = SensorDeviceClass.ENUM

    @property
    def device_info(self):
        """Return device information about this entity."""
        _LOGGER.debug("My Fisker: device_info")

        return {
            "identifiers": {
                # Unique identifiers within a specific domain
                (DOMAIN, self._coordinator.data["vin"])
            },
            "manufacturer": "Fisker inc.",
            "model": "Fisker (Ocean)",
            "name": self._coordinator._alias,
        }

    @property
    def icon(self):
        return self.entity_description.icon

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        value = self._coordinator.data[self.idx[1]]

        if "doors_" in self.entity_description.key:
            self._attr_state = DOOR_LOCK[value][0]
        elif "gear_in_park" in self.entity_description.key:
            self._attr_state = GEAR_IN_PARK[value][0]
        elif "climate_control_steering_wheel_heat" in self.entity_description.key:
            self._attr_state = CLIMATE_CONTROL_STEERING_WHEEL_HEAT[value][0]
        else:
            self._attr_state = value

        self._attr_available = True
        # self._attr_is_on = True

        self.async_write_ha_state()

    @property
    def should_poll(self):
        return False

    @property
    def state(self):
        try:
            state = self._attr_state
        except (KeyError, ValueError):
            return None
        return state


# Get an item by its key
def get_sensor_by_key(key):
    for sensor in BINARY_SENSORS:
        if sensor.key == key:
            return sensor
    return None
