"""Single-function logger bootstrap."""

from __future__ import annotations

import logging
from pathlib import Path

_initialized = False


def setup(log_dir: Path, level: int = logging.INFO) -> None:
    global _initialized
    if _initialized:
        return
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "profectf.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    _initialized = True


def get(name: str) -> logging.Logger:
    return logging.getLogger(name)
