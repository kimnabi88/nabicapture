"""Mosaic tool. Downsample → upsample a rectangular region, add as overlay pixmap."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, QPointF, QRect, QRectF, Qt
from PyQt6.QtGui import QColor, QMouseEvent, QPen, QPixmap
from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem

from src.editor.tools.base_tool import BaseTool
from src.editor.undo_stack import AddItemCommand
from src.utils import logger

_log = logger.get("mosaic")


class MosaicTool(BaseTool):
    name = "mosaic"

    def __init__(self, canvas, block_size: int = 10):
        super().__init__(canvas)
        self.block_size = max(2, block_size)
        self._start: QPointF | None = None
        self._preview: QGraphicsRectItem | None = None

    def set_block_size(self, size: int) -> None:
        self.block_size = max(2, int(size))

    def press(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        self._start = scene_pos
        self._preview = QGraphicsRectItem(QRectF(scene_pos, scene_pos))
        pen = QPen(QColor("#00B8D4"), 1, Qt.PenStyle.DashLine)
        self._preview.setPen(pen)
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
        if self._preview.scene() is scene:
            scene.removeItem(self._preview)
        self._preview = None
        self._start = None
        if rect.width() < 4 or rect.height() < 4:
            return

        try:
            base = self.canvas.base_pixmap()
            if base is None or base.isNull():
                return
            bounds = QRectF(0, 0, base.width(), base.height())
            clamped: QRect = rect.intersected(bounds).toRect()
            if clamped.width() < 2 or clamped.height() < 2:
                return

            region = base.copy(clamped)
            if region.isNull() or region.width() < 2 or region.height() < 2:
                return

            bs = max(2, int(self.block_size))
            w = max(1, region.width() // bs)
            h = max(1, region.height() // bs)
            tiny = region.scaled(
                w, h,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            if tiny.isNull():
                return
            mosaic = tiny.scaled(
                region.width(), region.height(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            if mosaic.isNull():
                return

            item = QGraphicsPixmapItem(mosaic)
            item.setPos(QPointF(clamped.topLeft()))
            item.setZValue(-500)
            self.canvas.undo_stack.push(AddItemCommand(scene, item, text="mosaic"))
        except Exception:  # noqa: BLE001
            _log.exception("mosaic apply failed")
