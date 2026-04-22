"""Inline color palette + custom picker with a large current-color indicator."""

from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QWidget,
)


class _CurrentSwatch(QFrame):
    """Big square that always shows the currently selected color."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(QSize(32, 32))
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._color = QColor("#000000")
        self._refresh()

    def set_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self._refresh()

    def _refresh(self) -> None:
        self.setStyleSheet(
            f"background-color: {self._color.name()};"
            " border: 2px solid #2f7fe6;"
            " border-radius: 6px;"
        )
        self.setToolTip(f"현재 색상: {self._color.name().upper()}")


class ColorPicker(QWidget):
    color_changed = pyqtSignal(QColor)

    def __init__(self, colors: list[str], initial: str | None = None):
        super().__init__()
        self._current = QColor(initial or (colors[0] if colors else "#000000"))
        self._buttons: dict[str, QPushButton] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._swatch = _CurrentSwatch()
        self._swatch.set_color(self._current)
        layout.addWidget(self._swatch)
        layout.addSpacing(6)

        for hex_ in colors:
            btn = QPushButton()
            btn.setFixedSize(QSize(20, 20))
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, h=hex_: self._choose(QColor(h)))
            self._buttons[hex_.upper()] = btn
            layout.addWidget(btn)

        more = QPushButton("···")
        more.setFixedSize(QSize(28, 20))
        more.setToolTip("사용자 지정 색상")
        more.clicked.connect(self._open_dialog)
        layout.addWidget(more)

        self._apply_styles()

    def current(self) -> QColor:
        return QColor(self._current)

    def _choose(self, color: QColor) -> None:
        self._current = color
        self._swatch.set_color(color)
        self._apply_styles()
        self.color_changed.emit(color)

    def _open_dialog(self) -> None:
        c = QColorDialog.getColor(self._current, self, "색상 선택")
        if c.isValid():
            self._choose(c)

    def _apply_styles(self) -> None:
        sel_hex = self._current.name().upper()
        for hex_, btn in self._buttons.items():
            selected = (hex_ == sel_hex)
            btn.setChecked(selected)
            border = "2px solid #111" if selected else "1px solid #bbb"
            btn.setStyleSheet(
                f"QPushButton {{"
                f" background-color: {hex_};"
                f" border: {border};"
                f" border-radius: 10px;"
                f"}}"
                f"QPushButton:hover {{ border: 2px solid #2f7fe6; }}"
            )
