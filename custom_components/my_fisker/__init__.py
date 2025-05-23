"""The My Fisker integration."""

from __future__ import annotations

import asyncio.timeouts
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging

import pytz

from homeassistant.components.button import ButtonEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ALIAS,
    CONF_PASSWORD,
    CONF_REGION,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import MyFiskerAPI
from .const import (
    DEVICE_MANUCFACTURER,
    DEVICE_MODEL,
    DOMAIN,
    TRIM_EXTREME_ULTRA_BATT_CAPACITY,
    TRIM_SPORT_BATT_CAPACITY,
)
from .stats import TripStats

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the My Fisker component."""

    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up My Fisker from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    data = entry.data
    myFiskerApi = MyFiskerAPI(
        data[CONF_USERNAME], data[CONF_PASSWORD], data[CONF_REGION]
    )
    await myFiskerApi.GetAuthTokenAsync()

    # Fetch initial data so we have data when entities subscribe
    coordinator = MyFiskerCoordinator(hass, myFiskerApi, data[CONF_ALIAS])
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = HassMyFisker(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_ALIAS],
        entry.data[CONF_REGION],
        coordinator,
    )

    # Get the time difference between UTC and local time zone
    utc_time = datetime.now(pytz.utc)
    local_time = utc_time.astimezone(pytz.timezone(hass.config.time_zone))
    coordinator.time_difference_from_utc = local_time.utcoffset()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await coordinator.async_refresh()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class HassMyFisker:
    def __init__(
        self,
        username: str,
        password: str,
        alias: str,
        region: str,
        coordinator: DataUpdateCoordinator,
    ):
        self._username = username
        self._password = password
        self._alias = alias
        self._region = region
        self._coordinator = coordinator

        _LOGGER.debug(
            f"MyFisker __init__{self._username}:{self._alias}, region={self._region}"
        )

    def get_name(self):
        return f"myFisker_{self._username}"

    def get_unique_id(self):
        return f"myfisker_{self._username}"


class MyFiskerCoordinator(DataUpdateCoordinator):
    """My Fisker coordinator."""

    def __init__(self, hass, my_api: MyFiskerAPI, alias: str):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=f"MyFisker coordinator for '{alias}'",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        self._hass = hass
        self._previous_update_interval = self.update_interval

        self.my_fisker_api = my_api
        self.alias = alias
        self.time_difference_from_utc = None
        self.tripstats: TripStats = TripStats()
        self.chargestats: TripStats = TripStats()

    async def _async_update_data(self):
        # Fetch data from API endpoint. This is the place to pre-process the data to lookup tables so entities can quickly look up their data.
        try:
            async with asyncio.timeout(30):
                await self.my_fisker_api.GetAuthTokenAsync()
                retData = await self.my_fisker_api.GetDigitalTwin()
                await self.my_fisker_api.GetCarSettings()
                await self.my_fisker_api.GetProfiles()

                self._previous_update_interval = self.update_interval

                # Dynamic refresh rate, based on door lock status
                if retData.get("door_locks_driver") is True:
                    self.update_interval = timedelta(seconds=60)
                else:
                    self.update_interval = timedelta(seconds=20)

                # Log only if the update interval has changed
                if self.update_interval != self._previous_update_interval:
                    _LOGGER.info(
                        "Fisker refresh rate changed from %s to %s",
                        self._previous_update_interval,
                        self.update_interval,
                    )
                    # Trigger an immediate refresh to apply the new interval
                    await self.async_refresh()

                return retData
        except Exception as ex:
            _LOGGER.error(f"MyCoordinator _async_update_data failed: {ex}")
        # except ApiAuthError as err:
        #     # Raising ConfigEntryAuthFailed will cancel future updates
        #     # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        #     raise ConfigEntryAuthFailed from err
        # except ApiError as err:
        #     raise UpdateFailed(f"Error communicating with API: {err}")


class FiskerBaseEntity(CoordinatorEntity):
    """Common base for MyFisker entities."""

    # _attr_should_poll = False
    _attr_attribution = "Data provided by FOCE (Fisker API)"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.index = index
        self._coordinator = coordinator

        if self._coordinator.data is None:
            _LOGGER.warning(
                f"FiskerBaseEntity: self._coordinator.data is None - ({self.index})"
            )
            return

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{self._coordinator.data['vin']}")},
            manufacturer=DEVICE_MANUCFACTURER,
            model=DEVICE_MODEL,
            name=self._coordinator.alias,
        )

    @property
    def device_info(self):
        """Return device information about this entity."""
        return self._attr_device_info


@dataclass
class FiskerButtonEntityDescription(ButtonEntityDescription):
    """Describes MyFisker ID button entity."""

    def __init__(
        self, key, name, translation_key, icon, command: str, command_data: str = None
    ):
        super().__init__(key)
        self.key = key
        self.name = name
        self.translation_key = translation_key
        self.icon = icon
        self.command = command
        self.command_data = command_data


@dataclass
class FiskerSensorEntityDescription(SensorEntityDescription):
    """Describes MyFisker ID sensor entity."""

    def __init__(
        self,
        key,
        name,
        icon,
        device_class,
        native_unit_of_measurement,
        value,
        format=None,
    ):
        super().__init__(key)
        self.key = key
        self.name = name
        self.icon = icon
        if device_class is not None:
            self.device_class = device_class
        self.native_unit_of_measurement = native_unit_of_measurement
        self.value = value
        self.format = format

    def get_digital_twin_value(self, data):
        return self.value(data, self.key)

    def get_car_settings_value(self, data):
        return self.findInArray(
            data, self.key.replace("car_settings_", "").replace("_updated", "")
        )

    def findInArray(self, jsonArray: str, nameToSearch: str):
        # Loop through the array
        for item in jsonArray["data"]:
            if item["name"] == nameToSearch:
                value = item["value"]
                name = item["name"]
                return item
                break
        else:
            return None
