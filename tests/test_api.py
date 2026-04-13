"""Basic API client tests for WoLLM."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.wollm.api import (
    WollmApiClient,
    WollmAuthError,
    WollmBadRequestError,
    WollmNotFoundError,
    WollmTimeoutError,
)


@pytest.mark.asyncio
async def test_get_models_parses_payload() -> None:
    """The client should return a flat list of model names."""
    session = Mock()
    client = WollmApiClient(session, "127.0.0.1", 8080)
    client._request = AsyncMock(  # type: ignore[method-assign]
        return_value={"models": [{"name": "mistral"}, {"name": "sdxl"}]}
    )

    models = await client.async_get_models()

    assert models == ["mistral", "sdxl"]


@pytest.mark.asyncio
async def test_get_status_parses_server_020_payload() -> None:
    """The client should normalize the WoLLM 0.2.0 status payload."""
    session = Mock()
    client = WollmApiClient(session, "127.0.0.1", 8080)
    client._request = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "currentModel": "mistral",
            "loadStatus": "loaded",
            "shutdownOnIdle": True,
            "unloadOnIdle": False,
            "idleTimeoutMinutes": 10,
            "idleSeconds": 42,
            "wolBoot": True,
            "system": {
                "cpus": 16,
                "ramUsedMb": 4096,
                "ramTotalMb": 32768,
                "gpus": [{"name": "RTX 4090"}],
            },
        }
    )

    status = await client.async_get_status()

    assert status.current_model == "mistral"
    assert status.load_status == "loaded"
    assert status.shutdown_on_idle is True
    assert status.unload_on_idle is False
    assert status.idle_timeout_minutes == 10
    assert status.idle_seconds == 42
    assert status.wol_boot is True
    assert status.cpu_count == 16
    assert status.gpu_count == 1
    assert status.ram_used_mb == 4096
    assert status.ram_total_mb == 32768


@pytest.mark.asyncio
async def test_set_runtime_settings_calls_new_set_endpoint() -> None:
    """Runtime settings updates should use the WoLLM 0.2.0 /set endpoint."""
    session = Mock()
    client = WollmApiClient(session, "127.0.0.1", 8080)
    client._request = AsyncMock(return_value={"status": "ok"})  # type: ignore[method-assign]

    await client.async_set_runtime_settings(
        idle_timeout_minutes=5,
        shutdown_on_idle=True,
        unload_on_idle=False,
    )

    client._request.assert_awaited_once_with(
        "post",
        "/set?idleTimeoutMinutes=5&shutdown_on_idle=true&unload_on_idle=false",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, WollmAuthError),
        (404, WollmNotFoundError),
        (400, WollmBadRequestError),
        (504, WollmTimeoutError),
    ],
)
async def test_handle_response_maps_errors(status: int, expected: type[Exception]) -> None:
    """HTTP error codes should map to custom exceptions."""
    session = Mock()
    client = WollmApiClient(session, "127.0.0.1", 8080)
    response = Mock(status=status)
    response.json = AsyncMock(return_value={"error": "boom", "detail": "boom"})

    with pytest.raises(expected):
        await client._handle_response(response)  # type: ignore[arg-type]
