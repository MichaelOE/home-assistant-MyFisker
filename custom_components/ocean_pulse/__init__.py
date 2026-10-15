"""The Ocean Pulse integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
from zoneinfo import ZoneInfo

from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.components.button import ButtonEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ALIAS, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import AuthenticationError, OceanPulseAPI, PulseDeviceLink
from .const import DEVICE_MANUCFACTURER, DEVICE_MODEL, DOMAIN
from .stats import TripStats

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ocean Pulse from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    data = entry.data

    @callback
    def _async_persist_tokens(link: PulseDeviceLink) -> None:
        # The server rotates refresh tokens, so the new pair must survive restarts
        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                "access_token": link.access_token,
                "refresh_token": link.refresh_token,
            },
        )

    api = OceanPulseAPI(on_tokens_refreshed=_async_persist_tokens)
    link = PulseDeviceLink(
        vin=data["vin"],
        device_id=data["device_id"],
        car_device_id=data["car_device_id"],
        api_base_url=data["api_base_url"],
        profile_id=data["profile_id"],
        access_token=data.get("access_token"),
        refresh_token=data.get("refresh_token"),
    )
    api.link_device(link)

    coordinator = OceanPulseCoordinator(hass, entry, api, data["vin"], data[CONF_ALIAS])

    utc_time = datetime.now(timezone.utc)
    local_time = utc_time.astimezone(ZoneInfo(hass.config.time_zone))
    coordinator.time_difference_from_utc = local_time.utcoffset()

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class OceanPulseCoordinator(DataUpdateCoordinator):
    """Ocean Pulse coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: OceanPulseAPI,
        vin: str,
        alias: str,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"OceanPulse coordinator for '{alias}'",
            update_interval=timedelta(seconds=30),
        )
        self.api = api
        self.vin = vin
        self.alias = alias
        self._previous_update_interval = self.update_interval
        self.time_difference_from_utc = None
        self.tripstats: TripStats = TripStats()
        self.chargestats: TripStats = TripStats()

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            async with asyncio.timeout(30):
                raw = await self.api.get_status(self.vin)
                data = dict(raw.get("status", {}))
                location = data.pop("LOCATION", {})
                data["lat"] = location.get("lat")
                data["lon"] = location.get("lon")
                data["device_id"] = raw.get("device_id")
                data["device_name"] = raw.get("device_name")

                self._previous_update_interval = self.update_interval

                if data.get("POWER_MODE") == "off":
                    self.update_interval = timedelta(seconds=60)
                else:
                    self.update_interval = timedelta(seconds=20)

                self.update_interval = timedelta(seconds=300)

                if self.update_interval != self._previous_update_interval:
                    _LOGGER.info(
                        "OceanPulse refresh rate changed from %s to %s",
                        self._previous_update_interval,
                        self.update_interval,
                    )

                return data
        except AuthenticationError as ex:
            raise ConfigEntryAuthFailed(str(ex)) from ex
        except Exception as ex:
            raise UpdateFailed(f"Error communicating with API: {ex}") from ex


class OceanPulseBaseEntity(CoordinatorEntity):
    """Common base for OceanPulse entities."""

    _attr_attribution = "Data provided by FOCE (OceanPulse API)"

    def __init__(
        self,
        coordinator: OceanPulseCoordinator,
        index: int,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self.index = index
        self._coordinator = coordinator

        if self._coordinator is None:
            _LOGGER.warning(
                "OceanPulseBaseEntity: coordinator data is None - (%s)", self.index
            )
            return

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.vin)},
            manufacturer=DEVICE_MANUCFACTURER,
            model=DEVICE_MODEL,
            name=coordinator.alias,
        )

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information about this entity."""
        return self._attr_device_info


@dataclass
class OceanPulseButtonEntityDescription(ButtonEntityDescription):
    """Describes OceanPulse button entity."""

    def __init__(
        self,
        key: str,
        name: str,
        translation_key: str,
        icon: str,
        command: str,
        command_data: str | None = None,
    ) -> None:
        super().__init__(key)
        self.key = key
        self.name = name
        self.translation_key = translation_key
        self.icon = icon
        self.command = command
        self.command_data = command_data


@dataclass
class OceanPulseBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Ocean Pulse binary sensor entity."""

    def __init__(
        self,
        key: str,
        name: str,
        icon: str,
        device_class,
        value,
    ) -> None:
        super().__init__(key)
        self.key = key
        self.name = name
        self.icon = icon
        if device_class is not None:
            self.device_class = device_class
        self.value = value

    def get_value(self, data):
        return self.value(data, self.key)


@dataclass
class OceanPulseSensorEntityDescription(SensorEntityDescription):
    """Describes Ocean Pulse sensor entity."""

    def __init__(
        self,
        key: str,
        name: str,
        icon: str,
        device_class,
        native_unit_of_measurement,
        value,
        format=None,
        suggested_display_precision: int | None = None,
        entity_registry_visible_default: bool = True,
    ) -> None:
        super().__init__(key)
        self.key = key
        self.name = name
        self.icon = icon
        if device_class is not None:
            self.device_class = device_class
        self.native_unit_of_measurement = native_unit_of_measurement
        self.value = value
        self.format = format
        self.suggested_display_precision = suggested_display_precision
        self.entity_registry_visible_default = entity_registry_visible_default

    def get_digital_twin_value(self, data):
        return self.value(data, self.key)

    def get_car_settings_value(self, data):
        return self._find_in_array(
            data, self.key.replace("car_settings_", "").replace("_updated", "")
        )

    def _find_in_array(self, json_array: dict, name_to_search: str):
        for item in json_array["data"]:
            if item["name"] == name_to_search:
                return item
        return None
