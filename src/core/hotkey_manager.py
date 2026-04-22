"""Global hotkeys via `keyboard` library. Bridges to Qt signals (thread-safe)."""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from src.utils import logger

log = logger.get(__name__)

try:
    import keyboard as _kb  # type: ignore
    _HAS_KB = True
except ImportError:
    _HAS_KB = False


class HotkeyManager(QObject):
    """Each registered hotkey emits `triggered(action_id)` on the Qt main thread."""

    triggered = pyqtSignal(str)
    error = pyqtSignal(str, str)   # action_id, message

    def __init__(self):
        super().__init__()
        self._handles: dict[str, object] = {}
        self._bindings: dict[str, str] = {}
        self._printscreen_handle: object | None = None

    def apply(self, bindings: dict[str, str], *, printscreen_action: str | None) -> None:
        """Replace all hotkeys. printscreen_action=None disables PrintScreen hook."""
        self.clear()
        self._bindings = dict(bindings)
        if not _HAS_KB:
            self.error.emit("*", "keyboard library not available")
            return
        for action, combo in bindings.items():
            if not combo:
                continue
            self._register(action, combo)
        if printscreen_action:
            self._register(printscreen_action, "print screen", override=True)

    def clear(self) -> None:
        if not _HAS_KB:
            return
        for handle in list(self._handles.values()):
            try:
                _kb.remove_hotkey(handle)
            except (KeyError, ValueError):
                pass
        self._handles.clear()

    def _register(self, action: str, combo: str, override: bool = False) -> None:
        try:
            handle = _kb.add_hotkey(
                combo,
                lambda a=action: self.triggered.emit(a),
                suppress=True,
            )
        except Exception as exc:  # noqa: BLE001 — keyboard can raise many types
            log.warning("hotkey register failed %s=%s: %s", action, combo, exc)
            self.error.emit(action, str(exc))
            return
        if override and action in self._handles:
            return
        self._handles[action] = handle
