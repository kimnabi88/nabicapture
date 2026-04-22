"""Text insertion tool. Click to place an inline editor, Enter/완료 commits."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QFocusEvent, QFont, QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import QGraphicsTextItem

from src.editor.tools.base_tool import BaseTool
from src.editor.undo_stack import AddItemCommand


class _InlineTextItem(QGraphicsTextItem):
    """Editable text item that commits on focus-out, Ctrl+Enter, or Esc."""

    def __init__(self, tool: "TextTool"):
        super().__init__("")
        self._tool = tool
        self.setFlag(QGraphicsTextItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsTextItem.GraphicsItemFlag.ItemIsFocusable, True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)

    def focusOutEvent(self, event: QFocusEvent) -> None:  # noqa: N802
        super().focusOutEvent(event)
        self._tool._commit_active(self)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self._tool._cancel_active(self)
            return
        if (event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
                and (event.modifiers() & Qt.KeyboardModifier.ControlModifier)):
            self._tool._commit_active(self)
            return
        super().keyPressEvent(event)


class TextTool(BaseTool):
    name = "text"

    def __init__(self, canvas, font_family: str = "Segoe UI", font_size: int = 16):
        super().__init__(canvas)
        self.font_family = font_family
        self.font_size = int(font_size)
        self.bold = False
        self._active: _InlineTextItem | None = None

    # --- configuration (driven by toolbar) -----------------------------
    def set_font(self, family: str, size: int) -> None:
        self.font_family = family
        self.font_size = int(size)
        self._apply_font_to_active()

    def set_font_family(self, family: str) -> None:
        self.font_family = family
        self._apply_font_to_active()

    def set_font_size(self, size: int) -> None:
        self.font_size = int(size)
        self._apply_font_to_active()

    def set_bold(self, bold: bool) -> None:
        self.bold = bool(bold)
        self._apply_font_to_active()

    def set_color(self, color: QColor) -> None:
        super().set_color(color)
        if self._active is not None:
            self._active.setDefaultTextColor(QColor(self.color))

    def deactivate(self) -> None:
        self._commit_active(self._active)

    # --- mouse -----------------------------------------------------------
    def press(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        if self._active is not None:
            scene = self.canvas.scene_ref()
            hit = scene.itemAt(scene_pos, self.canvas.transform())
            if hit is self._active:
                return
            self._commit_active(self._active)

        item = _InlineTextItem(self)
        item.setDefaultTextColor(QColor(self.color))
        item.setFont(self._make_font())
        item.setPos(scene_pos)
        item.setZValue(500)
        self.canvas.scene_ref().addItem(item)
        item.setFocus(Qt.FocusReason.MouseFocusReason)
        self._active = item

    # --- externally invoked (toolbar "입력" button) ---------------------
    def commit_current(self) -> None:
        self._commit_active(self._active)

    # --- helpers --------------------------------------------------------
    def _make_font(self) -> QFont:
        f = QFont(self.font_family, self.font_size)
        f.setBold(self.bold)
        if not self.bold:
            f.setWeight(QFont.Weight.DemiBold)
        return f

    def _apply_font_to_active(self) -> None:
        if self._active is not None:
            self._active.setFont(self._make_font())

    def _commit_active(self, item: _InlineTextItem | None) -> None:
        if item is None or item is not self._active:
            return
        self._active = None
        text = item.toPlainText().strip()
        scene = self.canvas.scene_ref()
        if not text:
            if item.scene() is scene:
                scene.removeItem(item)
            return
        # Freeze: disable editing, make it just a movable overlay, and push undo.
        item.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        item.clearFocus()
        scene.removeItem(item)
        self.canvas.undo_stack.push(AddItemCommand(scene, item, text="text"))

    def _cancel_active(self, item: _InlineTextItem) -> None:
        if item is not self._active:
            return
        self._active = None
        scene = self.canvas.scene_ref()
        if item.scene() is scene:
            scene.removeItem(item)
