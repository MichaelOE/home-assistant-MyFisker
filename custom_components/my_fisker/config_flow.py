"""Config flow for My Fisker integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ALIAS, CONF_PASSWORD, CONF_REGION, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

# from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import MyFiskerAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_REGION): vol.In(["EU", "US", "Other"]),
    }
)
STEP_ALIAS_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ALIAS): str,
    }
)


async def validate_login(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect. Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user."""

    api = MyFiskerAPI(data[CONF_USERNAME], data[CONF_PASSWORD], data[CONF_REGION])

    try:
        res = await api.GetAuthTokenAsync()
        if len(res) < 50:
            raise InvalidAuth
    except:
        raise InvalidAuth

    try:
        vin = await api.GetProfiles()
    except:
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return vin


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for My Fisker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self._userInput = user_input
                self._userInput["vin"] = await validate_login(
                    self.hass, self._userInput
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return await self.async_step_alias()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_alias(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the alias step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self._userInput[CONF_ALIAS] = user_input[CONF_ALIAS]
                _LOGGER.info(user_input)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"{self._userInput[CONF_ALIAS]}  ({self._userInput['vin']})",
                    data=self._userInput,
                )

        return self.async_show_form(
            step_id="alias", data_schema=STEP_ALIAS_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
