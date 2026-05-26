"""Editor status bar with image size, zoom, and status text."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QStatusBar


class EditorStatusBar(QStatusBar):
    def __init__(self):
        super().__init__()
        self._size = QLabel("-- x -- px")
        self._zoom = QLabel("100%")
        self._info = QLabel("")
        self.addPermanentWidget(self._info, 1)
        self.addPermanentWidget(self._zoom)
        self.addPermanentWidget(self._size)

    def set_size(self, width: int, height: int) -> None:
        self._size.setText(f"{width} x {height} px")

    def set_info(self, text: str) -> None:
        self._info.setText(text)

    def set_zoom(self, percent: int) -> None:
        self._zoom.setText(f"{int(percent)}%")
