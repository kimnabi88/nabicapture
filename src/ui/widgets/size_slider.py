"""Discrete size selector — stepped slider + numeric label."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSlider, QWidget


class SizeSlider(QWidget):
    value_changed = pyqtSignal(int)

    def __init__(self, values: list[int], initial: int | None = None, label: str = "굵기"):
        super().__init__()
        self._values = list(values)
        start_idx = 0
        if initial is not None and initial in self._values:
            start_idx = self._values.index(initial)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(QLabel(label))

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setFixedWidth(100)
        self._slider.setMinimum(0)
        self._slider.setMaximum(len(self._values) - 1)
        self._slider.setValue(start_idx)
        self._slider.valueChanged.connect(self._on_change)
        layout.addWidget(self._slider)

        self._readout = QLabel(str(self._values[start_idx]))
        self._readout.setFixedWidth(26)
        layout.addWidget(self._readout)

    def value(self) -> int:
        return self._values[self._slider.value()]

    def _on_change(self, idx: int) -> None:
        v = self._values[idx]
        self._readout.setText(str(v))
        self.value_changed.emit(v)
