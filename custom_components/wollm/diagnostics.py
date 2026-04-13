"""Diagnostics support for WoLLM."""

from __future__ import annotations

from copy import deepcopy

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import WollmRuntimeData


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""
    runtime: WollmRuntimeData = hass.data[DOMAIN][entry.entry_id]
    entry_data = dict(entry.data)
    if CONF_API_KEY in entry_data:
        entry_data[CONF_API_KEY] = "***redacted***"

    return {
        "entry": entry_data,
        "options": dict(entry.options),
        "models": list(runtime.models),
        "selected_model": runtime.selected_model,
        "effective_status": runtime.effective_status,
        "last_error": runtime.last_error,
        "last_health": deepcopy(runtime.last_health_raw),
        "last_status": deepcopy(runtime.last_status_raw),
    }
