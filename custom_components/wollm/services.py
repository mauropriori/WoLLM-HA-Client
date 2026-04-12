"""Service registration for WoLLM."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .api import WollmError
from .const import (
    ATTR_ENTRY_ID,
    ATTR_FORCE,
    ATTR_MODEL,
    DOMAIN,
    SERVICE_LOAD_MODEL,
    SERVICE_REFRESH_MODELS,
    SERVICE_SHUTDOWN,
    SERVICE_UNLOAD_MODEL,
    SERVICE_WAKE,
    SERVICES_REGISTERED,
)
from .coordinator import (
    WollmRuntimeData,
    async_load_selected_model,
    async_perform_wake,
    async_refresh_models,
    async_shutdown,
    async_unload_model,
)

WAKE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTRY_ID): cv.string})
LOAD_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTRY_ID): cv.string,
        vol.Required(ATTR_MODEL): cv.string,
    }
)
UNLOAD_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTRY_ID): cv.string})
SHUTDOWN_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTRY_ID): cv.string,
        vol.Optional(ATTR_FORCE, default=False): cv.boolean,
    }
)
REFRESH_MODELS_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTRY_ID): cv.string})


async def async_register_services(hass: HomeAssistant) -> None:
    """Register domain services once."""
    if hass.data[DOMAIN].get(SERVICES_REGISTERED):
        return

    async def handle_wake(call: ServiceCall) -> None:
        await _handle_wake(hass, call)

    async def handle_load(call: ServiceCall) -> None:
        await _handle_load(hass, call)

    async def handle_unload(call: ServiceCall) -> None:
        await _handle_unload(hass, call)

    async def handle_shutdown(call: ServiceCall) -> None:
        await _handle_shutdown(hass, call)

    async def handle_refresh_models(call: ServiceCall) -> None:
        await _handle_refresh_models(hass, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_WAKE,
        handle_wake,
        schema=WAKE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LOAD_MODEL,
        handle_load,
        schema=LOAD_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UNLOAD_MODEL,
        handle_unload,
        schema=UNLOAD_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SHUTDOWN,
        handle_shutdown,
        schema=SHUTDOWN_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_MODELS,
        handle_refresh_models,
        schema=REFRESH_MODELS_SCHEMA,
    )
    hass.data[DOMAIN][SERVICES_REGISTERED] = True


async def async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister services when the last entry is removed."""
    if any(isinstance(value, WollmRuntimeData) for value in hass.data.get(DOMAIN, {}).values()):
        return

    for service in (
        SERVICE_WAKE,
        SERVICE_LOAD_MODEL,
        SERVICE_UNLOAD_MODEL,
        SERVICE_SHUTDOWN,
        SERVICE_REFRESH_MODELS,
    ):
        hass.services.async_remove(DOMAIN, service)

    hass.data[DOMAIN].pop(SERVICES_REGISTERED, None)


def _resolve_runtime(hass: HomeAssistant, entry_id: str | None) -> WollmRuntimeData:
    """Resolve the target runtime from a service call."""
    runtimes = [
        value for value in hass.data.get(DOMAIN, {}).values() if isinstance(value, WollmRuntimeData)
    ]

    if entry_id:
        runtime = hass.data.get(DOMAIN, {}).get(entry_id)
        if isinstance(runtime, WollmRuntimeData):
            return runtime
        raise HomeAssistantError(f"Unknown entry_id: {entry_id}")

    if len(runtimes) == 1:
        return runtimes[0]

    raise HomeAssistantError("Multiple WoLLM entries configured, entry_id is required")


async def _handle_wake(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle wake service."""
    runtime = _resolve_runtime(hass, call.data.get(ATTR_ENTRY_ID))
    try:
        await async_perform_wake(runtime)
    except WollmError as err:
        raise HomeAssistantError(str(err)) from err


async def _handle_load(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle load_model service."""
    runtime = _resolve_runtime(hass, call.data.get(ATTR_ENTRY_ID))
    runtime.selected_model = call.data[ATTR_MODEL]
    try:
        await async_load_selected_model(runtime)
    except WollmError as err:
        raise HomeAssistantError(str(err)) from err


async def _handle_unload(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle unload service."""
    runtime = _resolve_runtime(hass, call.data.get(ATTR_ENTRY_ID))
    try:
        await async_unload_model(runtime)
    except WollmError as err:
        raise HomeAssistantError(str(err)) from err


async def _handle_shutdown(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle shutdown service."""
    runtime = _resolve_runtime(hass, call.data.get(ATTR_ENTRY_ID))
    try:
        await async_shutdown(runtime, bool(call.data.get(ATTR_FORCE, False)))
    except WollmError as err:
        raise HomeAssistantError(str(err)) from err


async def _handle_refresh_models(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle refresh_models service."""
    runtime = _resolve_runtime(hass, call.data.get(ATTR_ENTRY_ID))
    try:
        await async_refresh_models(runtime)
        await runtime.coordinator.async_request_refresh()
    except WollmError as err:
        raise HomeAssistantError(str(err)) from err
