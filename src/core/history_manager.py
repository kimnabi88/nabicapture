"""In-memory capture history. Single source of truth for UI panels."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from itertools import count
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

_id_counter = count(1)


@dataclass
class CaptureItem:
    image: QImage
    created_at: datetime = field(default_factory=datetime.now)
    saved_path: Path | None = None
    name: str = ""
    id: int = field(default_factory=lambda: next(_id_counter))

    def size_label(self) -> str:
        return f"{self.image.width()} × {self.image.height()} px"

    def thumbnail(self, max_side: int) -> QPixmap:
        return QPixmap.fromImage(
            self.image.scaled(
                max_side, max_side,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )


class HistoryManager(QObject):
    item_added = pyqtSignal(int)       # item id
    item_removed = pyqtSignal(int)
    current_changed = pyqtSignal(int)  # -1 if none
    item_image_updated = pyqtSignal(int)   # image replaced in-place
    cleared = pyqtSignal()

    def __init__(self, max_items: int = 50):
        super().__init__()
        self._items: list[CaptureItem] = []
        self._current_id: int = -1
        self._max_items = max_items

    def set_max_items(self, n: int) -> None:
        self._max_items = max(1, n)
        self._trim()

    def add(self, item: CaptureItem) -> int:
        if not item.name:
            item.name = item.created_at.strftime("%H:%M:%S")
        self._items.append(item)
        self._trim()
        self.item_added.emit(item.id)
        self.set_current(item.id)
        return item.id

    def remove(self, item_id: int) -> None:
        for i, it in enumerate(self._items):
            if it.id == item_id:
                del self._items[i]
                self.item_removed.emit(item_id)
                if self._current_id == item_id:
                    new_id = self._items[-1].id if self._items else -1
                    self.set_current(new_id)
                return

    def clear(self) -> None:
        self._items.clear()
        self._current_id = -1
        self.cleared.emit()

    def items(self) -> list[CaptureItem]:
        return list(self._items)

    def by_id(self, item_id: int) -> CaptureItem | None:
        return next((it for it in self._items if it.id == item_id), None)

    def update_image(self, item_id: int, image: QImage) -> None:
        it = self.by_id(item_id)
        if it is None:
            return
        it.image = image
        self.item_image_updated.emit(item_id)

    def current(self) -> CaptureItem | None:
        return self.by_id(self._current_id)

    def set_current(self, item_id: int) -> None:
        if item_id != self._current_id:
            self._current_id = item_id
            self.current_changed.emit(item_id)

    def _trim(self) -> None:
        while len(self._items) > self._max_items:
            dropped = self._items.pop(0)
            self.item_removed.emit(dropped.id)
            if self._current_id == dropped.id:
                self._current_id = self._items[-1].id if self._items else -1
                self.current_changed.emit(self._current_id)
