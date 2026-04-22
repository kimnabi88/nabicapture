"""Main window — single-row capture bar, settings button, light theme."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src import __app_name__

CAPTURE_ACTIONS = [
    ("region", "직접지정", "드래그로 사각 영역 캡쳐"),
    ("window", "창", "창 클릭으로 선택 캡쳐"),
    ("monitor", "단위영역", "모니터 단위 캡쳐"),
    ("fullscreen", "전체화면", "모든 모니터 캡쳐"),
    ("fixed_size", "크기지정", "W×H 지정 후 위치 이동으로 캡쳐"),
    ("scroll", "스크롤", "(2단계 예정)"),
]


class MainWindow(QMainWindow):
    capture_requested = pyqtSignal(str)     # capture mode id
    settings_requested = pyqtSignal()
    close_intent = pyqtSignal()             # true close (tray may intercept X)

    def __init__(self, close_behavior: str = "minimize"):
        super().__init__()
        self._close_behavior = close_behavior
        self.setWindowTitle(__app_name__)
        self.setObjectName("MainMenu")
        self.setFixedSize(760, 128)
        self._build_ui()

    def set_close_behavior(self, behavior: str) -> None:
        self._close_behavior = behavior

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("MainMenuCentral")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 10, 16, 12)
        root.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel(f"{__app_name__}")
        title.setObjectName("MenuTitle")
        subtitle = QLabel("가벼운 화면 캡쳐")
        subtitle.setObjectName("MenuSubtitle")
        header.addWidget(title)
        header.addSpacing(8)
        header.addWidget(subtitle)
        header.addStretch(1)
        settings_btn = QPushButton("설정")
        settings_btn.setObjectName("MenuSettings")
        settings_btn.setFixedWidth(68)
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

    # X click routing
    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (Qt naming)
        if self._close_behavior == "minimize":
            event.ignore()
            self.hide()
        else:
            self.close_intent.emit()
            event.accept()

    def force_close(self) -> None:
        self._close_behavior = "quit"
        self.close()
