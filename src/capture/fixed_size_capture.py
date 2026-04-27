"""Fixed-size capture — ask W×H, then let user place the rectangle and click."""

from __future__ import annotations

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
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
    QWidget,
)

from src.capture.screen_capture import Rect


class SizeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("크기지정")
        form = QFormLayout(self)
        self.w = QSpinBox(); self.w.setRange(10, 16384); self.w.setValue(800)
        self.h = QSpinBox(); self.h.setRange(10, 16384); self.h.setValue(600)
        form.addRow("가로 (px)", self.w)
        form.addRow("세로 (px)", self.h)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self) -> tuple[int, int]:
        return self.w.value(), self.h.value()


class FixedSizeSelector(QWidget):
    """Full-screen overlay with a rectangle cursor of fixed size."""

    region_selected = pyqtSignal(object)
    cancelled = pyqtSignal()

    def __init__(self, width_px: int, height_px: int):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.BlankCursor)
        self.setMouseTracking(True)

        self._w = width_px
        self._h = height_px
        self._dpr = QGuiApplication.primaryScreen().devicePixelRatio() or 1.0
        virt = QGuiApplication.primaryScreen().virtualGeometry()
        self.setGeometry(virt)
        self._cursor = QCursor.pos() - self.pos()

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        """Force keyboard focus onto the overlay when it appears."""
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        self.grabKeyboard()
        QTimer.singleShot(0, self._refocus)

    def _logical_rect(self) -> QRect:
        """Return the current fixed capture rectangle in logical pixels."""
        lw = int(self._w / self._dpr)
        lh = int(self._h / self._dpr)
        return QRect(self._cursor.x() - lw // 2, self._cursor.y() - lh // 2, lw, lh)

    def paintEvent(self, _):  # noqa: N802, ANN001
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 90))
        rect = self._logical_rect()
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(rect, Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setPen(QPen(QColor("#2f7fe6"), 2))
        painter.drawRect(rect)
        painter.setPen(Qt.GlobalColor.white)
        label = f"{self._w} × {self._h} px"
        painter.fillRect(rect.left(), rect.top() - 22, 140, 20, QColor(0, 0, 0, 200))
        painter.drawText(rect.left() + 6, rect.top() - 7, label)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._cursor = event.pos()
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.RightButton:
            self._cancel()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        rect = self._logical_rect()
        self.releaseKeyboard()
        self.hide()
        phys = Rect(
            left=int(rect.left() * self._dpr) + self.x(),
            top=int(rect.top() * self._dpr) + self.y(),
            width=self._w,
            height=self._h,
        )
        self.region_selected.emit(phys)

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
