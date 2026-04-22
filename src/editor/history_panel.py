"""Right-side capture history panel — thumbnails + click-to-switch + delete."""

from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from src.core.history_manager import HistoryManager


class HistoryPanel(QWidget):
    item_activated = pyqtSignal(int)   # item id
    item_deleted = pyqtSignal(int)

    def __init__(self, history: HistoryManager, thumbnail_size: int = 96):
        super().__init__()
        self._history = history
        self._thumb_size = thumbnail_size

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self._list = QListWidget()
        self._list.setIconSize(QSize(thumbnail_size, thumbnail_size))
        self._list.setSpacing(3)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._show_menu)
        self._list.currentItemChanged.connect(self._on_selection)
        layout.addWidget(self._list)

        history.item_added.connect(self._on_added)
        history.item_removed.connect(self._on_removed)
        history.current_changed.connect(self._on_current_changed)
        history.item_image_updated.connect(self._on_image_updated)
        history.cleared.connect(self._list.clear)

        # seed from any existing items
        for it in history.items():
            self._on_added(it.id)

    def _on_added(self, item_id: int) -> None:
        cap = self._history.by_id(item_id)
        if cap is None:
            return
        icon = QIcon(cap.thumbnail(self._thumb_size))
        text = f"{cap.name}\n{cap.size_label()}"
        list_item = QListWidgetItem(icon, text)
        list_item.setData(Qt.ItemDataRole.UserRole, item_id)
        self._list.addItem(list_item)
        self._list.setCurrentItem(list_item)

    def _on_removed(self, item_id: int) -> None:
        for row in range(self._list.count()):
            if self._list.item(row).data(Qt.ItemDataRole.UserRole) == item_id:
                self._list.takeItem(row)
                return

    def _on_current_changed(self, item_id: int) -> None:
        for row in range(self._list.count()):
            if self._list.item(row).data(Qt.ItemDataRole.UserRole) == item_id:
                self._list.setCurrentRow(row)
                return

    def _on_image_updated(self, item_id: int) -> None:
        cap = self._history.by_id(item_id)
        if cap is None:
            return
        for row in range(self._list.count()):
            list_item = self._list.item(row)
            if list_item.data(Qt.ItemDataRole.UserRole) != item_id:
                continue
            list_item.setIcon(QIcon(cap.thumbnail(self._thumb_size)))
            list_item.setText(f"{cap.name}\n{cap.size_label()}")
            return

    def _on_selection(self, current, _previous) -> None:
        if current is None:
            return
        item_id = current.data(Qt.ItemDataRole.UserRole)
        self.item_activated.emit(item_id)

    def _show_menu(self, pos) -> None:
        item = self._list.itemAt(pos)
        if item is None:
            return
        item_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        delete = menu.addAction("삭제")
        action = menu.exec(self._list.mapToGlobal(pos))
        if action is delete:
            self.item_deleted.emit(item_id)
