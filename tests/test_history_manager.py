"""HistoryManager: add/remove/trim/current."""

from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PyQt6.QtCore")

from PyQt6.QtGui import QImage  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from src.core.history_manager import CaptureItem, HistoryManager  # noqa: E402

_app = QApplication.instance() or QApplication(sys.argv)


def _img(w: int = 20, h: int = 10) -> QImage:
    img = QImage(w, h, QImage.Format.Format_ARGB32)
    img.fill(0xFF0000FF)
    return img


def test_add_emits_and_becomes_current():
    h = HistoryManager(max_items=5)
    added: list[int] = []
    current: list[int] = []
    h.item_added.connect(added.append)
    h.current_changed.connect(current.append)
    item_id = h.add(CaptureItem(image=_img()))
    assert added == [item_id]
    assert current[-1] == item_id
    assert h.current().id == item_id


def test_remove_current_falls_back():
    h = HistoryManager(max_items=5)
    a = h.add(CaptureItem(image=_img()))
    b = h.add(CaptureItem(image=_img()))
    h.remove(b)
    assert h.current().id == a


def test_trim_to_max():
    h = HistoryManager(max_items=2)
    ids = [h.add(CaptureItem(image=_img())) for _ in range(3)]
    remaining = [it.id for it in h.items()]
    assert len(remaining) == 2
    assert ids[-2:] == remaining


def test_size_label_matches_image():
    item = CaptureItem(image=_img(123, 45))
    assert "123" in item.size_label()
    assert "45" in item.size_label()
