"""Full-screen translucent overlay — drag to pick a rectangular region.

Emits a screen_capture.Rect in physical-pixel coordinates.
Uses Qt virtualGeometry so the overlay spans ALL monitors.
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

from src.capture.screen_capture import Rect


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

        # virtualGeometry covers all monitors in logical coordinates
        virt = QGuiApplication.primaryScreen().virtualGeometry()
        self.setGeometry(virt)
        self._virt_left = virt.left()
        self._virt_top = virt.top()

    # --- painting -------------------------------------------------------
    def paintEvent(self, _: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        full = self.rect()
        painter.fillRect(full, QColor(0, 0, 0, 110))

        rect = self._current_rect()
        if rect is not None and rect.isValid():
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            pen = QPen(self._guideline, self._thickness)
            painter.setPen(pen)
            painter.drawRect(rect)

            # Size label in physical px using screen DPR at selection center
            dpr = self._dpr_at(rect.center())
            phys_w = int(rect.width() * dpr)
            phys_h = int(rect.height() * dpr)
            label = f"{phys_w} × {phys_h} px"
            tx = rect.right() + 8
            ty = rect.bottom() + 18
            if tx + 140 > full.right():
                tx = rect.right() - 140
            if ty + 4 > full.bottom():
                ty = rect.top() - 6
            painter.setPen(Qt.GlobalColor.white)
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

    def _dpr_at(self, widget_pos: QPoint) -> float:
        """Return the device pixel ratio of the screen under widget_pos."""
        global_pos = QPoint(
            widget_pos.x() + self._virt_left,
            widget_pos.y() + self._virt_top,
        )
        screen = QGuiApplication.screenAt(global_pos) or QGuiApplication.primaryScreen()
        return screen.devicePixelRatio() if screen else 1.0

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

        dpr = self._dpr_at(rect.center())
        # Convert widget-local logical rect to global physical coords
        global_left = rect.left() + self._virt_left
        global_top = rect.top() + self._virt_top
        phys = Rect(
            left=int(global_left * dpr),
            top=int(global_top * dpr),
            width=max(1, int(rect.width() * dpr)),
            height=max(1, int(rect.height() * dpr)),
        )
        self.region_selected.emit(phys)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self._cancel()

    def _cancel(self) -> None:
        self.hide()
        self.cancelled.emit()
