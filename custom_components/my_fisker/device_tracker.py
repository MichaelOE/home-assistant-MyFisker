import logging

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FiskerBaseEntity, FiskerSensorEntityDescription
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Add sensors for passed config_entry in HA."""

    my_Fisker_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = my_Fisker_data._coordinator
    entities: list[DeviceTrackerSensor] = []

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    sens = DEVICE_TRACKER_SENSORS[0]
    entities.append(DeviceTrackerSensor(sens, my_Fisker_data))

    if entities:
        async_add_entities(entities)


class DeviceTrackerSensor(FiskerBaseEntity, TrackerEntity):
    """Representation of a vehicle device_Tracker sensor."""

    def __init__(
        self,
        sensor: FiskerSensorEntityDescription,
        client,
    ) -> None:
        """Initialize My Fisker vehicle sensor."""
        super().__init__(client._coordinator, -1)

        self._coordinator = client._coordinator
        self._data = client
        self.entity_description = sensor
        self._attr_unique_id = (
            f"{self._coordinator.data['vin']}_{self.entity_description.key}"
        )
        self._attr_name = f"{self._coordinator.alias} {self.entity_description.name}"

        _LOGGER.info(self._attr_unique_id)

    @property
    def icon(self):
        return self.entity_description.icon

    @property
    def latitude(self) -> float:
        """Return latitude value of the device."""
        try:
            lat = self._coordinator.data["location_latitude"]
            return lat
        except KeyError:
            return None

    @property
    def longitude(self) -> float:
        """Return longitude value of the device."""
        try:
            lon = self._coordinator.data["location_longitude"]
            return lon
        except KeyError:
            return None

    @property
    def battery_level(self) -> float:
        """Return battery_level of the device."""
        try:
            soc = self._coordinator.data["battery_state_of_charge"]
            return soc
        except KeyError:
            return None

    @property
    def source_type(self):
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def extra_state_attributes(self):
        """Return timestamp of when the data was captured."""
        try:
            return {"last_captured": f"{self._coordinator.data['updated']}"}
        except KeyError:
            return None


# Get an item by its key
def get_sensor_by_key(key):
    for sensor in DEVICE_TRACKER_SENSORS:
        if sensor.key == key:
            return sensor
    return None


DEVICE_TRACKER_SENSORS: tuple[SensorEntityDescription, ...] = (
    FiskerSensorEntityDescription(
        key="device_location",
        name="Location",
        icon="mdi:crosshairs-gps",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
)
