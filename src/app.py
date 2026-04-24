"""Application coordinator — wires managers and windows together.

Kept deliberately thin: this is pure orchestration, not logic.
"""

from __future__ import annotations

import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox, QSystemTrayIcon

try:
    import winreg as _winreg
    _HAS_WINREG = True
except ImportError:
    _HAS_WINREG = False

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_REG_NAME = "NabiCapture"


def _apply_run_on_boot(enable: bool) -> None:
    """Write/delete HKCU Run key. Only works in frozen (exe) mode."""
    if not _HAS_WINREG or not getattr(sys, "frozen", False):
        return
    try:
        key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, _winreg.KEY_SET_VALUE)
        if enable:
            _winreg.SetValueEx(key, _APP_REG_NAME, 0, _winreg.REG_SZ, f'"{sys.executable}"')
        else:
            try:
                _winreg.DeleteValue(key, _APP_REG_NAME)
            except FileNotFoundError:
                pass
        _winreg.CloseKey(key)
    except Exception as exc:  # noqa: BLE001
        from src.utils import logger
        logger.get(__name__).warning("run_on_boot registry update failed: %s", exc)

from src.capture import screen_capture
from src.capture.fixed_size_capture import FixedSizeSelector, SizeDialog
from src.capture.region_selector import RegionSelector
from src.capture.window_capture import WindowPicker
from src.core.config_manager import ConfigManager
from src.core.history_manager import HistoryManager
from src.core.hotkey_manager import HotkeyManager
from src.core.update_checker import UpdateChecker
from src.editor.editor_window import EditorWindow
from src.ui.main_window import MainWindow
from src.ui.tray_icon import TrayIcon
from src.utils import logger

log = logger.get(__name__)


