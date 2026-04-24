"""Windows-specific utility helpers."""

from __future__ import annotations

import ctypes


def grant_foreground() -> None:
    """Let this process call SetForegroundWindow after releasing overlay focus.

    Must be called BEFORE hide() while the overlay still owns the foreground,
    otherwise Windows will ignore subsequent activateWindow() calls from us.
    """
    try:
        pid = ctypes.windll.kernel32.GetCurrentProcessId()
        ctypes.windll.user32.AllowSetForegroundWindow(pid)
    except Exception:  # noqa: BLE001
        pass
