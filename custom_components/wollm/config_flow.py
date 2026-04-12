"""Config flow for WoLLM."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WollmApiClient, WollmAuthError, WollmConnectionError
from .const import (
    CONF_MAC_ADDRESS,
    CONF_SCAN_INTERVAL,
    CONF_WAKE_TIMEOUT,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_WAKE_TIMEOUT,
    DOMAIN,
)

MAC_PATTERN = re.compile(r"^([0-9A-Fa-f]{2}([:-]?)){5}[0-9A-Fa-f]{2}$")


def _normalize_mac(value: str) -> str:
    """Normalize a MAC address for storage and uniqueness."""
    compact = re.sub(r"[^0-9A-Fa-f]", "", value).lower()
    return ":".join(compact[idx : idx + 2] for idx in range(0, 12, 2))


def _validate_mac(value: str) -> bool:
    """Validate a MAC address."""
    return bool(MAC_PATTERN.fullmatch(value)) or len(re.sub(r"[^0-9A-Fa-f]", "", value)) == 12


async def _validate_input(hass, data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Validate config flow input."""
    errors: dict[str, str] = {}

    if not _validate_mac(data[CONF_MAC_ADDRESS]):
        errors[CONF_MAC_ADDRESS] = "invalid_mac"
        return data, errors

    normalized = {
        **data,
        CONF_HOST: data[CONF_HOST].strip(),
        CONF_NAME: data[CONF_NAME].strip(),
        CONF_API_KEY: data.get(CONF_API_KEY, "").strip(),
        CONF_MAC_ADDRESS: _normalize_mac(data[CONF_MAC_ADDRESS]),
    }

    client = WollmApiClient(
        session=async_get_clientsession(hass),
        host=normalized[CONF_HOST],
        port=normalized[CONF_PORT],
        api_key=normalized.get(CONF_API_KEY),
    )

    try:
        await client.async_health()
    except WollmAuthError:
        errors["base"] = "invalid_auth"
    except WollmConnectionError:
        pass

    return normalized, errors


class WollmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WoLLM."""

    VERSION = 1
    MINOR_VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return WollmOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data, errors = await _validate_input(self.hass, user_input)
            if not errors:
                await self.async_set_unique_id(data[CONF_MAC_ADDRESS])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=data[CONF_NAME], data=data)
        return self.async_show_form(
            step_id="user",
            data_schema=_build_user_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        """Handle reconfiguration."""
        config_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            data, errors = await _validate_input(self.hass, user_input)
            if not errors:
                await self.async_set_unique_id(data[CONF_MAC_ADDRESS])
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    config_entry,
                    data_updates=data,
                )
        current = {**config_entry.data}
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_build_user_schema(user_input or current),
            errors=errors,
        )


class WollmOptionsFlow(config_entries.OptionsFlow):
    """Handle WoLLM options."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage WoLLM options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                    vol.Required(
                        CONF_WAKE_TIMEOUT,
                        default=self.config_entry.options.get(
                            CONF_WAKE_TIMEOUT, DEFAULT_WAKE_TIMEOUT
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=900)),
                }
            ),
        )


def _build_user_schema(user_input: dict[str, Any] | None) -> vol.Schema:
    """Build the config flow form schema."""
    data = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data.get(CONF_NAME, "WoLLM")): str,
            vol.Required(CONF_HOST, default=data.get(CONF_HOST, "")): str,
            vol.Required(CONF_PORT, default=data.get(CONF_PORT, DEFAULT_PORT)): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
            vol.Required(CONF_MAC_ADDRESS, default=data.get(CONF_MAC_ADDRESS, "")): str,
            vol.Optional(CONF_API_KEY, default=data.get(CONF_API_KEY, "")): str,
        }
    )
