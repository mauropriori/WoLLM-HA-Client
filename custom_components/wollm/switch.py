"""Switch platform for WoLLM."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import WollmError
from .const import DOMAIN
from .coordinator import WollmRuntimeData, async_set_runtime_settings
from .entity import WollmCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WoLLM switches."""
    runtime: WollmRuntimeData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            WollmShutdownOnIdleSwitch(runtime),
            WollmUnloadOnIdleSwitch(runtime),
        ]
    )


class WollmShutdownOnIdleSwitch(WollmCoordinatorEntity, SwitchEntity):
    """Toggle WoLLM shutdown on idle."""

    _attr_translation_key = "shutdown_on_idle"

    def __init__(self, runtime: WollmRuntimeData) -> None:
        """Initialize switch."""
        super().__init__(runtime)
        self._attr_unique_id = f"{runtime.entry.entry_id}_shutdown_on_idle"

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.runtime.is_online

    @property
    def is_on(self) -> bool:
        """Return current switch state."""
        return bool(self.runtime.status and self.runtime.status.shutdown_on_idle)

    async def async_turn_on(self, **kwargs) -> None:
        """Enable shutdown on idle."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable shutdown on idle."""
        await self._async_set_state(False)

    async def _async_set_state(self, enabled: bool) -> None:
        """Set switch state and surface API errors nicely."""
        try:
            await async_set_runtime_settings(self.runtime, shutdown_on_idle=enabled)
        except WollmError as err:
            raise HomeAssistantError(str(err)) from err


class WollmUnloadOnIdleSwitch(WollmCoordinatorEntity, SwitchEntity):
    """Toggle WoLLM unload on idle."""

    _attr_translation_key = "unload_on_idle"

    def __init__(self, runtime: WollmRuntimeData) -> None:
        """Initialize switch."""
        super().__init__(runtime)
        self._attr_unique_id = f"{runtime.entry.entry_id}_unload_on_idle"

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.runtime.is_online

    @property
    def is_on(self) -> bool:
        """Return current switch state."""
        return bool(self.runtime.status and self.runtime.status.unload_on_idle)

    async def async_turn_on(self, **kwargs) -> None:
        """Enable unload on idle."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable unload on idle."""
        await self._async_set_state(False)

    async def _async_set_state(self, enabled: bool) -> None:
        """Set switch state and surface API errors nicely."""
        try:
            await async_set_runtime_settings(self.runtime, unload_on_idle=enabled)
        except WollmError as err:
            raise HomeAssistantError(str(err)) from err
