"""Zaptec component binary sensors."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant import const
from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

from . import MyFiskerCoordinator

_LOGGER = logging.getLogger(__name__)


class MyButton(ButtonEntity):
    def __init__(self):
        self._state = False

    @property
    def name(self):
        return "My Button"

    @property
    def state(self):
        return self._state

    def turn_on(self, **kwargs):
        self._state = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        self._state = False
        self.schedule_update_ha_state()


class FiskerButton(ButtonEntity):
    def __init__(
        self,
        coordinator: MyFiskerCoordinator,
        description: FiskerButtonEntityDescription,
        # device_info: DeviceInfo,
    ) -> None:
        self.entity_description = description
        self._state = 0
        # self._attr_unique_id = f"{zaptec_object.id}_{description.key}"
        # self._attr_device_info = device_info

    @property
    def name(self):
        return "glostrup My Button"

    @property
    def state(self):
        return self._state

    # @callback
    # def _handle_coordinator_update(self) -> None:
    #     try:
    #         self._update_from_zaptec()
    #     except Exception as exc:
    #         raise HomeAssistantError(f"Error updating entity {self.key}") from exc
    #     super()._handle_coordinator_update()

    async def async_press(self) -> None:
        """Press the button."""
        _LOGGER.debug(
            "Press %s.%s   (in %s)",
            self.__class__.__qualname__,
            self.key,
            self.zaptec_obj.id,
        )

        try:
            await self.zaptec_obj.command(self.key)
        except Exception as exc:
            raise HomeAssistantError(f"Running command '{self.key}' failed") from exc

        await self.coordinator.async_request_refresh()


@dataclass
class FiskerButtonEntityDescription(ButtonEntityDescription):
    cls: type | None = None


BUTTON_ENTITIES: list[EntityDescription] = [
    FiskerButtonEntityDescription(
        key="doors_unlock",
        translation_key="doors_unlock",
        icon="mdi:play-circle-outline",
    ),
    FiskerButtonEntityDescription(
        key="doors_lock",
        translation_key="doors_lock",
        icon="mdi:play-circle-outline",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.debug("Setup buttons")

    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[FiskerButton] = []

    for but in BUTTON_ENTITIES:
        entities.append(FiskerButton(coordinator, but))

    async_add_entities(entities, True)
