"""Single-function logger bootstrap."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_initialized = False


def setup(log_dir: Path, level: int = logging.INFO) -> None:
    global _initialized
    if _initialized:
        return
    log_dir.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [
        logging.FileHandler(log_dir / "nabicapture.log", encoding="utf-8"),
    ]
    # Skip StreamHandler in frozen (windowed) exe — avoids phantom console popup
    if not getattr(sys, "frozen", False):
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )
    _initialized = True


def get(name: str) -> logging.Logger:
    return logging.getLogger(name)
