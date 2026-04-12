"""Validation tests for the WoLLM config flow."""

from __future__ import annotations

import pytest

from custom_components.wollm.config_flow import _normalize_mac, _validate_mac


def test_validate_mac() -> None:
    """MAC validation should accept common formats."""
    assert _validate_mac("AA:BB:CC:DD:EE:FF")
    assert _validate_mac("AA-BB-CC-DD-EE-FF")
    assert _validate_mac("aabbccddeeff")
    assert not _validate_mac("not-a-mac")


def test_normalize_mac() -> None:
    """MAC normalization should persist a colon-separated lowercase value."""
    assert _normalize_mac("AA-BB-CC-DD-EE-FF") == "aa:bb:cc:dd:ee:ff"
