"""Zaptec component binary sensors."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import (
    OceanPulseBaseEntity,
    OceanPulseButtonEntityDescription,
    OceanPulseCoordinator,
)
from .api import AuthenticationError, OceanPulseAPI
from .const import DEVICE_MANUCFACTURER, DEVICE_MODEL, DOMAIN
from .entities_button import BUTTON_ENTITIES

_LOGGER = logging.getLogger(__name__)


class OceanPulseButton(OceanPulseBaseEntity, ButtonEntity):
    """Button entity for OceanPulse vehicle commands."""

    def __init__(
        self,
        coordinator: OceanPulseCoordinator,
        description: OceanPulseButtonEntityDescription,
        # device_info: DeviceInfo,
    ) -> None:
        """Initialize OceanPulse vehicle sensor."""
        super().__init__(coordinator, -1)

        self.entity_description = description
        self._coordinator: OceanPulseCoordinator = coordinator
        self._state = 0
        self._attr_unique_id = f"{self._coordinator.vin}_{description.key}"
        self._attr_name = f"{self._coordinator.alias} {description.name}"

        _LOGGER.info(self._attr_unique_id)

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
        super()._handle_coordinator_update()

    async def async_press(self) -> None:
        """Press the button."""
        _LOGGER.info("Press %s", self.entity_description.key)

        api: OceanPulseAPI = self._coordinator.api

        try:
            await api.send_command(
                self._coordinator.vin,
                self.entity_description.command,
                self.entity_description.command_data,
            )
        except AuthenticationError as exc:
            self._coordinator.config_entry.async_start_reauth(self.hass)
            raise HomeAssistantError(
                "Ocean Pulse authentication expired, please re-pair the device"
            ) from exc
        except Exception as exc:
            raise HomeAssistantError(
                f"Running command '{self.entity_description.key}' failed"
            ) from exc

        await self._coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.debug("Setup buttons")

    coordinator: OceanPulseCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [OceanPulseButton(coordinator, but) for but in BUTTON_ENTITIES], True
    )