class AppController:
    """Hub that owns managers and windows. Instantiated from main.py."""

    def __init__(self, qt_app: QApplication, config: ConfigManager):
        self.qt_app = qt_app
        self.config = config

        history_max = int(config.get("editor", "history_max_items", 50) or 50)
        self.history = HistoryManager(max_items=history_max)

        self.main_window = MainWindow(
            close_behavior=config.get("startup", "close_behavior", "minimize"),
        )
        self.editor_window = EditorWindow(config, self.history)
        self.hotkeys = HotkeyManager()
        self.tray = TrayIcon() if QSystemTrayIcon.isSystemTrayAvailable() else None

        self._region_selector: RegionSelector | None = None
        self._window_picker: WindowPicker | None = None
        self._fixed_selector: FixedSizeSelector | None = None
        self._last_mode: str = "region"
        self._updater = UpdateChecker()
        self._settings_dlg: QDialog | None = None

        self._wire()
        self._apply_hotkeys()
        if self.tray is not None:
            self.tray.show()

    # --- setup ---------------------------------------------------------
    def _wire(self) -> None:
        self.main_window.capture_requested.connect(self.on_capture_requested)
        self.main_window.settings_requested.connect(self.on_settings_requested)
        self.main_window.close_intent.connect(self._quit)

        self.editor_window.settings_requested.connect(self.on_settings_requested)

        self.config.changed.connect(self._on_config_changed)
        self.hotkeys.triggered.connect(self.on_capture_requested)

        if self.tray is not None:
            self.tray.show_main_requested.connect(self._show_main)
            self.tray.capture_requested.connect(self.on_capture_requested)
            self.tray.reconnect_hotkeys_requested.connect(self._apply_hotkeys)
            self.tray.quit_requested.connect(self._quit)

    def _apply_hotkeys(self) -> None:
        bindings = self.config.get("hotkeys") or {}
        use_ps = bool(self.config.get("capture", "use_printscreen", True))
        ps_action = str(self.config.get("capture", "printscreen_action", "region")) if use_ps else None
        self.hotkeys.apply(bindings, printscreen_action=ps_action)

    def _on_config_changed(self, section: str) -> None:
        if section in ("startup", "*"):
            self.main_window.set_close_behavior(
                self.config.get("startup", "close_behavior", "minimize"),
            )
            _apply_run_on_boot(bool(self.config.get("startup", "run_on_boot", False)))
        if section in ("editor", "*"):
            self.history.set_max_items(
                int(self.config.get("editor", "history_max_items", 50) or 50),
            )
        if section in ("hotkeys", "capture", "*"):
            self._apply_hotkeys()

    # --- capture routing ----------------------------------------------
    def on_capture_requested(self, mode: str) -> None:
        log.info("capture requested: %s", mode)
        if mode == "new":
            mode = self._last_mode
        else:
            self._last_mode = mode

        # Close settings dialog if open — modal loop blocks overlay focus/keyboard.
        if self._settings_dlg is not None:
            self._settings_dlg.reject()
            self._settings_dlg = None

        was_visible = self.main_window.isVisible()
        self.main_window.hide()
        delay = 80 if was_visible else 0
        QTimer.singleShot(delay, lambda: self._run_capture(mode))

    def _run_capture(self, mode: str) -> None:
        try:
            if mode == "region":
                self._start_region_selection()
                return
            if mode == "window":
                self._start_window_picker()
                return
            if mode == "fixed_size":
                self._start_fixed_size()
                return
            if mode == "fullscreen":
                image = screen_capture.grab_fullscreen()
            elif mode == "monitor":
                image = screen_capture.grab_monitor(0)
            else:
                log.warning("unsupported capture mode: %s", mode)
                self._show_main()
                return
        except Exception as exc:  # noqa: BLE001
            log.exception("capture failed")
            QMessageBox.critical(self.main_window, "캡쳐 실패", str(exc))
            self._show_main()
            return

        self._deliver_image(image)

    # --- region / window / fixed ---------------------------------------
    def _start_region_selection(self) -> None:
        cap_cfg = self.config.get("capture")
        self._region_selector = RegionSelector(
            guideline_color=cap_cfg.get("guideline_color", "#FF5555"),
            thickness=int(cap_cfg.get("guideline_thickness", 1)),
        )
        self._region_selector.region_selected.connect(self._on_region_selected)
        self._region_selector.cancelled.connect(self._on_capture_cancelled)
        self._region_selector.show()  # show() respects geometry; showFullScreen() locks to primary monitor

    def _on_region_selected(self, rect) -> None:
        try:
            image = screen_capture.grab(rect)
        except Exception as exc:  # noqa: BLE001
            log.exception("region grab failed")
            QMessageBox.critical(self.main_window, "캡쳐 실패", str(exc))
            self._show_main()
            return
        self._deliver_image(image)

    def _start_window_picker(self) -> None:
        self._window_picker = WindowPicker()
        self._window_picker.window_picked.connect(self._on_region_selected)
        self._window_picker.cancelled.connect(self._on_capture_cancelled)
        self._window_picker.show()

    def _start_fixed_size(self) -> None:
        dlg = SizeDialog(self.main_window)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            self._show_main()
            return
        w, h = dlg.values()
        self._fixed_selector = FixedSizeSelector(w, h)
        self._fixed_selector.region_selected.connect(self._on_region_selected)
        self._fixed_selector.cancelled.connect(self._on_capture_cancelled)
        self._fixed_selector.show()

    def _on_capture_cancelled(self) -> None:
        esc_behavior = str(self.config.get("capture", "esc_behavior", "tray"))
        if esc_behavior == "quit":
            self._quit()
        elif self.tray is not None:
            pass  # stay hidden; user accesses via tray icon
        else:
            self._show_main()

    def _deliver_image(self, image: QImage) -> None:
        auto_copy = bool(self.config.get("capture", "copy_to_clipboard", True))
        self.editor_window.open_capture(image, auto_copy=auto_copy)

    # --- settings & lifecycle ------------------------------------------
    def on_settings_requested(self) -> None:
        from src.ui.settings_dialog import SettingsDialog  # local import avoids cycle
        parent = self.editor_window if self.editor_window.isVisible() else self.main_window
        self._settings_dlg = SettingsDialog(self.config, parent)
        self._settings_dlg.finished.connect(lambda _: setattr(self, "_settings_dlg", None))
        self._settings_dlg.exec()

    def _show_main(self) -> None:
        self.main_window.showNormal()
        self.main_window.raise_()
        self.main_window.activateWindow()

    # --- update --------------------------------------------------------
    def _check_update(self) -> None:
        self._updater.update_available.connect(self._on_update_available)
        self._updater.check_async()

    def _on_update_available(self, version: str, url: str) -> None:
        log.info("update available: v%s", version)
        if self.tray is not None:
            self.tray.showMessage(
                "NabiCapture 업데이트",
                f"새 버전 v{version}이 있습니다. 클릭하여 업데이트하세요.",
                self.tray.icon(),
                8000,
            )
            self.tray.messageClicked.connect(lambda: self._start_download(version, url))
        else:
            self._prompt_update(version, url)

    def _prompt_update(self, version: str, url: str) -> None:
        res = QMessageBox.question(
            None,
            "업데이트 있음",
            f"새 버전 v{version}이 있습니다.\n지금 다운로드하고 재시작하시겠습니까?",
        )
        if res == QMessageBox.StandardButton.Yes:
            self._start_download(version, url)

    def _start_download(self, version: str, url: str) -> None:
        self._updater.download_done.connect(self._on_download_done)
        self._updater.download_failed.connect(
            lambda e: QMessageBox.warning(None, "다운로드 실패", e)
        )
        if self.tray is not None:
            self.tray.showMessage("NabiCapture", f"v{version} 다운로드 중...", self.tray.icon(), 4000)
        self._updater.download_async(url)

    def _on_download_done(self, path: str) -> None:
        res = QMessageBox.question(
            None,
            "다운로드 완료",
            "다운로드가 완료됐습니다.\n지금 재시작하여 업데이트를 적용하시겠습니까?",
        )
        if res == QMessageBox.StandardButton.Yes:
            UpdateChecker.apply_update(path)
            self._quit()

    def _quit(self) -> None:
        self.hotkeys.clear()
        self.main_window.force_close()
        if self.tray is not None:
            self.tray.hide()
        self.qt_app.quit()

    def start(self) -> int:
        # Tray-only startup: hotkey or tray menu triggers capture.
        # (Auto-starting capture on launch breaks Windows startup registration.)
        if bool(self.config.get("startup", "auto_update", True)):
            QTimer.singleShot(3000, self._check_update)
        return self.qt_app.exec()
