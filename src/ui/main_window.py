"""Main capture menu window opened from the tray."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src import __app_name__, __version__

CAPTURE_ACTIONS = [
    ("region", "Region", "Drag to capture a rectangular area"),
    ("window", "Window", "Pick a window to capture"),
    ("monitor", "Monitor", "Capture one monitor"),
    ("fullscreen", "Full", "Capture all monitors"),
    ("fixed_size", "Fixed", "Capture a fixed-size area"),
    ("scroll", "Scroll", "Planned"),
]


class MainWindow(QMainWindow):
    capture_requested = pyqtSignal(str)
    settings_requested = pyqtSignal()
    close_intent = pyqtSignal()

    def __init__(self, close_behavior: str = "minimize"):
        super().__init__()
        self._close_behavior = close_behavior
        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.setObjectName("MainMenu")
        self.setFixedSize(760, 128)
        self._build_ui()

    def set_close_behavior(self, behavior: str) -> None:
        """Set whether the close button hides or exits the app."""
        self._close_behavior = behavior

    def _build_ui(self) -> None:
        """Build the capture menu and settings button."""
        central = QWidget()
        central.setObjectName("MainMenuCentral")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 10, 16, 12)
        root.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel(__app_name__)
        title.setObjectName("MenuTitle")
        subtitle = QLabel("Screen capture")
        subtitle.setObjectName("MenuSubtitle")
        header.addWidget(title)
        header.addSpacing(8)
        header.addWidget(subtitle)
        header.addStretch(1)

        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("MenuSettings")
        settings_btn.setFixedWidth(78)
        settings_btn.clicked.connect(self.settings_requested.emit)
        header.addWidget(settings_btn)
        root.addLayout(header)

        row = QHBoxLayout()
        row.setSpacing(6)
        for mode, label, tip in CAPTURE_ACTIONS:
            btn = QPushButton(label)
            btn.setObjectName("MenuAction")
            btn.setToolTip(tip)
            btn.setMinimumHeight(42)
            if mode == "scroll":
                btn.setEnabled(False)
            btn.clicked.connect(lambda _=False, m=mode: self.capture_requested.emit(m))
            row.addWidget(btn, 1)
        root.addLayout(row)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """Route X button to tray hide or real quit."""
        if self._close_behavior == "minimize":
            event.ignore()
            self.hide()
        else:
            self.close_intent.emit()
            event.accept()

    def force_close(self) -> None:
        """Force a real close during application quit."""
        self._close_behavior = "quit"
        self.close()
