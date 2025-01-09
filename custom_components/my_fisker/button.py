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
from .const import DOMAIN
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
        self.coordinator: MyFiskerCoordinator = coordinator
        self._state = 0
        self._attr_unique_id = (
            f"{self.coordinator._coordinator.data['vin']}_{description.key}"
        )
        self._attr_name = f"{self.coordinator._coordinator._alias} {description.name}"

    @property
    def state(self):
        return self._state

    @callback
    def _handle_coordinator_update(self) -> None:
        try:
            # self._update_from_zaptec()
            _LOGGER.info("Fisker: _handle_coordinator_update")
        except Exception as exc:
            raise HomeAssistantError(f"Error updating entity {self.key}") from exc
        super()._handle_coordinator_update()

    async def async_press(self) -> None:
        """Press the button."""
        _LOGGER.debug("Press %s", self.entity_description.key)

        api: MyFiskerAPI = self.coordinator._coordinator.my_fisker_api

        try:
            await api.SendCommandRequest(self.entity_description.key)
        except Exception as exc:
            raise HomeAssistantError(
                f"Running command '{self.entity_description.key}' failed"
            ) from exc

        await self.coordinator._coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.debug("Setup buttons")

    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[FiskerButton] = []

    for but in BUTTON_ENTITIES:
        entities.append(FiskerButton(coordinator, but))

    async_add_entities(entities, True)
