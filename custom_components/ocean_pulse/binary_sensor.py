"""Platform for binary_sensor integration."""

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import (
    OceanPulseBaseEntity,
    OceanPulseCoordinator,
    OceanPulseSensorEntityDescription,
)
from .const import (
    CLIMATE_CONTROL_STEERING_WHEEL_HEAT,
    DEVICE_MANUCFACTURER,
    DEVICE_MODEL,
    DOMAIN,
    DOOR_LOCK,
    GEAR_IN_PARK,
)
from .entities_binary_sensor import BINARY_SENSORS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.debug("Setup sensors")

    coordinator: OceanPulseCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[OceanPulseBinarySensor] = []

    # for sensor in SENSORS:
    for idx in enumerate(coordinator.data):
        sens = get_sensor_by_key(idx[1])
        if sens is None:
            _LOGGER.warning(idx[1])
        else:
            entities.append(OceanPulseBinarySensor(coordinator, idx, sens))

    # Add entities to Home Assistant
    async_add_entities(entities)


class OceanPulseBinarySensor(
    OceanPulseBaseEntity, CoordinatorEntity, BinarySensorEntity
):
    """Sensor used by all Fisker entities, inherits from CoordinatorEntity."""

    def __init__(
        self,
        coordinator: OceanPulseCoordinator,
        idx,
        sensor: OceanPulseSensorEntityDescription,
    ) -> None:
        """Initialize Ocean Pulse vehicle sensor."""
        super().__init__(coordinator, idx)

        self.idx = idx
        self.vin = coordinator.vin
        self.entity_description: OceanPulseSensorEntityDescription = sensor
        self._attr_unique_id = f"{coordinator.vin}_{sensor.key}"
        self._attr_name = f"{coordinator.alias} {sensor.name}"

        _LOGGER.info(self._attr_unique_id)

    @property
    def icon(self):
        return self.entity_description.icon

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if self._coordinator.data is None:
            _LOGGER.warning(
                f"binary_sensor _handle_coordinator_update: ({self.entity_description.key})"
            )
            return

        try:
            value = self._coordinator.data[self.idx[1]]
        except KeyError:
            _LOGGER.error(
                f"binary_sensor: _handle_coordinator_update KeyError: {self.idx[1]}"
            )
            return
        except Exception as ex:
            _LOGGER.error(
                f"binary_sensor: _handle_coordinator_update Exception: {self.idx[1]} ({ex})"
            )
            return

        value = self._coordinator.data[self.idx[1]]

        # if "DOOR_" in self.entity_description.key:
        #     self._attr_state = DOOR_LOCK[value][0]
        # # elif "gear_in_park" in self.entity_description.key:
        # #     self._attr_state = GEAR_IN_PARK[value][0]
        # elif "STEERING_WHEEL_HEAT" in self.entity_description.key:
        #     self._attr_state = CLIMATE_CONTROL_STEERING_WHEEL_HEAT[value][0]
        # else:
        #     self._attr_state = value

        # self._attr_available = True
        # # self._attr_is_on = True

        self._attr_is_on = bool(value)
        self._attr_available = True

        self.async_write_ha_state()

    @property
    def should_poll(self):
        return False


# Get an item by its key
def get_sensor_by_key(key):
    for sensor in BINARY_SENSORS:
        if sensor.key == key:
            return sensor
    return None
