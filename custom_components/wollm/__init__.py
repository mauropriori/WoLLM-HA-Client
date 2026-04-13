"""The WoLLM integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import async_build_runtime
from .services import async_register_services, async_unregister_services

PLATFORMS: tuple[Platform, ...] = (
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the WoLLM integration."""
    hass.data.setdefault(DOMAIN, {})
    await async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WoLLM from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    runtime = await async_build_runtime(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = runtime
    await async_register_services(hass)
    await runtime.coordinator.async_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a WoLLM config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        await async_unregister_services(hass)
    return unload_ok
