"""Config flow for Ocean Pulse integration."""

from __future__ import annotations

from collections.abc import Mapping
import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_ALIAS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import (
    OceanPulseAPI,
    RequestConnectionError,
    RequestDataError,
    RequestError,
    RequestTimeoutError,
)
from .const import CONF_PAIRING_CODE, CONF_VIN, DOMAIN, URL_BASE

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_PAIRING_CODE): str})
STEP_ALIAS_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_VIN): str,
        vol.Required(CONF_ALIAS): str,
    }
)


def _parse_pairing_input(raw: str) -> tuple[str, str]:
    """Return (pairing code, base URL) from a bare code or the QR JSON payload."""
    raw = raw.strip()
    if raw.startswith("{"):
        try:
            qr = json.loads(raw)
        except ValueError as ex:
            raise InvalidPairingCode from ex
        if not isinstance(qr, dict) or not qr.get("pairingCode"):
            raise InvalidPairingCode
        return str(qr["pairingCode"]), qr.get("apiBaseUrl") or URL_BASE
    return raw, URL_BASE


async def validate_pairing(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Redeem the pairing code and return config entry data (without VIN)."""
    code, base_url = _parse_pairing_input(data[CONF_PAIRING_CODE])
    api = OceanPulseAPI()
    try:
        payload = await api.redeem_pairing_code(code, base_url)
    except RequestError as ex:
        if ex.error_code in (404, 410):
            raise InvalidPairingCode from ex
        raise CannotConnect from ex
    except (RequestConnectionError, RequestTimeoutError) as ex:
        raise CannotConnect from ex

    if not isinstance(payload, dict):
        raise InvalidPairingCode

    try:
        return OceanPulseAPI.parse_link_payload(payload, base_url)
    except RequestDataError as ex:
        _LOGGER.error("Unexpected pairing response: %s", ex)
        raise InvalidPairingCode from ex


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ocean Pulse."""

    VERSION = 1

    def __init__(self) -> None:
        super().__init__()
        self._device_data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self._device_data = await validate_pairing(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidPairingCode:
                errors["base"] = "invalid_pairing_code"
            except Exception:
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
        """Ask for the VIN (not returned by the pairing API) and an alias."""
        if user_input is not None:
            vin = user_input[CONF_VIN].strip().upper()
            await self.async_set_unique_id(vin)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"{user_input[CONF_ALIAS]} ({vin})",
                data={
                    **self._device_data,
                    "vin": vin,
                    CONF_ALIAS: user_input[CONF_ALIAS],
                },
            )

        return self.async_show_form(step_id="alias", data_schema=STEP_ALIAS_DATA_SCHEMA)

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start reauth when the stored tokens are rejected."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Re-pair with a new code; VIN and alias are kept from the entry."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        if user_input is not None:
            try:
                device_data = await validate_pairing(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidPairingCode:
                errors["base"] = "invalid_pairing_code"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry, data_updates=device_data
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            description_placeholders={"name": reauth_entry.title},
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidPairingCode(HomeAssistantError):
    """Error to indicate an invalid or expired pairing code."""
