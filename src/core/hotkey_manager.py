"""Global hotkeys with a native Windows backend and keyboard fallback."""

from __future__ import annotations

import ctypes
import queue
import threading
from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtCore import QObject, pyqtSignal

from src.utils import logger

log = logger.get(__name__)

try:
    import keyboard as _kb  # type: ignore
    _HAS_KB = True
except ImportError:
    _HAS_KB = False

try:
    from ctypes import wintypes
    _HAS_WIN32_HOTKEY = True
except ImportError:
    _HAS_WIN32_HOTKEY = False


MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
WM_APP_REGISTER = 0x8001

_NAMED_KEYS = {
    "print screen": 0x2C,
    "printscreen": 0x2C,
    "prtsc": 0x2C,
    "space": 0x20,
    "enter": 0x0D,
    "return": 0x0D,
    "esc": 0x1B,
    "escape": 0x1B,
    "tab": 0x09,
    "backspace": 0x08,
    "delete": 0x2E,
    "insert": 0x2D,
    "home": 0x24,
    "end": 0x23,
    "page up": 0x21,
    "page down": 0x22,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
}


@dataclass(frozen=True)
class ParsedHotkey:
    """A RegisterHotKey-compatible modifier mask and virtual key."""

    modifiers: int
    vk: int


def _parse_combo(combo: str) -> ParsedHotkey:
    """Parse a combo string like ctrl+shift+c into Win32 values."""
    parts = [part.strip().lower() for part in combo.split("+") if part.strip()]
    if not parts:
        raise ValueError("empty hotkey")

    modifiers = 0
    key_parts: list[str] = []
    for part in parts:
        if part in {"ctrl", "control"}:
            modifiers |= MOD_CONTROL
        elif part == "shift":
            modifiers |= MOD_SHIFT
        elif part == "alt":
            modifiers |= MOD_ALT
        elif part in {"win", "meta", "windows"}:
            modifiers |= MOD_WIN
        else:
            key_parts.append(part)

    key_name = " ".join(key_parts)
    if key_name in _NAMED_KEYS:
        return ParsedHotkey(modifiers=modifiers, vk=_NAMED_KEYS[key_name])
    if len(key_name) == 1 and key_name.isalpha():
        return ParsedHotkey(modifiers=modifiers, vk=ord(key_name.upper()))
    if len(key_name) == 1 and key_name.isdigit():
        return ParsedHotkey(modifiers=modifiers, vk=ord(key_name))
    if key_name.startswith("f") and key_name[1:].isdigit():
        number = int(key_name[1:])
        if 1 <= number <= 24:
            return ParsedHotkey(modifiers=modifiers, vk=0x70 + number - 1)
    raise ValueError(f"unsupported hotkey: {combo}")


