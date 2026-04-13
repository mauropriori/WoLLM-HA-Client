"""Coordinator for WoLLM state."""

from __future__ import annotations

import asyncio
import contextlib
import ipaddress
import logging
import socket
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    WollmApiClient,
    WollmAuthError,
    WollmConnectionError,
    WollmError,
    WollmNotFoundError,
    WollmStatus,
    WollmTimeoutError,
)
from .const import (
    CONF_MAC_ADDRESS,
    CONF_SCAN_INTERVAL,
    CONF_WAKE_TIMEOUT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_WAKE_TIMEOUT,
    DOMAIN,
    STATUS_ERROR,
    STATUS_IDLE,
    STATUS_LOADING,
    STATUS_OFFLINE,
    STATUS_RUNNING,
    STATUS_SHUTTING_DOWN,
    STATUS_UNLOADING,
    STATUS_WAKING,
)


@dataclass(slots=True)
class WollmRuntimeData:
    """Runtime data stored per config entry."""

    entry: ConfigEntry
    client: WollmApiClient
    coordinator: DataUpdateCoordinator[WollmStatus | None]
    models: list[str] = field(default_factory=list)
    selected_model: str | None = None
    operation_state: str | None = None
    last_error: str | None = None
    last_health_raw: dict[str, Any] | None = None
    last_status_raw: dict[str, Any] | None = None

    @property
    def status(self) -> WollmStatus | None:
        """Return the last fetched WoLLM status."""
        return self.coordinator.data

    @property
    def is_online(self) -> bool:
        """Return whether the coordinator last succeeded."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def effective_status(self) -> str:
        """Return the synthesized server status."""
        if self.operation_state is not None:
            return self.operation_state
        if self.last_error is not None:
            return STATUS_ERROR
        if not self.is_online:
            return STATUS_OFFLINE
        return STATUS_RUNNING if self.status and self.status.current_model else STATUS_IDLE

    def clear_error(self) -> None:
        """Clear the last remembered action error."""
        self.last_error = None


class WollmDataUpdateCoordinator(DataUpdateCoordinator[WollmStatus | None]):
    """Poll WoLLM status at a configurable interval."""

    def __init__(self, hass: HomeAssistant, runtime: WollmRuntimeData) -> None:
        """Initialize coordinator."""
        scan_interval = runtime.entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name=f"{DOMAIN}_{runtime.entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.runtime = runtime

    async def _async_update_data(self) -> WollmStatus | None:
        """Fetch latest status from WoLLM."""
        try:
            status = await self.runtime.client.async_get_status()
            health = await self.runtime.client.async_health()
        except WollmAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except WollmConnectionError as err:
            raise UpdateFailed("WoLLM is offline") from err
        except WollmError as err:
            raise UpdateFailed(str(err)) from err

        self.runtime.last_health_raw = health
        self.runtime.last_status_raw = status.raw
        self.runtime.clear_error()
        if status.current_model:
            self.runtime.selected_model = status.current_model
        return status


async def async_build_runtime(hass: HomeAssistant, entry: ConfigEntry) -> WollmRuntimeData:
    """Create runtime data for a config entry."""
    session = async_get_clientsession(hass)
    client = WollmApiClient(
        session=session,
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        api_key=entry.data.get(CONF_API_KEY),
    )
    placeholder = WollmRuntimeData(entry=entry, client=client, coordinator=None)  # type: ignore[arg-type]
    coordinator = WollmDataUpdateCoordinator(hass, placeholder)
    runtime = WollmRuntimeData(entry=entry, client=client, coordinator=coordinator)
    coordinator.runtime = runtime
    try:
        await async_refresh_models(runtime)
    except WollmError as err:
        runtime.last_error = str(err)
    return runtime


async def async_refresh_models(runtime: WollmRuntimeData) -> list[str]:
    """Refresh cached model list from WoLLM."""
    try:
        models = await runtime.client.async_get_models()
    except WollmConnectionError:
        return runtime.models

    runtime.models = models
    if runtime.selected_model not in models:
        runtime.selected_model = runtime.status.current_model if runtime.status else None
    if runtime.selected_model not in models:
        runtime.selected_model = models[0] if models else None
    return runtime.models


@contextlib.asynccontextmanager
async def async_operation(runtime: WollmRuntimeData, state: str):
    """Set a transient operation state around an async action."""
    runtime.operation_state = state
    runtime.clear_error()
    runtime.coordinator.async_update_listeners()
    try:
        yield
    except Exception as err:
        runtime.operation_state = None
        runtime.last_error = str(err)
        runtime.coordinator.async_update_listeners()
        raise
    else:
        runtime.operation_state = None
        runtime.coordinator.async_update_listeners()


async def async_perform_wake(runtime: WollmRuntimeData) -> None:
    """Send a magic packet and wait for WoLLM health to come back."""
    timeout_seconds = runtime.entry.options.get(CONF_WAKE_TIMEOUT, DEFAULT_WAKE_TIMEOUT)
    async with async_operation(runtime, STATUS_WAKING):
        await runtime.coordinator.hass.async_add_executor_job(
            _send_magic_packet,
            runtime.entry.data[CONF_MAC_ADDRESS],
            runtime.entry.data[CONF_HOST],
        )
        await _async_wait_for_health(runtime.client, timeout_seconds)
        await async_refresh_models(runtime)
        await runtime.coordinator.async_request_refresh()


async def async_load_selected_model(runtime: WollmRuntimeData) -> None:
    """Load the currently selected model."""
    model_name = runtime.selected_model
    if not model_name:
        raise WollmNotFoundError("No model selected")
    async with async_operation(runtime, STATUS_LOADING):
        await runtime.client.async_load_model(model_name)
        await async_refresh_models(runtime)
        await runtime.coordinator.async_request_refresh()


async def async_unload_model(runtime: WollmRuntimeData) -> None:
    """Unload the current model."""
    async with async_operation(runtime, STATUS_UNLOADING):
        await runtime.client.async_unload()
        await runtime.coordinator.async_request_refresh()


async def async_shutdown(runtime: WollmRuntimeData, force: bool) -> None:
    """Shutdown the server host."""
    async with async_operation(runtime, STATUS_SHUTTING_DOWN):
        await runtime.client.async_shutdown(force=force)
        await asyncio.sleep(1)
        await runtime.coordinator.async_request_refresh()


async def async_set_runtime_settings(
    runtime: WollmRuntimeData,
    *,
    idle_timeout_minutes: int | None = None,
    shutdown_on_idle: bool | None = None,
    unload_on_idle: bool | None = None,
) -> None:
    """Update WoLLM runtime settings."""
    await runtime.client.async_set_runtime_settings(
        idle_timeout_minutes=idle_timeout_minutes,
        shutdown_on_idle=shutdown_on_idle,
        unload_on_idle=unload_on_idle,
    )
    await runtime.coordinator.async_request_refresh()


async def _async_wait_for_health(client: WollmApiClient, timeout_seconds: int) -> None:
    """Poll the health endpoint until it responds or timeout expires."""
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while True:
        try:
            await client.async_health()
            return
        except WollmConnectionError:
            if asyncio.get_running_loop().time() >= deadline:
                raise WollmTimeoutError("Wake timeout expired before WoLLM came online")
            await asyncio.sleep(5)


def _send_magic_packet(mac_address: str, host: str) -> None:
    """Send a Wake-on-LAN magic packet."""
    normalized = mac_address.replace("-", "").replace(":", "").lower()
    if len(normalized) != 12:
        raise ValueError("Invalid MAC address")

    payload = bytes.fromhex("ff" * 6 + normalized * 16)
    targets = {_guess_broadcast_address(host), "255.255.255.255"}

    for target in targets:
        for port in (9, 7):
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(payload, (target, port))


def _guess_broadcast_address(host: str) -> str:
    """Guess a broadcast address from the configured host when possible."""
    with contextlib.suppress(ValueError):
        ip = ipaddress.ip_address(host)
        if ip.version == 4:
            octets = host.split(".")
            octets[-1] = "255"
            return ".".join(octets)
    return "255.255.255.255"
