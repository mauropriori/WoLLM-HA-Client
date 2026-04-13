"""API client for WoLLM."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any
from urllib.parse import urlencode

import aiohttp


class WollmError(Exception):
    """Base WoLLM exception."""


class WollmConnectionError(WollmError):
    """Raised when the WoLLM server cannot be reached."""


class WollmAuthError(WollmError):
    """Raised when authentication fails."""


class WollmNotFoundError(WollmError):
    """Raised when a requested model or endpoint does not exist."""


class WollmTimeoutError(WollmError):
    """Raised when WoLLM reports a startup timeout or request timeout."""


class WollmBadRequestError(WollmError):
    """Raised when WoLLM rejects a request."""


@dataclass(slots=True)
class WollmStatus:
    """Normalized WoLLM status payload."""

    current_model: str | None
    load_status: str | None
    shutdown_on_idle: bool
    unload_on_idle: bool
    idle_timeout_minutes: int | None
    idle_seconds: int | None
    wol_boot: bool | None
    cpu_count: int | None
    gpu_count: int | None
    ram_used_mb: int | None
    ram_total_mb: int | None
    raw: dict[str, Any]


class WollmApiClient:
    """Simple async client for the WoLLM REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        api_key: str | None = None,
        request_timeout: int = 15,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._base_url = f"http://{host}:{port}"
        self._api_key = api_key or None
        self._request_timeout = aiohttp.ClientTimeout(total=request_timeout)

    @property
    def base_url(self) -> str:
        """Return the base URL for the server."""
        return self._base_url

    async def async_health(self) -> dict[str, Any]:
        """Fetch health status."""
        return await self._request("get", "/health")

    async def async_get_status(self) -> WollmStatus:
        """Fetch and normalize WoLLM status."""
        payload = await self._request("get", "/status")
        system = payload.get("system", {})
        gpus = system.get("gpus")
        return WollmStatus(
            current_model=payload.get("currentModel"),
            load_status=payload.get("loadStatus"),
            shutdown_on_idle=bool(payload.get("shutdownOnIdle", False)),
            unload_on_idle=bool(payload.get("unloadOnIdle", True)),
            idle_timeout_minutes=payload.get("idleTimeoutMinutes"),
            idle_seconds=payload.get("idleSeconds"),
            wol_boot=payload.get("wolBoot"),
            cpu_count=system.get("cpus"),
            gpu_count=len(gpus) if isinstance(gpus, list) else None,
            ram_used_mb=system.get("ramUsedMb"),
            ram_total_mb=system.get("ramTotalMb"),
            raw=payload,
        )

    async def async_get_models(self) -> list[str]:
        """Fetch configured model names."""
        payload = await self._request("get", "/models")
        return [
            model["name"]
            for model in payload.get("models", [])
            if isinstance(model, dict) and model.get("name")
        ]

    async def async_set_runtime_settings(
        self,
        *,
        idle_timeout_minutes: int | None = None,
        shutdown_on_idle: bool | None = None,
        unload_on_idle: bool | None = None,
    ) -> dict[str, Any]:
        """Update WoLLM runtime settings through the /set endpoint."""
        params: dict[str, str | int] = {}
        if idle_timeout_minutes is not None:
            params["idleTimeoutMinutes"] = idle_timeout_minutes
        if shutdown_on_idle is not None:
            params["shutdown_on_idle"] = str(shutdown_on_idle).lower()
        if unload_on_idle is not None:
            params["unload_on_idle"] = str(unload_on_idle).lower()

        suffix = f"?{urlencode(params)}" if params else ""
        return await self._request("post", f"/set{suffix}")

    async def async_load_model(self, model_name: str) -> dict[str, Any]:
        """Load a specific model."""
        return await self._request("post", f"/load/{model_name}")

    async def async_unload(self) -> dict[str, Any]:
        """Unload the current model."""
        return await self._request("post", "/unload")

    async def async_shutdown(self, force: bool = False) -> dict[str, Any]:
        """Request system shutdown."""
        suffix = "?forceShutdown=true" if force else ""
        return await self._request("post", f"/shutdown{suffix}")

    async def _request(self, method: str, path: str) -> dict[str, Any]:
        """Perform an HTTP request against the WoLLM server."""
        headers = {}
        if self._api_key:
            headers["X-Api-Key"] = self._api_key

        try:
            async with self._session.request(
                method,
                f"{self._base_url}{path}",
                headers=headers,
                timeout=self._request_timeout,
            ) as response:
                return await self._handle_response(response)
        except WollmError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise WollmConnectionError("Unable to connect to WoLLM") from err

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict[str, Any]:
        """Translate HTTP responses into domain exceptions."""
        try:
            payload = await response.json(content_type=None)
        except aiohttp.ContentTypeError:
            payload = {}
        except ValueError:
            payload = {}

        if response.status == HTTPStatus.UNAUTHORIZED:
            raise WollmAuthError(payload.get("error", "Unauthorized"))
        if response.status == HTTPStatus.NOT_FOUND:
            raise WollmNotFoundError(payload.get("error", "Resource not found"))
        if response.status == HTTPStatus.BAD_REQUEST:
            raise WollmBadRequestError(payload.get("error", "Bad request"))
        if response.status == HTTPStatus.GATEWAY_TIMEOUT:
            raise WollmTimeoutError(payload.get("detail", "Startup timeout"))
        if response.status >= HTTPStatus.BAD_REQUEST:
            raise WollmError(
                payload.get("error")
                or payload.get("detail")
                or f"WoLLM returned HTTP {response.status}"
            )

        return payload