class _NativeHotkeyBackend:
    """Register global hotkeys through the Windows RegisterHotKey API."""

    def __init__(self, callback: Callable[[str], None]):
        self._callback = callback
        self._actions_by_id: dict[int, str] = {}
        self._next_id = 1000
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._ready = threading.Event()
        self._lock = threading.RLock()
        self._commands: queue.Queue[dict] = queue.Queue()

    def register(self, action: str, combo: str) -> int:
        """Register one combo and return its native hotkey id."""
        if not _HAS_WIN32_HOTKEY:
            raise RuntimeError("native hotkey backend is unavailable")
        parsed = _parse_combo(combo)
        self._ensure_thread()
        with self._lock:
            hotkey_id = self._next_id
            self._next_id += 1
        done = threading.Event()
        command = {
            "id": hotkey_id,
            "action": action,
            "combo": combo,
            "parsed": parsed,
            "done": done,
            "error": None,
        }
        self._commands.put(command)
        ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_APP_REGISTER, 0, 0)
        if not done.wait(timeout=1.0):
            raise RuntimeError(f"RegisterHotKey timed out for {combo}")
        if command["error"]:
            raise RuntimeError(str(command["error"]))
        return hotkey_id

    def clear(self) -> None:
        """Unregister every native hotkey and stop the message thread."""
        if not _HAS_WIN32_HOTKEY:
            return
        thread_id = self._thread_id
        if thread_id:
            ctypes.windll.user32.PostThreadMessageW(thread_id, WM_QUIT, 0, 0)
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self._thread = None
        self._thread_id = 0
        self._ready.clear()

    def _ensure_thread(self) -> None:
        """Start the native message loop thread once."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._ready.clear()
        self._thread = threading.Thread(
            target=self._message_loop,
            name="NabiCaptureHotkeys",
            daemon=True,
        )
        self._thread.start()
        if not self._ready.wait(timeout=1.0):
            raise RuntimeError("native hotkey message loop did not start")

    def _message_loop(self) -> None:
        """Process WM_HOTKEY messages and dispatch actions."""
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        ctypes.windll.user32.PeekMessageW(ctypes.byref(wintypes.MSG()), None, 0, 0, 0)
        self._ready.set()
        msg = wintypes.MSG()
        try:
            while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_APP_REGISTER:
                    self._process_register_command()
                    continue
                if msg.message != WM_HOTKEY:
                    continue
                action = self._actions_by_id.get(int(msg.wParam))
                if action:
                    self._callback(action)
        finally:
            for hotkey_id in list(self._actions_by_id):
                ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
            self._actions_by_id.clear()

    def _process_register_command(self) -> None:
        """Register queued hotkey commands on the message-loop thread."""
        while True:
            try:
                command = self._commands.get_nowait()
            except queue.Empty:
                return
            parsed = command["parsed"]
            hotkey_id = int(command["id"])
            ok = ctypes.windll.user32.RegisterHotKey(None, hotkey_id, parsed.modifiers, parsed.vk)
            if ok:
                self._actions_by_id[hotkey_id] = str(command["action"])
            else:
                command["error"] = f"RegisterHotKey failed for {command['combo']}"
            command["done"].set()


class _KeyboardHotkeyBackend:
    """Fallback backend using the keyboard package."""

    def __init__(self, callback: Callable[[str], None]):
        self._callback = callback
        self._handles: list[object] = []

    def register(self, action: str, combo: str) -> object:
        """Register one combo through keyboard.add_hotkey."""
        if not _HAS_KB:
            raise RuntimeError("keyboard library not available")
        handle = _kb.add_hotkey(combo, lambda a=action: self._callback(a), suppress=True)
        self._handles.append(handle)
        return handle

    def clear(self) -> None:
        """Remove every keyboard-package hotkey handle."""
        if not _HAS_KB:
            self._handles.clear()
            return
        for handle in list(self._handles):
            try:
                _kb.remove_hotkey(handle)
            except (KeyError, ValueError):
                pass
        self._handles.clear()


class HotkeyManager(QObject):
    """Each registered hotkey emits `triggered(action_id)` on the Qt main thread."""

    triggered = pyqtSignal(str)
    error = pyqtSignal(str, str)   # action_id, message

    def __init__(self):
        super().__init__()
        self._bindings: dict[str, str] = {}
        self._printscreen_action: str | None = None
        self._backend: _NativeHotkeyBackend | _KeyboardHotkeyBackend | None = None
        self._backend_name = ""

    def apply(self, bindings: dict[str, str], *, printscreen_action: str | None) -> None:
        """Replace all hotkeys. printscreen_action=None disables PrintScreen hook."""
        self.clear()
        self._bindings = dict(bindings)
        self._printscreen_action = printscreen_action
        registrations = [(action, combo) for action, combo in bindings.items() if combo]
        if printscreen_action:
            registrations.append((printscreen_action, "print screen"))
        if not registrations:
            return

        errors = self._apply_with_backend(_NativeHotkeyBackend, registrations, "native")
        if not errors:
            return
        log.warning("native hotkey backend failed; falling back to keyboard backend: %s", errors)
        errors = self._apply_with_backend(_KeyboardHotkeyBackend, registrations, "keyboard")
        for action, message in errors:
            self.error.emit(action, message)

    def clear(self) -> None:
        """Remove every registered hotkey handle owned by this manager."""
        if self._backend is not None:
            self._backend.clear()
        self._backend = None
        self._backend_name = ""

    def refresh(self) -> None:
        """Re-register the last applied hotkeys to recover stale OS hooks."""
        self.apply(self._bindings, printscreen_action=self._printscreen_action)

    def _apply_with_backend(
        self,
        backend_type: type[_NativeHotkeyBackend] | type[_KeyboardHotkeyBackend],
        registrations: list[tuple[str, str]],
        name: str,
    ) -> list[tuple[str, str]]:
        """Try to register every combo using one backend."""
        backend = backend_type(lambda action: self.triggered.emit(action))
        errors: list[tuple[str, str]] = []
        for action, combo in registrations:
            try:
                backend.register(action, combo)
            except Exception as exc:  # noqa: BLE001
                log.warning("hotkey register failed via %s %s=%s: %s", name, action, combo, exc)
                errors.append((action, str(exc)))
        if errors:
            backend.clear()
            return errors
        self._backend = backend
        self._backend_name = name
        return []
