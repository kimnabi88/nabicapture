"""Full-screen translucent overlay — drag to pick a rectangular region.

Emits a screen_capture.Rect in physical-pixel coordinates.
"""

from __future__ import annotations

from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QCursor,
    QGuiApplication,
    QKeyEvent,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import QWidget

from src.capture.screen_capture import Rect, virtual_screen


class RegionSelector(QWidget):
    region_selected = pyqtSignal(object)   # Rect in physical px
    cancelled = pyqtSignal()

    def __init__(self, guideline_color: str = "#FF5555", thickness: int = 1):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)

        self._guideline = QColor(guideline_color)
        self._thickness = max(1, thickness)
        self._start: QPoint | None = None
        self._end: QPoint | None = None

        # Use logical geometry. We'll convert to physical px on emit.
        self._virt = virtual_screen()
        self._dpr = QGuiApplication.primaryScreen().devicePixelRatio() or 1.0
        logical_w = int(self._virt.width / self._dpr)
        logical_h = int(self._virt.height / self._dpr)
        logical_left = int(self._virt.left / self._dpr)
        logical_top = int(self._virt.top / self._dpr)
        self.setGeometry(logical_left, logical_top, logical_w, logical_h)

    # --- painting -------------------------------------------------------
    def paintEvent(self, _: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        full = self.rect()
        shade = QColor(0, 0, 0, 110)
        painter.fillRect(full, shade)

        rect = self._current_rect()
        if rect is not None and rect.isValid():
            # punch hole: clear the selected area back to fully transparent
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # border
            pen = QPen(self._guideline, self._thickness)
            painter.setPen(pen)
            painter.drawRect(rect)

            # size text
            painter.setPen(Qt.GlobalColor.white)
            phys_w = int(rect.width() * self._dpr)
            phys_h = int(rect.height() * self._dpr)
            label = f"{phys_w} × {phys_h} px"
            tx = rect.right() + 8
            ty = rect.bottom() + 18
            if tx + 140 > full.right():
                tx = rect.right() - 140
            if ty + 4 > full.bottom():
                ty = rect.top() - 6
            painter.fillRect(tx - 4, ty - 14, 140, 20, QColor(0, 0, 0, 180))
            painter.drawText(tx, ty, label)

        # crosshair guidelines when not dragging
        if self._start is None and self.underMouse():
            pos = self.mapFromGlobal(QCursor.pos())
            pen = QPen(self._guideline, self._thickness, Qt.PenStyle.DotLine)
            painter.setPen(pen)
            painter.drawLine(0, pos.y(), full.width(), pos.y())
            painter.drawLine(pos.x(), 0, pos.x(), full.height())

    def _current_rect(self) -> QRect | None:
        if self._start is None or self._end is None:
            return None
        return QRect(self._start, self._end).normalized()

    # --- input ----------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.pos()
            self._end = event.pos()
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self._cancel()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton or self._start is None:
            return
        self._end = event.pos()
        rect = self._current_rect()
        self.hide()
        if rect is None or rect.width() < 3 or rect.height() < 3:
            self.cancelled.emit()
            return
        phys = Rect(
            left=int(rect.left() * self._dpr) + self._virt.left,
            top=int(rect.top() * self._dpr) + self._virt.top,
            width=int(rect.width() * self._dpr),
            height=int(rect.height() * self._dpr),
        )
        self.region_selected.emit(phys)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self._cancel()

    def _cancel(self) -> None:
        self.hide()
        self.cancelled.emit()
