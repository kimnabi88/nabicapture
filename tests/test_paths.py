"""paths: app_root, captures_dir relative-path anchoring."""

from __future__ import annotations

from pathlib import Path

from src.utils import paths


def test_app_root_returns_existing_directory():
    root = paths.app_root()
    assert isinstance(root, Path)
    assert root.exists()


def test_default_config_file_is_inside_root():
    root = paths.resource_root()
    cfg = paths.default_config_file()
    assert cfg.is_relative_to(root)


def test_captures_dir_anchors_relative_to_root(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    out = paths.captures_dir("./captures")
    assert out == tmp_path / "captures"
    assert out.exists() and out.is_dir()


def test_captures_dir_respects_absolute(tmp_path: Path):
    target = tmp_path / "abs"
    out = paths.captures_dir(str(target))
    assert out == target
    assert out.exists()
