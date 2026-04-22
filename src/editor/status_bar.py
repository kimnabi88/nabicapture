"""Editor status bar — shows W×H px and zoom/cursor info."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QStatusBar


class EditorStatusBar(QStatusBar):
    def __init__(self):
        super().__init__()
        self._size = QLabel("— × — px")
        self._info = QLabel("")
        self.addPermanentWidget(self._info, 1)
        self.addPermanentWidget(self._size)

    def set_size(self, width: int, height: int) -> None:
        self._size.setText(f"{width} × {height} px")

    def set_info(self, text: str) -> None:
        self._info.setText(text)
