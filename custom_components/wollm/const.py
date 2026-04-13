"""Constants for the WoLLM integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "wollm"

CONF_MAC_ADDRESS: Final = "mac_address"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_WAKE_TIMEOUT: Final = "wake_timeout"

DEFAULT_PORT: Final = 8080
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_WAKE_TIMEOUT: Final = 180

MANUFACTURER: Final = "WoLLM"
MODEL: Final = "WoLLM Server"

ATTR_ENTRY_ID: Final = "entry_id"
ATTR_FORCE: Final = "force"
ATTR_MODEL: Final = "model"

SERVICE_WAKE: Final = "wake"
SERVICE_LOAD_MODEL: Final = "load_model"
SERVICE_UNLOAD_MODEL: Final = "unload_model"
SERVICE_SHUTDOWN: Final = "shutdown"
SERVICE_REFRESH_MODELS: Final = "refresh_models"

SERVICES_REGISTERED: Final = "services_registered"

STATUS_OFFLINE: Final = "offline"
STATUS_IDLE: Final = "idle"
STATUS_RUNNING: Final = "running"
STATUS_WAKING: Final = "waking"
STATUS_LOADING: Final = "loading"
STATUS_UNLOADING: Final = "unloading"
STATUS_SHUTTING_DOWN: Final = "shutting_down"
STATUS_ERROR: Final = "error"

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
