"""Platform for sensor integration."""

from __future__ import annotations

from datetime import datetime
import logging
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
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
    CLIMATE_CONTROL_SEAT_HEAT,
    DOMAIN,
    LIST_CLIMATE_CONTROL_SEAT_HEAT,
    TRIM_EXTREME_ULTRA_BATT_CAPACITY,
    TRIM_SPORT_BATT_CAPACITY,
)
from .entities_sensor import (
    SENSORS_CAR_SETTINGS,
    SENSORS_DIGITAL_TWIN,
    # SENSORS_ChargeStat,
    # SENSORS_tripSTAT,
)

_LOGGER = logging.getLogger(__name__)


class OceanPulseSensor(OceanPulseBaseEntity, CoordinatorEntity, SensorEntity):
    """Sensor entity for Ocean Pulse."""

    def __init__(
        self,
        coordinator: OceanPulseCoordinator,
        idx,
        sensor: OceanPulseSensorEntityDescription,
    ) -> None:
        """Initialize Ocean Pulse sensor."""
        super().__init__(coordinator, idx)

        self.idx = idx
        self._coordinator = coordinator
        self.vin = coordinator.vin
        self.entity_description: OceanPulseSensorEntityDescription = sensor
        self._attr_unique_id = f"{coordinator.vin}_{sensor.key}"
        self._attr_name = f"{coordinator.alias} {sensor.name}"

        _LOGGER.info(self._attr_unique_id)

        if sensor.native_unit_of_measurement:
            self._attr_native_unit_of_measurement = sensor.native_unit_of_measurement
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "SEAT_HEAT" in self.entity_description.key:
            self._attr_options = LIST_CLIMATE_CONTROL_SEAT_HEAT
            self._attr_device_class = SensorDeviceClass.ENUM

        if sensor.suggested_display_precision is not None:
            self._attr_suggested_display_precision = sensor.suggested_display_precision

        self._attr_entity_registry_visible_default = (
            sensor.entity_registry_visible_default
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._coordinator.data is None:
            _LOGGER.warning(
                "sensor _handle_coordinator_update: (%s)", self.entity_description.key
            )
            return

        data_available = False

        # self.update_chargestats()
        # self.update_tripstats()

        # if "tripstat" in self.entity_description.key:
        #     self._attr_native_value = self.handle_tripstats(self.entity_description.key)

        # elif "chargestat" in self.entity_description.key:
        #     self._attr_native_value = self.handle_chargestats(
        #         self.entity_description.key
        #     )

        # else:
        value = self._coordinator.data.get(self.idx[1])
        data_available = value is not None

        if "SEAT_HEAT" in self.entity_description.key:
            self._attr_native_value = CLIMATE_CONTROL_SEAT_HEAT[value][0]
        elif "last_update" in self.entity_description.key:
            utc_time = datetime.fromisoformat(value.replace("Z", "+00:00"))
            local_time = utc_time + self._coordinator.time_difference_from_utc
            self._attr_native_value = local_time.strftime(
                self.entity_description.format
            )
        else:
            self._attr_native_value = value

        self._attr_available = data_available
        self.async_write_ha_state()

    @property
    def should_poll(self):
        return False

    @property
    def friendly_name(self):
        return self.entity_description.name

    @property
    def extra_state_attributes(self):
        return None

    def handle_carsettings(self, key):
        carSetting = self._coordinator.data.get("car_settings", {})
        value = self.entity_description.get_car_settings_value(carSetting)

        if "_updated" in key:
            utc_timestamp = value["updated"]
            utc_time = datetime.fromisoformat(utc_timestamp.replace("Z", "+00:00"))
            hass_tz = self._coordinator.hass.config.time_zone
            local_time = utc_time.astimezone(ZoneInfo(hass_tz))
            return local_time.strftime("%Y-%m-%d %H:%M:%S")

        return value["value"]

    # def handle_tripstats(self, key):
    #     batt_factor = self.battery_capacity / 100
    #     value = None

    #     if "battery" in key:
    #         value = round(self._coordinator.tripstats.batt * batt_factor, 2)
    #     elif "distance" in key:
    #         value = self._coordinator.tripstats.dist
    #     elif "duration" in key:
    #         value = self._coordinator.tripstats.time
    #     elif "_efficiency_dist" in key:
    #         value = round(self._coordinator.tripstats.efficiency_dist * batt_factor, 2)
    #     elif "_efficiency" in key:
    #         value = round(self._coordinator.tripstats.efficiency * batt_factor, 2)
    #     elif "_prevefficiency" in key:
    #         value = round(
    #             self._coordinator.tripstats.previous_efficiency * batt_factor, 2
    #         )
    #     elif "speed" in key:
    #         value = self._coordinator.tripstats.average_speed

    #     return value

    # def handle_chargestats(self, key):
    #     batt_factor = self.battery_capacity / 100
    #     value = None

    #     if "battery" in key:
    #         value = round(self._coordinator.chargestats.batt * batt_factor, 2)
    #     if "distance" in key:
    #         value = self._coordinator.chargestats.dist
    #     if "duration" in key:
    #         value = self._coordinator.chargestats.time
    #     if "_efficiency" in key:
    #         value = round(self._coordinator.chargestats.efficiency * batt_factor, 2)
    #     if "_prevefficiency" in key:
    #         value = round(
    #             self._coordinator.chargestats.previous_efficiency * batt_factor, 2
    #         )
    #     if "speed" in key:
    #         value = self._coordinator.chargestats.average_speed

    #     return value

    # def update_tripstats(self):
    #     is_parked = self._coordinator.data.get("POWER_MODE") == "off"
    #     was_parked = self._coordinator.tripstats.vehicleParked

    #     carStartedDriving = was_parked is True and not is_parked
    #     carIsDriving = was_parked is False and not is_parked
    #     carEndedDriving = was_parked is False and is_parked

    #     self._coordinator.tripstats.vehicleParked = is_parked

    #     if carStartedDriving:
    #         self._coordinator.tripstats.Clear()
    #         if self.entity_description.key == "SOC":
    #             self._coordinator.tripstats.add_battery(
    #                 self._coordinator.data[self.idx[1]]
    #             )
    #         if self.entity_description.key == "MILEAGE":
    #             self._coordinator.tripstats.add_distance(
    #                 self._coordinator.data[self.idx[1]]
    #             )

    #     if carIsDriving:
    #         if self.entity_description.key == "SOC":
    #             prevBatt = self._attr_native_value
    #             if prevBatt != self._coordinator.data[self.idx[1]]:
    #                 self._coordinator.tripstats.add_battery(
    #                     self._coordinator.data[self.idx[1]]
    #                 )
    #         if self.entity_description.key == "MILEAGE":
    #             prevDist = self._attr_native_value
    #             if prevDist != self._coordinator.data[self.idx[1]]:
    #                 self._coordinator.tripstats.add_distance(
    #                     self._coordinator.data[self.idx[1]]
    #                 )

    # def update_chargestats(self):
    #     is_charging = bool(self._coordinator.data.get("CHARGING", 0))
    #     was_charging = not self._coordinator.chargestats.carIsRunning

    #     carEndedCharging = was_charging and not is_charging

    #     self._coordinator.chargestats.carIsRunning = not is_charging
    #     self._coordinator.chargestats.vehicleParked = (
    #         self._coordinator.data.get("POWER_MODE") == "off"
    #     )

    #     if carEndedCharging:
    #         self._coordinator.chargestats.Clear()
    #         if self.entity_description.key == "SOC":
    #             self._coordinator.chargestats.add_battery(
    #                 self._coordinator.data[self.idx[1]]
    #             )
    #         if self.entity_description.key == "MILEAGE":
    #             self._coordinator.chargestats.add_distance(
    #                 self._coordinator.data[self.idx[1]]
    #             )

    #     if is_charging:
    #         if self.entity_description.key == "SOC":
    #             prevBatt = self._attr_native_value
    #             if prevBatt != self._coordinator.data[self.idx[1]]:
    #                 self._coordinator.chargestats.add_battery(
    #                     self._coordinator.data[self.idx[1]]
    #                 )
    #         if self.entity_description.key == "MILEAGE":
    #             prevDist = self._attr_native_value
    #             if prevDist != self._coordinator.data[self.idx[1]]:
    #                 self._coordinator.chargestats.add_distance(
    #                     self._coordinator.data[self.idx[1]]
    #                 )


def get_sensor_by_key(key):
    for sensor in SENSORS_DIGITAL_TWIN:
        if sensor.key == key:
            return sensor
    return None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.debug("Setup sensors")

    coordinator: OceanPulseCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[OceanPulseSensor] = []

    for idx in enumerate(coordinator.data):
        sens = get_sensor_by_key(idx[1])
        if sens is None:
            _LOGGER.warning(idx[1])
        else:
            entities.append(OceanPulseSensor(coordinator, idx, sens))

    entities.extend(
        OceanPulseSensor(coordinator, 100, sensor) for sensor in SENSORS_CAR_SETTINGS
    )
    # entities.extend(
    #     OceanPulseSensor(coordinator, 200, sensor) for sensor in SENSORS_tripSTAT
    # )
    # entities.extend(
    #     OceanPulseSensor(coordinator, 300, sensor) for sensor in SENSORS_ChargeStat
    # )

    async_add_entities(entities)
