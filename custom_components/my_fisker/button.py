"""Zaptec component binary sensors."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MyFiskerCoordinator
from .const import DOMAIN
from .api import MyFiskerAPI

_LOGGER = logging.getLogger(__name__)


# class MyButton(ButtonEntity):
#     def __init__(self):
#         self._state = False

#     @property
#     def name(self):
#         return "My Button"

#     @property
#     def state(self):
#         return self._state

#     def turn_on(self, **kwargs):
#         self._state = True
#         self.schedule_update_ha_state()

#     def turn_off(self, **kwargs):
#         self._state = False
#         self.schedule_update_ha_state()


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


@dataclass
class FiskerButtonEntityDescription(ButtonEntityDescription):
    """Describes MyFisker ID button entity."""

    def __init__(self, key, name, translation_key, icon):
        super().__init__(key)
        self.key = key
        self.name = name
        self.translation_key = translation_key
        self.icon = icon


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.debug("Setup buttons")

    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[FiskerButton] = []

    for but in BUTTON_ENTITIES:
        entities.append(FiskerButton(coordinator, but))

    async_add_entities(entities, True)


BUTTON_ENTITIES: list[EntityDescription] = [
    FiskerButtonEntityDescription(
        key="doors_unlock",
        name="doors_unlock",
        translation_key="doors_unlock",
        icon="mdi:car-door-lock-open",
    ),
    FiskerButtonEntityDescription(
        key="doors_lock",
        name="doors_lock",
        translation_key="doors_lock",
        icon="mdi:car-door-lock",
    ),
    FiskerButtonEntityDescription(
        key="trunk_open",
        name="trunk_open",
        translation_key="doors_lock",
        icon="mdi:play-circle-outline",
    ),
    FiskerButtonEntityDescription(
        key="trunk_close",
        name="trunk_close",
        translation_key="doors_lock",
        icon="mdi:play-circle-outline",
    ),
]
