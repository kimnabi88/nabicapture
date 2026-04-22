"""Image save with config-driven format, quality, and filename pattern."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image
from PyQt6.QtCore import QBuffer, QByteArray, QIODevice
from PyQt6.QtGui import QImage

from src.utils import paths


def _fill_pattern(pattern: str) -> str:
    """Replace {yyyy}{MM}{dd}{HH}{mm}{ss} tokens with zero-padded values."""
    now = datetime.now()
    return (
        pattern.replace("{yyyy}", f"{now.year:04d}")
        .replace("{MM}", f"{now.month:02d}")
        .replace("{dd}", f"{now.day:02d}")
        .replace("{HH}", f"{now.hour:02d}")
        .replace("{mm}", f"{now.minute:02d}")
        .replace("{ss}", f"{now.second:02d}")
    )


def _unique(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    for i in range(2, 9999):
        candidate = path.with_name(f"{stem}_{i}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"cannot find free filename for {path}")


def qimage_to_pil(image: QImage) -> Image.Image:
    """Convert QImage → PIL.Image via an in-memory PNG buffer (lossless)."""
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.ReadWrite)
    image.save(buf, "PNG")
    return Image.open(BytesIO(bytes(buf.data()))).convert("RGBA")


def save_image(image: QImage, save_cfg: dict[str, Any]) -> Path:
    directory = paths.captures_dir(save_cfg.get("directory", "./captures"))
    fmt = save_cfg.get("format", "png").lower()
    quality = int(save_cfg.get("quality", 95))
    pattern = save_cfg.get("filename_pattern", "capture_{yyyy}{MM}{dd}_{HH}{mm}{ss}")

    filename = _fill_pattern(pattern) + f".{fmt}"
    out_path = _unique(directory / filename)

    pil = qimage_to_pil(image)
    if fmt in ("jpg", "jpeg"):
        pil.convert("RGB").save(out_path, format="JPEG", quality=quality)
    elif fmt == "webp":
        pil.save(out_path, format="WEBP", quality=quality)
    elif fmt == "bmp":
        pil.convert("RGB").save(out_path, format="BMP")
    else:
        pil.save(out_path, format="PNG", optimize=True)
    return out_path
