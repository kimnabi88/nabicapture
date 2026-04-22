"""Eraser. Removes non-base graphics items under the cursor, stroke-granular undo."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QMouseEvent, QPen
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsRectItem

from src.editor.tools.base_tool import BaseTool
from src.editor.undo_stack import CallableCommand


class EraserTool(BaseTool):
    name = "eraser"

    def __init__(self, canvas, radius: int = 10):
        super().__init__(canvas)
        self.radius = radius
        self._removed: list[QGraphicsItem] = []
        self._cursor: QGraphicsRectItem | None = None
        self._active = False

    def set_radius(self, r: int) -> None:
        self.radius = max(2, int(r))

    def activate(self) -> None:
        r = QRectF(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        self._cursor = QGraphicsRectItem(r)
        self._cursor.setPen(QPen(QColor("#FFFFFF"), 1, Qt.PenStyle.DashLine))
        self._cursor.setZValue(10_000)
        self.canvas.scene_ref().addItem(self._cursor)

    def deactivate(self) -> None:
        if self._cursor is not None:
            self.canvas.scene_ref().removeItem(self._cursor)
            self._cursor = None

    def press(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        self._active = True
        self._removed = []
        self._erase_at(scene_pos)

    def move(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        if self._cursor is not None:
            self._cursor.setPos(scene_pos)
        if self._active:
            self._erase_at(scene_pos)

    def release(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        self._active = False
        if not self._removed:
            return
        removed = list(self._removed)
        scene = self.canvas.scene_ref()

        def do():
            for it in removed:
                if it.scene() is not None:
                    scene.removeItem(it)

        def undo():
            for it in removed:
                if it.scene() is None:
                    scene.addItem(it)

        self.canvas.undo_stack.push(CallableCommand("erase", do, undo))
        self._removed = []

    def _erase_at(self, pos: QPointF) -> None:
        scene = self.canvas.scene_ref()
        area = QRectF(pos.x() - self.radius, pos.y() - self.radius,
                      self.radius * 2, self.radius * 2)
        for it in scene.items(area):
            if it is self._cursor:
                continue
            if it.zValue() <= -1000:  # base layer
                continue
            scene.removeItem(it)
            self._removed.append(it)
