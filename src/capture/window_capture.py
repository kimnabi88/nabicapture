"""Click-to-select window capture via Win32 EnumWindows."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QPoint, QRect, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QCursor,
    QGuiApplication,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
    QShowEvent,
)
from PyQt6.QtWidgets import QWidget

from src.capture.screen_capture import Rect
from src.utils import logger

log = logger.get(__name__)

try:
    import win32gui  # type: ignore
    _HAS_WIN32 = True
except ImportError:
    _HAS_WIN32 = False


@dataclass
class WindowEntry:
    hwnd: int
    title: str
    rect: Rect


def list_windows() -> list[WindowEntry]:
    if not _HAS_WIN32:
        return []
    out: list[WindowEntry] = []

    def _cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return True
        try:
            l, t, r, b = win32gui.GetWindowRect(hwnd)
        except Exception:  # noqa: BLE001
            return True
        if r - l <= 0 or b - t <= 0:
            return True
        out.append(WindowEntry(hwnd=hwnd, title=title, rect=Rect(l, t, r - l, b - t)))
        return True

    win32gui.EnumWindows(_cb, None)
    # Topmost first (last enumerated is usually bottommost; EnumWindows yields z-order top→bottom)
    return out


class WindowPicker(QWidget):
    """Full-screen overlay that highlights the window under the cursor."""

    window_picked = pyqtSignal(object)   # Rect in physical px
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

        self._dpr = QGuiApplication.primaryScreen().devicePixelRatio() or 1.0
        virt = QGuiApplication.primaryScreen().virtualGeometry()
        self.setGeometry(virt)
        self._windows = list_windows()
        self._hovered: WindowEntry | None = None

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        """Force keyboard focus onto the overlay when it appears."""
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        self.grabKeyboard()
        QTimer.singleShot(0, self._refocus)

    # --- painting ------------------------------------------------------
    def paintEvent(self, _):  # noqa: N802, ANN001
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
        if self._hovered is None:
            return
        phys = self._hovered.rect
        local = QRect(
            int(phys.left / self._dpr) - self.x(),
            int(phys.top / self._dpr) - self.y(),
            int(phys.width / self._dpr),
            int(phys.height / self._dpr),
        )
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(local, Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        pen = QPen(QColor("#2f7fe6"), 3)
        painter.setPen(pen)
        painter.drawRect(local)
        painter.setPen(Qt.GlobalColor.white)
        title = self._hovered.title[:80]
        painter.fillRect(local.left(), local.top() - 22, min(600, len(title) * 9 + 20), 20, QColor(0, 0, 0, 200))
        painter.drawText(local.left() + 8, local.top() - 7, title)

    def _pick_at(self, global_pos: QPoint) -> WindowEntry | None:
        px = int(global_pos.x() * self._dpr)
        py = int(global_pos.y() * self._dpr)
        for w in self._windows:
            r = w.rect
            if r.left <= px <= r.right and r.top <= py <= r.bottom:
                return w
        return None

    # --- input ---------------------------------------------------------
    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._hovered = self._pick_at(event.globalPosition().toPoint())
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.RightButton:
            self._cancel()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        target = self._pick_at(event.globalPosition().toPoint())
        self.releaseKeyboard()
        self.hide()
        if target is None:
            self.cancelled.emit()
            return
        self.window_picked.emit(target.rect)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self._cancel()

    def _cancel(self) -> None:
        """Hide the overlay and notify capture cancellation."""
        self.releaseKeyboard()
        self.hide()
        self.cancelled.emit()

    def _refocus(self) -> None:
        """Retry focus after the window manager finishes showing the overlay."""
        if not self.isVisible():
            return
        self.activateWindow()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
