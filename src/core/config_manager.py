"""Config load/save/merge. Single source of truth for all settings."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

from src.utils import logger, paths

log = logger.get(__name__)


def _deep_merge(base: dict, override: dict) -> dict:
    """Override wins but missing keys are filled from base (recursive)."""
    result = deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


class ConfigManager(QObject):
    """Holds a merged config dict and persists user overrides."""

    changed = pyqtSignal(str)  # section name that changed

    def __init__(self, default_path: Path | None = None, user_path: Path | None = None):
        super().__init__()
        self._default_path = default_path or paths.default_config_file()
        self._user_path = user_path or paths.config_file()
        self._default: dict[str, Any] = {}
        self._data: dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        self._default = self._read_json(self._default_path)
        user = self._read_json(self._user_path) if self._user_path.exists() else {}
        self._data = _deep_merge(self._default, user)

    @staticmethod
    def _read_json(path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            log.warning("config file missing: %s", path)
            return {}
        except json.JSONDecodeError as exc:
            log.error("config parse error %s: %s", path, exc)
            return {}

    def get(self, section: str, key: str | None = None, default: Any = None) -> Any:
        """`get("save")` → dict. `get("save", "format")` → value."""
        sect = self._data.get(section, {})
        if key is None:
            return deepcopy(sect)
        return sect.get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        self._data.setdefault(section, {})[key] = value
        self.changed.emit(section)

    def update_section(self, section: str, patch: dict) -> None:
        merged = _deep_merge(self._data.get(section, {}), patch)
        self._data[section] = merged
        self.changed.emit(section)

    def save(self) -> None:
        """Persist only the diff vs default to keep config.json minimal."""
        diff = self._diff(self._default, self._data)
        self._user_path.write_text(
            json.dumps(diff, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def _diff(base: dict, current: dict) -> dict:
        out: dict[str, Any] = {}
        for key, val in current.items():
            if key not in base:
                out[key] = val
            elif isinstance(val, dict) and isinstance(base[key], dict):
                sub = ConfigManager._diff(base[key], val)
                if sub:
                    out[key] = sub
            elif val != base[key]:
                out[key] = val
        return out

    def reset_to_defaults(self) -> None:
        self._data = deepcopy(self._default)
        self.changed.emit("*")
