"""NabiCapture entry point. Orchestration only — no logic lives here."""

from __future__ import annotations

import sys
import traceback

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox

from src import __app_name__
from src.app import AppController
from src.core.config_manager import ConfigManager
from src.ui.tray_icon import load_app_icon
from src.utils import logger, paths


def _load_stylesheet() -> str:
    path = paths.styles_file()
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _install_exception_hook() -> None:
    """Keep the app alive when a Qt slot raises — log and pop a dialog."""
    log = logger.get("excepthook")

    def _hook(exc_type, exc_value, exc_tb):
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        log.error("unhandled exception:\n%s", msg)
        try:
            QMessageBox.critical(
                None, f"{__app_name__} — 오류", f"{exc_type.__name__}: {exc_value}",
            )
        except Exception:  # noqa: BLE001
            pass

    sys.excepthook = _hook


def main() -> int:
    logger.setup(paths.app_root() / "logs")
    _install_exception_hook()
    config = ConfigManager()

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName(__app_name__)
    qt_app.setQuitOnLastWindowClosed(False)
    qt_app.setStyleSheet(_load_stylesheet())
    qt_app.setWindowIcon(load_app_icon())

    controller = AppController(qt_app, config)
    return controller.start()


if __name__ == "__main__":
    sys.exit(main())
