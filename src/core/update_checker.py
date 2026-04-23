"""Background update checker — queries GitHub Releases API.

Download flow:
  1. check_async() → runs in daemon thread → emits update_available(ver, url)
  2. Caller downloads via download_update(url, dest) → emits download_progress / download_done
  3. apply_update(new_exe) writes a batch launcher and exits the app
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from src import __version__
from src.utils import logger

log = logger.get(__name__)

_RELEASES_API = "https://api.github.com/repos/kimnabi88/nabicapture/releases/latest"
_HEADERS = {"User-Agent": f"NabiCapture/{__version__}"}


def _parse_version(v: str) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    except ValueError:
        return (0,)


class UpdateChecker(QObject):
    update_available = pyqtSignal(str, str)  # (latest_version, exe_download_url)
    no_update = pyqtSignal()
    check_failed = pyqtSignal(str)

    download_progress = pyqtSignal(int)  # percent 0-100
    download_done = pyqtSignal(str)      # path to downloaded exe
    download_failed = pyqtSignal(str)

    def check_async(self) -> None:
        threading.Thread(target=self._check, daemon=True).start()

    def _check(self) -> None:
        try:
            req = urllib.request.Request(_RELEASES_API, headers=_HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            latest_tag = data.get("tag_name", "")
            latest = latest_tag.lstrip("v")
            exe_url = next(
                (a["browser_download_url"] for a in data.get("assets", [])
                 if a["name"].lower().endswith(".exe")),
                "",
            )
            log.info("update check: current=%s latest=%s", __version__, latest)
            if _parse_version(latest) > _parse_version(__version__):
                self.update_available.emit(latest, exe_url)
            else:
                self.no_update.emit()
        except Exception as exc:  # noqa: BLE001
            log.warning("update check failed: %s", exc)
            self.check_failed.emit(str(exc))

    def download_async(self, url: str) -> None:
        threading.Thread(target=self._download, args=(url,), daemon=True).start()

    def _download(self, url: str) -> None:
        try:
            tmp = Path(tempfile.gettempdir()) / "NabiCapture_update.exe"
            req = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk = 65536
                with open(tmp, "wb") as f:
                    while True:
                        block = resp.read(chunk)
                        if not block:
                            break
                        f.write(block)
                        downloaded += len(block)
                        if total:
                            self.download_progress.emit(int(downloaded * 100 / total))
            self.download_done.emit(str(tmp))
        except Exception as exc:  # noqa: BLE001
            log.exception("update download failed")
            self.download_failed.emit(str(exc))

    @staticmethod
    def apply_update(new_exe: str) -> None:
        """Replace running exe with new_exe via a temporary batch script, then quit."""
        current = sys.executable if getattr(sys, "frozen", False) else ""
        if not current:
            # Dev mode — just open the download folder
            os.startfile(os.path.dirname(new_exe))
            return

        bat = Path(tempfile.gettempdir()) / "nabi_update.bat"
        bat.write_text(
            f'@echo off\n'
            f'timeout /t 2 /nobreak > NUL\n'
            f'move /y "{new_exe}" "{current}"\n'
            f'start "" "{current}"\n'
            f'del "%~f0"\n',
            encoding="ascii",
        )
        subprocess.Popen(["cmd", "/c", str(bat)], creationflags=subprocess.CREATE_NO_WINDOW)
