"""Platform for sensor integration."""

from __future__ import annotations

from datetime import datetime, timezone
import logging

import pytz

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FiskerSensorEntityDescription, MyFiskerCoordinator
from .const import (
    CLIMATE_CONTROL_SEAT_HEAT,
    DOMAIN,
    LIST_CLIMATE_CONTROL_SEAT_HEAT,
    MANUCFACTURER,
    MODEL,
    TRIM_EXTREME_ULTRA_BATT_CAPACITY,
    TRIM_SPORT_BATT_CAPACITY,
)
from .entities_sensor import (
    SENSORS_CAR_SETTINGS,
    SENSORS_DIGITAL_TWIN,
    SENSORS_ChargeStat,
    SENSORS_tripSTAT,
)

_LOGGER = logging.getLogger(__name__)


class FiskerSensor(CoordinatorEntity, SensorEntity):
    # An entity using CoordinatorEntity.

    def __init__(
        self,
        coordinator: MyFiskerCoordinator,
        idx,
        sensor: FiskerSensorEntityDescription,
        client,
    ):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx = idx
        # self._sensor = sensor
        self._data = client
        self._coordinator = coordinator
        self.vin = self._coordinator.data["vin"]
        self.entity_description: FiskerSensorEntityDescription = sensor
        self._attr_unique_id = f"{self._coordinator.data['vin']}_{sensor.key}"
        self._attr_name = f"{self._coordinator.alias} {sensor.name}"

        _LOGGER.info(self._attr_unique_id)

        if sensor.native_unit_of_measurement:
            self._attr_native_unit_of_measurement = sensor.native_unit_of_measurement
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "seat_heat" in self.entity_description.key:
            self._attr_options = LIST_CLIMATE_CONTROL_SEAT_HEAT
            self._attr_device_class = SensorDeviceClass.ENUM

    @property
    def device_info(self):
        """Return device information about this entity."""
        _LOGGER.debug("My Fisker: device_info")

        return {
            "identifiers": {
                # Unique identifiers within a specific domain
                (DOMAIN, self._coordinator.data["vin"])
            },
            "manufacturer": MANUCFACTURER,
            "model": MODEL,
            "name": self._coordinator.alias,
        }

    @property
    def battery_capacity(self):
        # VCF1Z = One, VCF1E = Extreme, VCF1U = Ultra VCF1S = Sport
        trim_extreme_ultra = ["VCF1Z", "VCF1E", "VCF1U"]
        trim_sport = ["VCF1s"]
        if self.vin[0:5] in trim_extreme_ultra:
            return TRIM_EXTREME_ULTRA_BATT_CAPACITY
        if self.vin[0:5] in trim_sport:
            return TRIM_SPORT_BATT_CAPACITY
        else:
            return 0

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        data_available = False

        self.update_chargestats()
        self.update_tripstats()

        if "car_settings" in self.entity_description.key:
            try:
                value = self.handle_carsettings(self.entity_description.key)
                data_available = True
                self._attr_native_value = value
            except:
                _LOGGER.debug("car_settings not available")

        elif "tripstat" in self.entity_description.key:
            self._attr_native_value = self.handle_tripstats(self.entity_description.key)

        elif "chargestat" in self.entity_description.key:
            self._attr_native_value = self.handle_chargestats(
                self.entity_description.key
            )

        else:
            value = self._coordinator.data[self.idx[1]]
            data_available = True

            if "seat_heat" in self.entity_description.key:
                self._attr_native_value = CLIMATE_CONTROL_SEAT_HEAT[value][0]
            elif "updated" in self.entity_description.key:
                utc_time = datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                )  # value = '2025-01-02T13:32:49.585703Z'
                local_time = utc_time + self._coordinator.time_difference_from_utc
                self._attr_native_value = local_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                self._attr_native_value = value

        self._attr_available = data_available
        self.async_write_ha_state()

    def handle_carsettings(self, key):
        value = "n/a"

        carSetting = self._coordinator.my_fisker_api.GetCarSettings()
        value = self.entity_description.get_car_settings_value(carSetting)

        if "_updated" in key:
            utc_timestamp = value["updated"]  #'2025-01-02T13:32:49.585703Z'
            utc_time = datetime.fromisoformat(utc_timestamp.replace("Z", "+00:00"))
            hass_tz = self._coordinator._hass.config.time_zone
            local_time = utc_time.astimezone(pytz.timezone(hass_tz))
            value = local_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            value = value["value"]

        return value

    def handle_tripstats(self, key):
        batt_factor = self.battery_capacity / 100
        value = None

        if "battery" in key:
            value = round(self._coordinator.tripstats.batt * batt_factor, 2)

        elif "distance" in key:
            value = self._coordinator.tripstats.dist

        elif "duration" in key:
            value = self._coordinator.tripstats.time

        elif "_efficiency" in key:
            value = round(self._coordinator.tripstats.efficiency * batt_factor, 2)

        elif "_efficiency_dist" in key:
            value = round(self._coordinator.tripstats.efficiency_dist * batt_factor, 2)

        elif "_prevefficiency" in key:
            value = round(
                self._coordinator.tripstats.previous_efficiency * batt_factor, 2
            )

        elif "speed" in key:
            value = self._coordinator.tripstats.average_speed

        return value

    def handle_chargestats(self, key):
        batt_factor = self.battery_capacity / 100
        value = None

        if "battery" in key:
            value = round(self._coordinator.chargestats.batt * batt_factor, 2)

        if "distance" in key:
            value = self._coordinator.chargestats.dist

        if "duration" in key:
            value = self._coordinator.chargestats.time

        if "_efficiency" in key:
            value = round(self._coordinator.chargestats.efficiency * batt_factor, 2)

        if "_prevefficiency" in key:
            value = round(
                self._coordinator.chargestats.previous_efficiency * batt_factor, 2
            )

        if "speed" in key:
            value = self._coordinator.chargestats.average_speed

        return value

    def update_tripstats(self):
        carStartedDriving = False
        carIsDriving = False
        carEndedDriving = False

        if self._coordinator.tripstats.vehicleParked is True:
            if (
                self._coordinator.tripstats.vehicleParked
                != self._coordinator.data["gear_in_park"]
            ):
                # _LOGGER.info("carStartedDriving")
                carStartedDriving = True

        if (
            self._coordinator.tripstats.vehicleParked is False
            and self._coordinator.data["gear_in_park"] is False
        ):
            # _LOGGER.info("carIsDriving")
            carIsDriving = True

        if (
            self._coordinator.tripstats.vehicleParked is False
            and self._coordinator.data["gear_in_park"] is True
        ):
            # _LOGGER.info("carEndedDriving")
            carEndedDriving = True

        self._coordinator.tripstats.vehicleParked = self._coordinator.data[
            "gear_in_park"
        ]

        if carStartedDriving:
            self._coordinator.tripstats.Clear()

            # Get battery info
            if "battery_percent" in self.entity_description.key:
                self._coordinator.tripstats.add_battery(
                    self._coordinator.data[self.idx[1]]
                )
            # Get distance info
            if "battery_total_mileage_odometer" in self.entity_description.key:
                self._coordinator.tripstats.add_distance(
                    self._coordinator.data[self.idx[1]]
                )

        if carIsDriving:
            # Get battery info
            if "battery_percent" in self.entity_description.key:
                prevBatt = self._attr_native_value

                # Save battery info
                if prevBatt != self._coordinator.data[self.idx[1]]:
                    self._coordinator.tripstats.add_battery(
                        self._coordinator.data[self.idx[1]]
                    )

            # Get distance info
            if "battery_total_mileage_odometer" in self.entity_description.key:
                prevDist = self._attr_native_value

                # Save distance info
                if prevDist != self._coordinator.data[self.idx[1]]:
                    self._coordinator.tripstats.add_distance(
                        self._coordinator.data[self.idx[1]]
                    )

        elif carEndedDriving:
            pass

    def update_chargestats(self):
        carIsCharging = False
        carEndedCharging = False

        if self._coordinator.chargestats.carIsRunning is False:
            carIsCharging = True

        if carIsCharging:
            if "Initial_value" in self._coordinator.data["battery_charge_type"]:
                carIsCharging = False
                carEndedCharging = True

        # Remember if vehicle is 'charging' and/or 'parked'
        self._coordinator.chargestats.carIsRunning = (
            "charging" not in self._coordinator.data["battery_charge_type"]
        )
        self._coordinator.chargestats.vehicleParked = self._coordinator.data[
            "gear_in_park"
        ]

        if carEndedCharging:
            self._coordinator.chargestats.Clear()

            # Get battery info
            if "battery_percent" in self.entity_description.key:
                self._coordinator.chargestats.add_battery(
                    self._coordinator.data[self.idx[1]]
                )

            # Get distance info
            if "battery_total_mileage_odometer" in self.entity_description.key:
                self._coordinator.chargestats.add_distance(
                    self._coordinator.data[self.idx[1]]
                )

        if carIsCharging is False:
            # Get battery info
            if "battery_percent" in self.entity_description.key:
                prevBatt = self._attr_native_value

                # Save battery info
                if prevBatt != self._coordinator.data[self.idx[1]]:
                    self._coordinator.chargestats.add_battery(
                        self._coordinator.data[self.idx[1]]
                    )

            # Get distance info
            if "battery_total_mileage_odometer" in self.entity_description.key:
                prevDist = self._attr_native_value

                # Save distance info
                if prevDist != self._coordinator.data[self.idx[1]]:
                    self._coordinator.chargestats.add_distance(
                        self._coordinator.data[self.idx[1]]
                    )
        else:
            pass

    @property
    def should_poll(self):
        return False

    @property
    def friendly_name(self):
        return self.entity_description.name

    @property
    def state(self):
        try:
            retVal = self._attr_native_value
            # if self.entity_description.format != None:
            #     parsed_datetime = datetime.strptime(retVal, "%Y-%m-%dT%H:%M:%S.%fZ")
            #     # Convert to the desired output format
            #     retVal = parsed_datetime.strftime(self.entity_description.format)

            state = retVal

        except (KeyError, ValueError):
            return None
        return state


# Get an item by its key
def get_sensor_by_key(key):
    for sensor in SENSORS_DIGITAL_TWIN:
        if sensor.key == key:
            return sensor


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

    entities.extend(
        FiskerSensor(coordinator, 100, sensor, my_Fisker_data)
        for sensor in SENSORS_CAR_SETTINGS
    )
    entities.extend(
        FiskerSensor(coordinator, 200, sensor, my_Fisker_data)
        for sensor in SENSORS_tripSTAT
    )
    entities.extend(
        FiskerSensor(coordinator, 300, sensor, my_Fisker_data)
        for sensor in SENSORS_ChargeStat
    )

    # Add entities to Home Assistant
    async_add_entities(entities)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    # Code for setting up your platform inside of the event loop
    _LOGGER.debug("async_setup_platform")
