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
