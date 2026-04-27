"""Update checker version comparison behavior."""

from __future__ import annotations

from src.core.update_checker import is_newer_version, normalize_version


def test_normalize_version_ignores_prefixes() -> None:
    """Version normalization strips non-numeric tag prefixes."""
    assert normalize_version("v0.1.1") == (0, 1, 1)


def test_is_newer_version_compares_numeric_parts() -> None:
    """Latest release versions compare by numeric components."""
    assert is_newer_version("0.1.2", "0.1.1") is True
    assert is_newer_version("0.1.1", "0.1.1") is False
    assert is_newer_version("0.1", "0.1.1") is False
