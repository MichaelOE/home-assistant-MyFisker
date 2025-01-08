"""The My Fisker integration."""

from __future__ import annotations

import asyncio.timeouts
from dataclasses import dataclass
from datetime import timedelta
import logging

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
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import MyFiskerAPI
from .const import DOMAIN, TRIM_EXTREME_ULTRA_BATT_CAPACITY, TRIM_SPORT_BATT_CAPACITY
from .stats import TripStats

_LOGGER = logging.getLogger(__name__)

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]


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

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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
        self.my_fisker_api = my_api
        self._alias = alias
        self.tripstats: TripStats = TripStats()
        self.chargestats: TripStats = TripStats()

    async def _async_update_data(self):
        # Fetch data from API endpoint. This is the place to pre-process the data to lookup tables so entities can quickly look up their data.
        try:
            async with asyncio.timeout(30):
                await self.my_fisker_api.GetAuthTokenAsync()
                retData = await self.my_fisker_api.GetDigitalTwin()

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
        except:
            _LOGGER.error("MyCoordinator _async_update_data failed")
        # except ApiAuthError as err:
        #     # Raising ConfigEntryAuthFailed will cancel future updates
        #     # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        #     raise ConfigEntryAuthFailed from err
        # except ApiError as err:
        #     raise UpdateFailed(f"Error communicating with API: {err}")


@dataclass
class FiskerEntityDescription(SensorEntityDescription):
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
