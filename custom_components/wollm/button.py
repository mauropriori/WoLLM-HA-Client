"""Button platform for WoLLM."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import WollmBadRequestError, WollmError, WollmNotFoundError, WollmTimeoutError
from .const import DOMAIN
from .coordinator import (
    WollmRuntimeData,
    async_load_selected_model,
    async_perform_wake,
    async_shutdown,
    async_unload_model,
)
from .entity import WollmCoordinatorEntity


@dataclass(slots=True, kw_only=True)
class WollmButtonDescription(ButtonEntityDescription):
    """Description for WoLLM buttons."""

    press_action: Callable[[WollmRuntimeData], Awaitable[None]]
    always_available: bool = False


DESCRIPTIONS = (
    WollmButtonDescription(
        key="wake_server",
        translation_key="wake_server",
        press_action=async_perform_wake,
        always_available=True,
    ),
    WollmButtonDescription(
        key="load_selected_model",
        translation_key="load_selected_model",
        press_action=async_load_selected_model,
    ),
    WollmButtonDescription(
        key="unload_model",
        translation_key="unload_model",
        press_action=async_unload_model,
    ),
    WollmButtonDescription(
        key="shutdown_server",
        translation_key="shutdown_server",
        press_action=lambda runtime: async_shutdown(runtime, False),
    ),
    WollmButtonDescription(
        key="force_shutdown_server",
        translation_key="force_shutdown_server",
        press_action=lambda runtime: async_shutdown(runtime, True),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WoLLM buttons."""
    runtime: WollmRuntimeData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(WollmButton(runtime, description) for description in DESCRIPTIONS)


class WollmButton(WollmCoordinatorEntity, ButtonEntity):
    """WoLLM action button."""

    entity_description: WollmButtonDescription

    def __init__(self, runtime: WollmRuntimeData, description: WollmButtonDescription) -> None:
        """Initialize button."""
        super().__init__(runtime)
        self.entity_description = description
        self._attr_unique_id = f"{runtime.entry.entry_id}_{description.key}"

    @property
    def available(self) -> bool:
        """Return button availability."""
        if self.entity_description.always_available:
            return True
        if self.entity_description.key == "load_selected_model" and not self.runtime.selected_model:
            return False
        return self.runtime.is_online

    async def async_press(self) -> None:
        """Handle button press."""
        try:
            await self.entity_description.press_action(self.runtime)
        except WollmNotFoundError as err:
            raise HomeAssistantError(f"Model not found: {err}") from err
        except WollmTimeoutError as err:
            raise HomeAssistantError(f"Model startup timeout: {err}") from err
        except WollmBadRequestError as err:
            raise HomeAssistantError(str(err)) from err
        except WollmError as err:
            raise HomeAssistantError(str(err)) from err
