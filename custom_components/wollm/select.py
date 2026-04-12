"""Select platform for WoLLM."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import WollmRuntimeData
from .entity import WollmCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WoLLM select."""
    runtime: WollmRuntimeData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WollmModelSelect(runtime)])


class WollmModelSelect(WollmCoordinatorEntity, SelectEntity):
    """Select the model to be loaded on demand."""

    _attr_translation_key = "model"

    def __init__(self, runtime: WollmRuntimeData) -> None:
        """Initialize select."""
        super().__init__(runtime)
        self._attr_unique_id = f"{runtime.entry.entry_id}_model"

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.runtime.is_online and bool(self.options)

    @property
    def options(self) -> list[str]:
        """Return available models."""
        return list(self.runtime.models)

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        return self.runtime.selected_model

    async def async_select_option(self, option: str) -> None:
        """Select a model without loading it yet."""
        if option not in self.runtime.models:
            raise HomeAssistantError(f"Unknown model: {option}")
        self.runtime.selected_model = option
        self.async_write_ha_state()
