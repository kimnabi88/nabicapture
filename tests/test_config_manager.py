"""ConfigManager: default merge, patch, save-as-diff."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PyQt6.QtCore")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from src.core.config_manager import ConfigManager, _deep_merge  # noqa: E402

_app = QApplication.instance() or QApplication(sys.argv)


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_deep_merge_basic():
    out = _deep_merge(
        {"a": 1, "b": {"x": 2, "y": 3}, "c": 4},
        {"b": {"y": 30}, "d": 5},
    )
    assert out == {"a": 1, "b": {"x": 2, "y": 30}, "c": 4, "d": 5}


def test_load_merges_user_over_default(tmp_path: Path):
    default = tmp_path / "default.json"
    user = tmp_path / "user.json"
    _write(default, {"save": {"format": "png", "quality": 95}})
    _write(user, {"save": {"quality": 80}})
    cm = ConfigManager(default_path=default, user_path=user)
    assert cm.get("save", "format") == "png"
    assert cm.get("save", "quality") == 80


def test_missing_user_file_falls_back_to_default(tmp_path: Path):
    default = tmp_path / "default.json"
    user = tmp_path / "missing.json"
    _write(default, {"save": {"format": "png"}})
    cm = ConfigManager(default_path=default, user_path=user)
    assert cm.get("save", "format") == "png"


def test_save_writes_only_diff(tmp_path: Path):
    default = tmp_path / "default.json"
    user = tmp_path / "user.json"
    _write(default, {"save": {"format": "png", "quality": 95},
                     "startup": {"close_behavior": "minimize"}})
    cm = ConfigManager(default_path=default, user_path=user)
    cm.set("save", "quality", 60)
    cm.save()
    stored = json.loads(user.read_text(encoding="utf-8"))
    assert stored == {"save": {"quality": 60}}


def test_reset_restores_default(tmp_path: Path):
    default = tmp_path / "default.json"
    user = tmp_path / "user.json"
    _write(default, {"save": {"quality": 95}})
    _write(user, {"save": {"quality": 40}})
    cm = ConfigManager(default_path=default, user_path=user)
    assert cm.get("save", "quality") == 40
    cm.reset_to_defaults()
    assert cm.get("save", "quality") == 95


def test_update_section_patches_and_keeps_others(tmp_path: Path):
    default = tmp_path / "default.json"
    user = tmp_path / "user.json"
    _write(default, {"hotkeys": {"region": "ctrl+shift+a", "window": "ctrl+shift+w"}})
    cm = ConfigManager(default_path=default, user_path=user)
    cm.update_section("hotkeys", {"region": "ctrl+alt+a"})
    assert cm.get("hotkeys", "region") == "ctrl+alt+a"
    assert cm.get("hotkeys", "window") == "ctrl+shift+w"
