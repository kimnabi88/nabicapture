"""AppController guards for modal settings and capture routing."""

from __future__ import annotations

from src.app import AppController


class _FakeHotkeys:
    """Minimal hotkey manager stub for AppController guard tests."""

    def __init__(self) -> None:
        self.applied: list[tuple[dict, str | None]] = []
        self.clear_count = 0

    def apply(self, bindings: dict, *, printscreen_action: str | None) -> None:
        """Record hotkey apply calls."""
        self.applied.append((dict(bindings), printscreen_action))

    def clear(self) -> None:
        """Record hotkey clear calls."""
        self.clear_count += 1


class _FakeConfig:
    """Small config stub with the keys AppController uses in these tests."""

    def get(self, section: str, key: str | None = None, default=None):
        """Return a configured section or value."""
        data = {
            "hotkeys": {"region": "ctrl+shift+a"},
            "capture": {
                "use_printscreen": True,
                "printscreen_action": "region",
                "hotkey_refresh_ms": 0,
            },
        }
        if key is None:
            return data.get(section, default)
        return data.get(section, {}).get(key, default)


class _FakeTimer:
    """Timer stub used by _apply_hotkeys tests."""

    def stop(self) -> None:
        """Accept stop calls without side effects."""


def _controller() -> AppController:
    """Create an AppController shell without constructing Qt windows."""
    controller = AppController.__new__(AppController)
    controller.config = _FakeConfig()
    controller.hotkeys = _FakeHotkeys()
    controller._settings_open = False
    controller._capture_active = False
    controller._last_mode = "region"
    controller._hotkey_refresh_timer = _FakeTimer()
    controller.main_window = type("MainWindowStub", (), {"hide": lambda self: None})()
    return controller


def test_capture_request_is_ignored_while_settings_open() -> None:
    """Global hotkey capture must not start while the settings dialog is modal."""
    controller = _controller()
    controller._settings_open = True
    controller.on_capture_requested("region")

    assert controller._capture_active is False


def test_apply_hotkeys_clears_while_settings_open() -> None:
    """Hotkeys stay disabled while the settings dialog is open."""
    controller = _controller()
    controller._settings_open = True
    controller._apply_hotkeys()

    assert controller.hotkeys.clear_count == 1
    assert controller.hotkeys.applied == []
