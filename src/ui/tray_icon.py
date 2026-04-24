"""System tray icon with a minimal context menu."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from src import __app_name__


def magnifier_icon(size: int = 32) -> QIcon:
    """Fallback painter-drawn magnifying-glass icon."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    s = size / 32.0
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    lens_pen = QPen(QColor("#2f7fe6"))
    lens_pen.setWidth(max(2, int(3 * s)))
    p.setPen(lens_pen)
    p.setBrush(QColor(255, 255, 255, 220))
    p.drawEllipse(QPoint(int(13 * s), int(13 * s)), int(8 * s), int(8 * s))
    handle_pen = QPen(QColor("#2f7fe6"))
    handle_pen.setWidth(max(3, int(4 * s)))
    handle_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(handle_pen)
    p.drawLine(int(19 * s), int(19 * s), int(28 * s), int(28 * s))
    p.end()
    return QIcon(pix)


def load_app_icon() -> QIcon:
    """Load icon.ico from resources if available, else programmatic fallback."""
    from src.utils.paths import icons_dir
    ico = icons_dir() / "icon.ico"
    if ico.exists():
        return QIcon(str(ico))
    return magnifier_icon(32)


def _fallback_icon() -> QIcon:
    return load_app_icon()


class TrayIcon(QSystemTrayIcon):
    show_main_requested = pyqtSignal()
    capture_requested = pyqtSignal(str)
    reconnect_hotkeys_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, icon: QIcon | None = None):
        super().__init__(icon or _fallback_icon())
        self.setToolTip(__app_name__)
        menu = QMenu()

        show_act = QAction("열기", menu)
        show_act.triggered.connect(self.show_main_requested.emit)
        menu.addAction(show_act)

        menu.addSeparator()

        for mode, label in (
            ("region", "직접지정 캡쳐"),
            ("fullscreen", "전체화면 캡쳐"),
            ("monitor", "모니터 캡쳐"),
        ):
            act = QAction(label, menu)
            act.triggered.connect(lambda _=False, m=mode: self.capture_requested.emit(m))
            menu.addAction(act)

        menu.addSeparator()

        reconnect_act = QAction("단축키 재등록", menu)
        reconnect_act.triggered.connect(self.reconnect_hotkeys_requested.emit)
        menu.addAction(reconnect_act)

        quit_act = QAction("종료", menu)
        quit_act.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_act)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_main_requested.emit()
