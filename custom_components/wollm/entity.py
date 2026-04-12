"""Base entity helpers for WoLLM."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import MANUFACTURER, MODEL
from .coordinator import WollmRuntimeData


class WollmCoordinatorEntity(CoordinatorEntity):
    """Base coordinator entity for WoLLM."""

    _attr_has_entity_name = True

    def __init__(self, runtime: WollmRuntimeData) -> None:
        """Initialize the base entity."""
        super().__init__(runtime.coordinator)
        self.runtime = runtime
        self._attr_device_info = DeviceInfo(
            identifiers={(self.runtime.entry.domain, self.runtime.entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=self.runtime.entry.title,
            configuration_url=self.runtime.client.base_url,
            connections={
                (
                    CONNECTION_NETWORK_MAC,
                    self.runtime.entry.data["mac_address"].lower().replace("-", ":"),
                )
            },
        )
