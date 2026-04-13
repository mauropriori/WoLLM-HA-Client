"""Number platform for WoLLM."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
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
    """Set up WoLLM numbers."""
    runtime: WollmRuntimeData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WollmIdleTimeoutNumber(runtime)])


class WollmIdleTimeoutNumber(WollmCoordinatorEntity, NumberEntity):
    """Expose the WoLLM idle timeout as a configurable number."""

    _attr_translation_key = "idle_timeout_minutes"
    _attr_native_min_value = 1
    _attr_native_max_value = 1440
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, runtime: WollmRuntimeData) -> None:
        """Initialize number entity."""
        super().__init__(runtime)
        self._attr_unique_id = f"{runtime.entry.entry_id}_idle_timeout_minutes"

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.runtime.is_online

    @property
    def native_value(self) -> float | None:
        """Return the current idle timeout in minutes."""
        if not self.runtime.status or self.runtime.status.idle_timeout_minutes is None:
            return None
        return float(self.runtime.status.idle_timeout_minutes)

    async def async_set_native_value(self, value: float) -> None:
        """Update the WoLLM idle timeout."""
        try:
            await async_set_runtime_settings(
                self.runtime,
                idle_timeout_minutes=int(value),
            )
        except WollmError as err:
            raise HomeAssistantError(str(err)) from err
