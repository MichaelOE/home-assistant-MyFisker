"""Zaptec component binary sensors."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FiskerButtonEntityDescription, MyFiskerCoordinator
from .api import MyFiskerAPI
from .const import DEVICE_MANUCFACTURER, DEVICE_MODEL, DOMAIN
from .entities_button import BUTTON_ENTITIES

_LOGGER = logging.getLogger(__name__)


class FiskerButton(ButtonEntity):
    def __init__(
        self,
        coordinator: MyFiskerCoordinator,
        description: FiskerButtonEntityDescription,
        # device_info: DeviceInfo,
    ) -> None:
        self.entity_description = description
        self._coordinator: MyFiskerCoordinator = coordinator
        # self.vin = self._coordinator.data["vin"]
        self._state = 0
        self._attr_unique_id = f"{self._coordinator.data['vin']}_{description.key}"
        self._attr_name = f"{self._coordinator.alias} {description.name}"

        _LOGGER.info(self._attr_unique_id)

    @property
    def device_info(self):
        """Return device information about this entity."""

        return {
            "identifiers": {
                # Unique identifiers within a specific domain
                (DOMAIN, self._coordinator.data["vin"])
            },
            "manufacturer": DEVICE_MANUCFACTURER,
            "model": DEVICE_MODEL,
            "name": self._coordinator.alias,
        }

    @property
    def name(self):
        return self._attr_name

    @property
    def friendly_name(self):
        return self.entity_description.name

    # @property
    # def is_on(self):
    #     return self._state

    @property
    def state(self):
        return self._state

    @callback
    def _handle_coordinator_update(self) -> None:
        try:
            _LOGGER.info("Fisker: _handle_coordinator_update")
        except Exception as exc:
            raise HomeAssistantError(f"Error updating entity {self.key}") from exc
        super()._handle_coordinator_update()

    async def async_press(self) -> None:
        """Press the button."""
        _LOGGER.info("Press %s", self.entity_description.key)

        api: MyFiskerAPI = self._coordinator.my_fisker_api

        try:
            if self.entity_description.command_data:
                await api.SendCommandRequest(
                    self.entity_description.command,
                    self.entity_description.command_data,
                )
            else:
                await api.SendCommandRequest(self.entity_description.command)
        except Exception as exc:
            raise HomeAssistantError(
                f"Running command '{self.entity_description.key}' failed"
            ) from exc

        await self._coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.debug("Setup buttons")

    my_Fisker_data = hass.data[DOMAIN][entry.entry_id]

    coordinator = my_Fisker_data._coordinator

    entities: list[FiskerButton] = []

    for but in BUTTON_ENTITIES:
        entities.append(FiskerButton(coordinator, but))

    async_add_entities(entities, True)
