"""image_io: filename pattern + format-specific save."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PyQt6.QtCore")

from PyQt6.QtGui import QImage  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from src.utils.image_io import _fill_pattern, _unique, save_image  # noqa: E402

_app = QApplication.instance() or QApplication(sys.argv)


def test_fill_pattern_replaces_known_tokens():
    out = _fill_pattern("cap_{yyyy}{MM}{dd}_{HH}{mm}{ss}")
    assert len(out) == len("cap_20260421_120000")
    assert out.startswith("cap_")


def test_unique_adds_suffix_on_collision(tmp_path: Path):
    (tmp_path / "a.png").write_bytes(b"x")
    result = _unique(tmp_path / "a.png")
    assert result.name == "a_2.png"


def test_save_image_png(tmp_path: Path):
    img = QImage(5, 5, QImage.Format.Format_ARGB32)
    img.fill(0xFF00FF00)
    cfg = {
        "directory": str(tmp_path),
        "format": "png",
        "quality": 90,
        "filename_pattern": "t_{HH}{mm}{ss}",
    }
    path = save_image(img, cfg)
    assert path.exists()
    assert path.suffix == ".png"


def test_save_image_jpeg(tmp_path: Path):
    img = QImage(5, 5, QImage.Format.Format_ARGB32)
    img.fill(0xFFFFFFFF)
    cfg = {
        "directory": str(tmp_path),
        "format": "jpg",
        "quality": 80,
        "filename_pattern": "t_{HH}{mm}{ss}",
    }
    path = save_image(img, cfg)
    assert path.exists()
    assert path.suffix == ".jpg"
