"""Path resolution — portable. Works for dev and PyInstaller frozen .exe."""

from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    """Return the folder where the executable / main script lives."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def resource_root() -> Path:
    """Bundled resources — differ for PyInstaller onefile mode."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return app_root()


def config_file() -> Path:
    """User config lives next to the executable so it's portable."""
    return app_root() / "config.json"


def default_config_file() -> Path:
    """Bundled default config shipped with the app."""
    return resource_root() / "config" / "default_config.json"


def styles_file() -> Path:
    return resource_root() / "resources" / "styles" / "main.qss"


def icons_dir() -> Path:
    return resource_root() / "resources" / "icons"


def captures_dir(relative: str) -> Path:
    """Resolve save directory. Relative paths anchor to app_root()."""
    p = Path(relative)
    if not p.is_absolute():
        p = app_root() / p
    p.mkdir(parents=True, exist_ok=True)
    return p
