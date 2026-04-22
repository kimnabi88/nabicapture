"""Low-level screen grab via mss. Returns QImage (RGBA32)."""

from __future__ import annotations

from dataclasses import dataclass

import mss
from PyQt6.QtGui import QImage


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


def monitors() -> list[Rect]:
    """All real monitors. mss index 0 is the full virtual screen."""
    with mss.mss() as sct:
        mons = sct.monitors
    return [Rect(m["left"], m["top"], m["width"], m["height"]) for m in mons[1:]]


def virtual_screen() -> Rect:
    with mss.mss() as sct:
        m = sct.monitors[0]
    return Rect(m["left"], m["top"], m["width"], m["height"])


def grab(rect: Rect) -> QImage:
    """Capture a physical-pixel rectangle. Returns a deep-copied QImage."""
    region = {
        "left": rect.left,
        "top": rect.top,
        "width": max(1, rect.width),
        "height": max(1, rect.height),
    }
    with mss.mss() as sct:
        shot = sct.grab(region)
    # On little-endian Windows, QImage ARGB32 stores pixels as BB GG RR AA in
    # memory, which matches mss BGRA output byte-for-byte — no swap needed.
    img = QImage(
        bytes(shot.bgra),
        shot.width,
        shot.height,
        shot.width * 4,
        QImage.Format.Format_ARGB32,
    )
    return img.copy()


def grab_fullscreen() -> QImage:
    return grab(virtual_screen())


def grab_monitor(index: int) -> QImage:
    mons = monitors()
    if not 0 <= index < len(mons):
        raise IndexError(f"monitor {index} out of range (have {len(mons)})")
    return grab(mons[index])
