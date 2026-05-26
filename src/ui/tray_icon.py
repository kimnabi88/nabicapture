"""System tray icon with app controls."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from src import __app_name__


def magnifier_icon(size: int = 32) -> QIcon:
    """Return a painter-drawn magnifying-glass fallback icon."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    scale = size / 32.0
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    lens_pen = QPen(QColor("#2f7fe6"))
    lens_pen.setWidth(max(2, int(3 * scale)))
    painter.setPen(lens_pen)
    painter.setBrush(QColor(255, 255, 255, 220))
    painter.drawEllipse(QPoint(int(13 * scale), int(13 * scale)), int(8 * scale), int(8 * scale))
    handle_pen = QPen(QColor("#2f7fe6"))
    handle_pen.setWidth(max(3, int(4 * scale)))
    handle_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(handle_pen)
    painter.drawLine(int(19 * scale), int(19 * scale), int(28 * scale), int(28 * scale))
    painter.end()
    return QIcon(pix)


def load_app_icon() -> QIcon:
    """Load icon.ico from resources if available, else use a fallback icon."""
    from src.utils.paths import icons_dir

    ico = icons_dir() / "icon.ico"
    if ico.exists():
        return QIcon(str(ico))
    return magnifier_icon(32)


class TrayIcon(QSystemTrayIcon):
    show_main_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, icon: QIcon | None = None):
        super().__init__(icon or load_app_icon())
        self.setToolTip(__app_name__)
        menu = QMenu()

        show_act = QAction("Open", menu)
        show_act.triggered.connect(self.show_main_requested.emit)
        menu.addAction(show_act)

        menu.addSeparator()

        quit_act = QAction("Quit", menu)
        quit_act.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_act)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason) -> None:
        """Open the app window on normal tray activation."""
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_main_requested.emit()
