"""Hotkey recorder line edit. Shows a human-readable combo and emits a string
compatible with the `keyboard` library (e.g. "ctrl+shift+a")."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QLineEdit

_MOD_MAP = {
    Qt.KeyboardModifier.ControlModifier: "ctrl",
    Qt.KeyboardModifier.ShiftModifier: "shift",
    Qt.KeyboardModifier.AltModifier: "alt",
    Qt.KeyboardModifier.MetaModifier: "win",
}

_KEY_NAMES = {
    Qt.Key.Key_Print: "print screen",
    Qt.Key.Key_Space: "space",
    Qt.Key.Key_Return: "enter",
    Qt.Key.Key_Enter: "enter",
    Qt.Key.Key_Escape: "esc",
    Qt.Key.Key_Tab: "tab",
    Qt.Key.Key_Backspace: "backspace",
    Qt.Key.Key_Delete: "delete",
    Qt.Key.Key_Insert: "insert",
    Qt.Key.Key_Home: "home",
    Qt.Key.Key_End: "end",
    Qt.Key.Key_PageUp: "page up",
    Qt.Key.Key_PageDown: "page down",
    Qt.Key.Key_Left: "left",
    Qt.Key.Key_Right: "right",
    Qt.Key.Key_Up: "up",
    Qt.Key.Key_Down: "down",
    Qt.Key.Key_Plus: "+",
    Qt.Key.Key_Minus: "-",
    Qt.Key.Key_Equal: "=",
}


def _key_name(key: int) -> str | None:
    if key in _KEY_NAMES:
        return _KEY_NAMES[key]
    if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
        return chr(key).lower()
    if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
        return chr(key)
    if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F24:
        return f"f{key - Qt.Key.Key_F1 + 1}"
    return None


class HotkeyInput(QLineEdit):
    combo_changed = pyqtSignal(str)

    def __init__(self, initial: str = ""):
        super().__init__(initial)
        self.setReadOnly(True)
        self.setPlaceholderText("여기를 클릭하고 키를 누르세요")

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        if key in (
            Qt.Key.Key_Control, Qt.Key.Key_Shift,
            Qt.Key.Key_Alt, Qt.Key.Key_Meta, Qt.Key.Key_AltGr,
        ):
            return
        if key == Qt.Key.Key_Backspace:
            self.setText("")
            self.combo_changed.emit("")
            return

        parts: list[str] = []
        mods = event.modifiers()
        for mod, name in _MOD_MAP.items():
            if mods & mod:
                parts.append(name)
        key_name = _key_name(key)
        if key_name is None:
            return
        parts.append(key_name)
        combo = "+".join(parts)
        self.setText(combo)
        self.combo_changed.emit(combo)

    def value(self) -> str:
        return self.text()
