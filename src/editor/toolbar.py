"""Editor top toolbar — tool selection + undo/redo/save/copy + settings."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence
from PyQt6.QtWidgets import QSizePolicy, QToolBar, QWidget

TOOL_BUTTONS = [
    ("pen", "펜"),
    ("highlighter", "형광펜"),
    ("rectangle", "사각"),
    ("ellipse", "원"),
    ("arrow", "화살표"),
    ("line", "선"),
    ("speech_bubble", "말풍선"),
    ("text", "텍스트"),
    ("crop", "자르기"),
    ("mosaic", "모자이크"),
    ("eraser", "지우개"),
]


class EditorToolbar(QToolBar):
    tool_selected = pyqtSignal(str)
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()
    save_requested = pyqtSignal()
    copy_requested = pyqtSignal()
    settings_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setMovable(False)
        self._actions: dict[str, QAction] = {}

        group = QActionGroup(self)
        group.setExclusive(True)
        for tool_id, label in TOOL_BUTTONS:
            act = QAction(label, self)
            act.setCheckable(True)
            act.triggered.connect(lambda _=False, t=tool_id: self.tool_selected.emit(t))
            group.addAction(act)
            self.addAction(act)
            self._actions[tool_id] = act

        self.addSeparator()

        undo = QAction("⟲ 실행취소", self)
        undo.setShortcut(QKeySequence.StandardKey.Undo)
        undo.triggered.connect(self.undo_requested.emit)
        self.addAction(undo)

        redo = QAction("⟳ 재실행", self)
        redo.setShortcut(QKeySequence.StandardKey.Redo)
        redo.triggered.connect(self.redo_requested.emit)
        self.addAction(redo)

        self.addSeparator()

        copy = QAction("클립보드 복사", self)
        copy.setShortcut(QKeySequence.StandardKey.Copy)
        copy.triggered.connect(self.copy_requested.emit)
        self.addAction(copy)

        save = QAction("저장", self)
        save.setShortcut(QKeySequence.StandardKey.Save)
        save.triggered.connect(self.save_requested.emit)
        self.addAction(save)

        # Push settings button to the far right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

        settings = QAction("⚙ 환경설정", self)
        settings.triggered.connect(self.settings_requested.emit)
        self.addAction(settings)

    def select_tool(self, tool_id: str) -> None:
        act = self._actions.get(tool_id)
        if act is not None:
            act.setChecked(True)
            self.tool_selected.emit(tool_id)
