"""HotkeyManager hook registration and recovery behavior."""

from __future__ import annotations

from src.core import hotkey_manager
from src.core.hotkey_manager import HotkeyManager, _parse_combo


class _FakeKeyboard:
    """Small stand-in for the keyboard module used by HotkeyManager tests."""

    def __init__(self) -> None:
        self.added: list[tuple[str, object, bool]] = []
        self.removed: list[object] = []
        self._next = 0

    def add_hotkey(self, combo: str, callback: object, suppress: bool) -> object:
        """Record a hotkey registration and return a unique handle."""
        self._next += 1
        handle = f"handle-{self._next}"
        self.added.append((combo, callback, suppress))
        return handle

    def remove_hotkey(self, handle: object) -> None:
        """Record a hotkey handle removal."""
        self.removed.append(handle)


def test_printscreen_handle_is_tracked_and_removed(monkeypatch) -> None:
    """PrintScreen registered for the same action must not leak a hook."""
    fake = _FakeKeyboard()
    monkeypatch.setattr(hotkey_manager, "_HAS_WIN32_HOTKEY", False)
    monkeypatch.setattr(hotkey_manager, "_HAS_KB", True)
    monkeypatch.setattr(hotkey_manager, "_kb", fake)

    manager = HotkeyManager()
    manager.apply({"region": "ctrl+shift+a"}, printscreen_action="region")
    manager.clear()

    assert [row[0] for row in fake.added] == ["ctrl+shift+a", "print screen"]
    assert fake.removed == ["handle-1", "handle-2"]


def test_refresh_replaces_existing_registered_handles(monkeypatch) -> None:
    """Refresh must clear stale handles before re-registering saved bindings."""
    fake = _FakeKeyboard()
    monkeypatch.setattr(hotkey_manager, "_HAS_WIN32_HOTKEY", False)
    monkeypatch.setattr(hotkey_manager, "_HAS_KB", True)
    monkeypatch.setattr(hotkey_manager, "_kb", fake)

    manager = HotkeyManager()
    manager.apply({"window": "ctrl+shift+w"}, printscreen_action=None)
    manager.refresh()

    assert [row[0] for row in fake.added] == ["ctrl+shift+w", "ctrl+shift+w"]
    assert fake.removed == ["handle-1"]


def test_native_combo_parser_supports_existing_bindings() -> None:
    """Native parser must support user-facing combo strings."""
    ctrl_shift_c = _parse_combo("ctrl+shift+c")
    print_screen = _parse_combo("print screen")

    assert ctrl_shift_c.vk == ord("C")
    assert ctrl_shift_c.modifiers == hotkey_manager.MOD_CONTROL | hotkey_manager.MOD_SHIFT
    assert print_screen.vk == 0x2C
    assert print_screen.modifiers == 0
