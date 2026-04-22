"""Freehand pen and highlighter. Shared path-building logic, different strokes."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QMouseEvent, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsPathItem

from src.editor.tools.base_tool import BaseTool
from src.editor.undo_stack import AddItemCommand


class _StrokeTool(BaseTool):
    """Shared base for path-drawing tools."""

    composition_mode: str = "normal"
    opacity: float = 1.0
    cap_style = Qt.PenCapStyle.RoundCap

    def __init__(self, canvas):
        super().__init__(canvas)
        self._current: QGraphicsPathItem | None = None
        self._path: QPainterPath | None = None

    def _build_pen(self) -> QPen:
        color = QColor(self.color)
        color.setAlphaF(self.opacity)
        pen = QPen(color, self.width)
        pen.setCapStyle(self.cap_style)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return pen

    def press(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        self._path = QPainterPath(scene_pos)
        item = QGraphicsPathItem(self._path)
        item.setPen(self._build_pen())
        self.canvas.scene_ref().addItem(item)
        self._current = item

    def move(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        if self._current is None or self._path is None:
            return
        self._path.lineTo(scene_pos)
        self._current.setPath(self._path)

    def release(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        if self._current is None:
            return
        scene = self.canvas.scene_ref()
        scene.removeItem(self._current)
        cmd = AddItemCommand(scene, self._current, text=self.name)
        self.canvas.undo_stack.push(cmd)
        self._current = None
        self._path = None


class PenTool(_StrokeTool):
    name = "pen"
    opacity = 1.0


class HighlighterTool(_StrokeTool):
    name = "highlighter"
    opacity = 0.35

    def __init__(self, canvas, width: int = 18):
        super().__init__(canvas)
        self.width = width
        self.cap_style = Qt.PenCapStyle.FlatCap
