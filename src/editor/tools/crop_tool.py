"""Crop tool. Drag a rect, release to confirm — reversible via undo."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QMouseEvent, QPen, QPixmap
from PyQt6.QtWidgets import QGraphicsRectItem

from src.editor.tools.base_tool import BaseTool
from src.editor.undo_stack import CallableCommand


class CropTool(BaseTool):
    name = "crop"

    def __init__(self, canvas):
        super().__init__(canvas)
        self._start: QPointF | None = None
        self._preview: QGraphicsRectItem | None = None

    def _pen(self) -> QPen:
        pen = QPen(QColor("#FFD600"), 2, Qt.PenStyle.DashLine)
        return pen

    def press(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        self._start = scene_pos
        self._preview = QGraphicsRectItem(QRectF(scene_pos, scene_pos))
        self._preview.setPen(self._pen())
        self.canvas.scene_ref().addItem(self._preview)

    def move(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        if self._start is None or self._preview is None:
            return
        self._preview.setRect(QRectF(self._start, scene_pos).normalized())

    def release(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        if self._start is None or self._preview is None:
            return
        rect = QRectF(self._start, scene_pos).normalized()
        scene = self.canvas.scene_ref()
        scene.removeItem(self._preview)
        self._preview = None
        self._start = None
        if rect.width() < 4 or rect.height() < 4:
            return

        old = self.canvas.base_pixmap()
        if old is None:
            return

        clamped = rect.intersected(QRectF(0, 0, old.width(), old.height())).toRect()
        new_pix = old.copy(clamped)

        def do_crop():
            self.canvas.replace_base(new_pix)

        def undo_crop():
            self.canvas.replace_base(old)

        self.canvas.undo_stack.push(
            CallableCommand("crop", do_crop, undo_crop),
        )
