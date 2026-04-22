"""Base class all editor tools inherit from."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QMouseEvent

if TYPE_CHECKING:
    from src.editor.canvas import Canvas


class BaseTool:
    """Mouse-event hooks scoped to a scene. Concrete tools override."""

    name: str = "base"

    def __init__(self, canvas: "Canvas"):
        self.canvas = canvas
        self.color: QColor = QColor("#FF1744")
        self.width: int = 3

    # --- lifecycle -----------------------------------------------------
    def activate(self) -> None:
        """Called when this tool becomes the active one."""

    def deactivate(self) -> None:
        """Called when another tool is activated."""

    # --- mouse hooks ---------------------------------------------------
    def press(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        pass

    def move(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        pass

    def release(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        pass

    # --- configuration passthrough ------------------------------------
    def set_color(self, color: QColor) -> None:
        self.color = color

    def set_width(self, width: int) -> None:
        self.width = width


class NoopTool(BaseTool):
    name = "noop"
