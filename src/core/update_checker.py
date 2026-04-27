"""GitHub release update checks for NabiCapture."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class UpdateInfo:
    """Result of a GitHub release update check."""

    current_version: str
    latest_version: str
    release_url: str
    is_update_available: bool


def normalize_version(value: str) -> tuple[int, ...]:
    """Convert a version string like v1.2.3 into comparable integers."""
    numbers = re.findall(r"\d+", value)
    return tuple(int(part) for part in numbers) if numbers else (0,)


def is_newer_version(latest: str, current: str) -> bool:
    """Return whether latest is greater than current using numeric parts."""
    latest_parts = normalize_version(latest)
    current_parts = normalize_version(current)
    width = max(len(latest_parts), len(current_parts))
    latest_parts += (0,) * (width - len(latest_parts))
    current_parts += (0,) * (width - len(current_parts))
    return latest_parts > current_parts


def check_latest_release(api_url: str, current_version: str, timeout: float = 5.0) -> UpdateInfo:
    """Fetch GitHub's latest release metadata and compare versions."""
    request = Request(api_url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "NabiCapture",
    })
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(str(exc)) from exc

    tag_name = str(payload.get("tag_name", "") or "")
    latest_version = tag_name.lstrip("v") or current_version
    release_url = str(payload.get("html_url", "") or "")
    return UpdateInfo(
        current_version=current_version,
        latest_version=latest_version,
        release_url=release_url,
        is_update_available=is_newer_version(latest_version, current_version),
    )
