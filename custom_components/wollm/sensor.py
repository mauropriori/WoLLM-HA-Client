"""Sensor platform for WoLLM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import WollmRuntimeData
from .entity import WollmCoordinatorEntity


@dataclass(slots=True, kw_only=True)
class WollmSensorDescription(SensorEntityDescription):
    """Description for WoLLM sensors."""

    value_fn: Any
    always_available: bool = False


DESCRIPTIONS = (
    WollmSensorDescription(
        key="server_status",
        translation_key="server_status",
        value_fn=lambda runtime: runtime.effective_status,
        always_available=True,
    ),
    WollmSensorDescription(
        key="current_model",
        translation_key="current_model",
        value_fn=lambda runtime: runtime.status.current_model if runtime.status else None,
    ),
    WollmSensorDescription(
        key="idle_seconds",
        translation_key="idle_seconds",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda runtime: runtime.status.idle_seconds if runtime.status else None,
    ),
    WollmSensorDescription(
        key="ram_used_mb",
        translation_key="ram_used_mb",
        native_unit_of_measurement="MB",
        value_fn=lambda runtime: runtime.status.ram_used_mb if runtime.status else None,
    ),
    WollmSensorDescription(
        key="ram_total_mb",
        translation_key="ram_total_mb",
        native_unit_of_measurement="MB",
        value_fn=lambda runtime: runtime.status.ram_total_mb if runtime.status else None,
    ),
    WollmSensorDescription(
        key="wol_boot",
        translation_key="wol_boot",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda runtime: runtime.status.wol_boot if runtime.status else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WoLLM sensors."""
    runtime: WollmRuntimeData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(WollmSensor(runtime, description) for description in DESCRIPTIONS)


class WollmSensor(WollmCoordinatorEntity, SensorEntity):
    """WoLLM coordinator-backed sensor."""

    entity_description: WollmSensorDescription

    def __init__(self, runtime: WollmRuntimeData, description: WollmSensorDescription) -> None:
        """Initialize sensor."""
        super().__init__(runtime)
        self.entity_description = description
        self._attr_unique_id = f"{runtime.entry.entry_id}_{description.key}"

    @property
    def available(self) -> bool:
        """Return availability."""
        if self.entity_description.always_available:
            return True
        return self.runtime.is_online

    @property
    def native_value(self) -> Any:
        """Return sensor value."""
        return self.entity_description.value_fn(self.runtime)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose useful status metadata."""
        if self.entity_description.key != "server_status":
            return None
        attrs: dict[str, Any] = {}
        if self.runtime.last_error:
            attrs["last_error"] = self.runtime.last_error
        if self.runtime.status:
            attrs["shutdown_on_idle"] = self.runtime.status.shutdown_on_idle
            attrs["idle_timeout_minutes"] = self.runtime.status.idle_timeout_minutes
            attrs["wol_boot"] = self.runtime.status.wol_boot
        return attrs
