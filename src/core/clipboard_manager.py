"""Clipboard image writer. Thin wrapper around Qt's clipboard."""

from __future__ import annotations

from PyQt6.QtGui import QGuiApplication, QImage

from src.utils import logger

log = logger.get(__name__)


def copy_image(image: QImage) -> None:
    """Place the image on the system clipboard."""
    QGuiApplication.clipboard().setImage(image)
