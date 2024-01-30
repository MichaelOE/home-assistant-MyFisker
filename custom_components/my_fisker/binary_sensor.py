import logging

from homeassistant.components.my_fisker import FiskerEntityDescription
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    CLIMATE_CONTROL_SEAT_HEAT,
    CLIMATE_CONTROL_STEERING_WHEEL_HEAT,
    DOMAIN,
    DOOR_LOCK,
    GEAR_IN_PARK,
    LIST_CLIMATE_CONTROL_STEERING_WHEEL_HEAT,
)

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
    def __init__(self, coordinator, idx, sensor: FiskerEntityDescription, client):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx = idx
        self._data = client
        self._coordinator = coordinator
        self.entity_description = sensor
        self._attr_unique_id = f"{self._coordinator.data['vin']}_{sensor.key}"
        self._attr_name = f"{self._coordinator._alias} {sensor.name}"

        _LOGGER.info(self._attr_unique_id)

        if "climate_control_steering_wheel_heat" in self.entity_description.key:
            self.options = LIST_CLIMATE_CONTROL_STEERING_WHEEL_HEAT
            self.device_class = SensorDeviceClass.ENUM

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


BINARY_SENSORS: tuple[SensorEntityDescription, ...] = (
    FiskerEntityDescription(
        key="climate_control_steering_wheel_heat",
        name="Steering wheel heat",
        icon="mdi:steering",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="door_locks_all",
        name="Door locks all",
        icon="mdi:car-door-lock",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="door_locks_driver",
        name="Door locks driver",
        icon="mdi:car-door-lock",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="doors_hood",
        name="Doors hood",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="doors_left_front",
        name="Door left front",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="doors_left_rear",
        name="Door left rear",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="doors_right_front",
        name="Door right front",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="doors_right_rear",
        name="Door right rear",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="doors_trunk",
        name="Door trunk",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="gear_in_park",
        name="Gear in park",
        icon="mdi:car-brake-parking",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="online",
        name="Online State",
        icon="mdi:car-connected",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="online_hmi",
        name="Online hmi",
        icon="mdi:car-connected",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
)
