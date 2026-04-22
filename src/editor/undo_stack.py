"""Helpers around QUndoStack. Keeps tools decoupled from Qt undo internals."""

from __future__ import annotations

from typing import Callable

from PyQt6.QtGui import QUndoCommand, QUndoStack
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsScene


class AddItemCommand(QUndoCommand):
    """Generic: add a QGraphicsItem to a scene, reversible."""

    def __init__(self, scene: QGraphicsScene, item: QGraphicsItem, text: str = "Add"):
        super().__init__(text)
        self._scene = scene
        self._item = item
        self._added = False

    def redo(self) -> None:
        if not self._added:
            self._scene.addItem(self._item)
            self._added = True
        else:
            if self._item.scene() is None:
                self._scene.addItem(self._item)

    def undo(self) -> None:
        if self._item.scene() is not None:
            self._scene.removeItem(self._item)


class CallableCommand(QUndoCommand):
    """Generic: run redo()/undo() as plain callables. Keeps tools simple."""

    def __init__(self, text: str, do: Callable[[], None], undo: Callable[[], None]):
        super().__init__(text)
        self._do = do
        self._undo = undo

    def redo(self) -> None:
        self._do()

    def undo(self) -> None:
        self._undo()


def new_stack() -> QUndoStack:
    s = QUndoStack()
    s.setUndoLimit(200)
    return s
