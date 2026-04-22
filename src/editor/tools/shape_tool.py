"""Drag-to-draw shapes: rectangle, ellipse, line, arrow, speech bubble."""

from __future__ import annotations

from math import atan2, cos, pi, sin

from PyQt6.QtCore import QLineF, QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QMouseEvent,
    QPainterPath,
    QPen,
    QPolygonF,
)
from PyQt6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
)

from src.editor.tools.base_tool import BaseTool
from src.editor.undo_stack import AddItemCommand

SHAPE_IDS = ("rectangle", "ellipse", "line", "arrow", "speech_bubble")


def _rect_from_points(a: QPointF, b: QPointF) -> QRectF:
    return QRectF(
        min(a.x(), b.x()), min(a.y(), b.y()),
        abs(a.x() - b.x()), abs(a.y() - b.y()),
    )


def _arrow_head(tail: QPointF, head: QPointF, size: float) -> QPolygonF:
    angle = atan2(head.y() - tail.y(), head.x() - tail.x())
    a = angle + pi - 0.45
    b = angle + pi + 0.45
    p1 = QPointF(head.x() + cos(a) * size, head.y() + sin(a) * size)
    p2 = QPointF(head.x() + cos(b) * size, head.y() + sin(b) * size)
    return QPolygonF([head, p1, p2])


def _speech_bubble(rect: QRectF) -> QPainterPath:
    path = QPainterPath()
    radius = min(rect.width(), rect.height()) * 0.15
    path.addRoundedRect(rect, radius, radius)
    # tail pointing down-left from the bottom edge
    tail_x1 = rect.left() + rect.width() * 0.25
    tail_x2 = rect.left() + rect.width() * 0.35
    tail_y = rect.bottom()
    tail_tip = QPointF(rect.left() + rect.width() * 0.18, tail_y + rect.height() * 0.25)
    tail = QPainterPath()
    tail.moveTo(tail_x1, tail_y)
    tail.lineTo(tail_tip)
    tail.lineTo(tail_x2, tail_y)
    tail.closeSubpath()
    path.addPath(tail)
    return path


class ShapeTool(BaseTool):
    name = "shape"

    def __init__(self, canvas, shape: str = "rectangle"):
        super().__init__(canvas)
        self.shape = shape if shape in SHAPE_IDS else "rectangle"
        self.filled = False
        self._start: QPointF | None = None
        self._preview = None

    def set_shape(self, shape: str) -> None:
        if shape in SHAPE_IDS:
            self.shape = shape

    def set_filled(self, on: bool) -> None:
        self.filled = on

    def _pen(self) -> QPen:
        pen = QPen(QColor(self.color), self.width)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        return pen

    def _brush(self) -> QBrush:
        if self.filled:
            c = QColor(self.color)
            c.setAlphaF(0.35)
            return QBrush(c)
        return QBrush(Qt.BrushStyle.NoBrush)

    def press(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        self._start = scene_pos
        self._preview = self._make_item(scene_pos, scene_pos)
        self.canvas.scene_ref().addItem(self._preview)

    def move(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        if self._start is None or self._preview is None:
            return
        self.canvas.scene_ref().removeItem(self._preview)
        self._preview = self._make_item(self._start, scene_pos)
        self.canvas.scene_ref().addItem(self._preview)

    def release(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        if self._start is None or self._preview is None:
            return
        scene = self.canvas.scene_ref()
        scene.removeItem(self._preview)
        item = self._make_item(self._start, scene_pos)
        self.canvas.undo_stack.push(
            AddItemCommand(scene, item, text=f"shape:{self.shape}")
        )
        self._preview = None
        self._start = None

    def _make_item(self, a: QPointF, b: QPointF):
        pen = self._pen()
        brush = self._brush()
        if self.shape == "rectangle":
            it = QGraphicsRectItem(_rect_from_points(a, b))
            it.setPen(pen); it.setBrush(brush)
            return it
        if self.shape == "ellipse":
            it = QGraphicsEllipseItem(_rect_from_points(a, b))
            it.setPen(pen); it.setBrush(brush)
            return it
        if self.shape == "line":
            it = QGraphicsLineItem(QLineF(a, b))
            it.setPen(pen)
            return it
        if self.shape == "arrow":
            path = QPainterPath()
            path.moveTo(a); path.lineTo(b)
            size = max(self.width * 3.5, 10.0)
            path.addPolygon(_arrow_head(a, b, size))
            it = QGraphicsPathItem(path)
            c = QColor(self.color)
            it.setPen(pen); it.setBrush(QBrush(c))
            return it
        # speech_bubble
        it = QGraphicsPathItem(_speech_bubble(_rect_from_points(a, b)))
        it.setPen(pen); it.setBrush(brush)
        return it
