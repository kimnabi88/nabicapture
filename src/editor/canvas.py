"""QGraphicsView wrapper hosting a base bitmap and editable overlay items."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
)

from src.editor.tools.base_tool import BaseTool, NoopTool
from src.editor.undo_stack import new_stack


class Canvas(QGraphicsView):
    """One image = one Canvas. Tools mutate the scene through the active tool."""

    base_changed = pyqtSignal(int, int)   # width, height after replace

    def __init__(self):
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setBackgroundBrush(QColor("#e9ecf1"))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setMouseTracking(True)

        self._base_item: QGraphicsPixmapItem | None = None
        self._active_tool: BaseTool = NoopTool(self)
        self.undo_stack = new_stack()

    # --- image ----------------------------------------------------------
    def set_image(self, image: QImage) -> None:
        self._scene.clear()
        pix = QPixmap.fromImage(image)
        self._base_item = QGraphicsPixmapItem(pix)
        self._base_item.setZValue(-1000)
        self._scene.addItem(self._base_item)
        self._scene.setSceneRect(QRectF(0, 0, pix.width(), pix.height()))
        self.resetTransform()
        self.base_changed.emit(pix.width(), pix.height())

    def base_pixmap(self) -> QPixmap | None:
        return self._base_item.pixmap() if self._base_item else None

    def replace_base(self, pix: QPixmap) -> None:
        if self._base_item is None:
            self._base_item = QGraphicsPixmapItem(pix)
            self._base_item.setZValue(-1000)
            self._scene.addItem(self._base_item)
        else:
            self._base_item.setPixmap(pix)
        self._scene.setSceneRect(QRectF(0, 0, pix.width(), pix.height()))
        self.base_changed.emit(pix.width(), pix.height())

    def render_flat(self) -> QImage:
        """Flatten scene (base + edits) to a QImage at native size."""
        rect = self._scene.sceneRect()
        image = QImage(
            int(rect.width()), int(rect.height()),
            QImage.Format.Format_ARGB32,
        )
        image.fill(0)
        painter = QPainter(image)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self._scene.render(painter, QRectF(image.rect()), rect)
        painter.end()
        return image

    # --- tools ----------------------------------------------------------
    def set_active_tool(self, tool: BaseTool) -> None:
        if self._active_tool is tool:
            return
        self._active_tool.deactivate()
        self._active_tool = tool
        tool.activate()

    def active_tool(self) -> BaseTool:
        return self._active_tool

    def scene_ref(self) -> QGraphicsScene:
        return self._scene

    # --- mouse routing --------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._active_tool.press(self.mapToScene(event.pos()), event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._active_tool.move(self.mapToScene(event.pos()), event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._active_tool.release(self.mapToScene(event.pos()), event)
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):  # noqa: N802, ANN001
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
            event.accept()
            return
        super().wheelEvent(event)
