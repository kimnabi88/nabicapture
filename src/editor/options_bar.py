"""Per-tool options bar — second toolbar row below the main tool strip."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QFontComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QToolBar,
    QWidget,
)

from src.ui.widgets.color_picker import ColorPicker
from src.ui.widgets.size_slider import SizeSlider

# tool_id → stack page index
_TOOL_PAGE: dict[str, int] = {
    "pen": 0, "highlighter": 0, "eraser": 0,
    "rectangle": 0, "ellipse": 0, "line": 0, "arrow": 0, "speech_bubble": 0,
    "text": 1,
    "mosaic": 2,
    "crop": 3,
}


def _page(tool_id: str) -> int:
    return _TOOL_PAGE.get(tool_id, 0)


class OptionsBar(QToolBar):
    """Context-sensitive options row driven by the active tool."""

    color_changed = pyqtSignal(QColor)
    width_changed = pyqtSignal(int)
    mosaic_size_changed = pyqtSignal(int)
    font_family_changed = pyqtSignal(str)
    font_size_changed = pyqtSignal(int)
    font_bold_changed = pyqtSignal(bool)
    text_commit_requested = pyqtSignal()

    def __init__(self, editor_cfg: dict):
        super().__init__()
        self.setMovable(False)
        self.setObjectName("OptionsBar")

        colors: list[str] = editor_cfg.get("colors", ["#000000"])
        widths: list[int] = editor_cfg.get("pen_widths", [1, 3, 5, 8, 12])
        default_w = int(editor_cfg.get("default_pen_width", widths[len(widths) // 2]))
        default_family = str(editor_cfg.get("default_font_family", "Segoe UI"))
        default_font_size = int(editor_cfg.get("default_font_size", 16))

        self._stack = QStackedWidget()
        self._stack.addWidget(self._make_drawing_page(colors, widths, default_w))   # 0
        self._stack.addWidget(self._make_text_page(colors, default_family, default_font_size))  # 1
        self._stack.addWidget(self._make_mosaic_page(editor_cfg))                   # 2
        self._stack.addWidget(self._make_crop_page())                               # 3

        self.addWidget(self._stack)

    # ------------------------------------------------------------------ pages

    def _make_drawing_page(self, colors: list, widths: list, default_w: int) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(6, 2, 6, 2)
        lay.setSpacing(8)

        lay.addWidget(QLabel("색상"))
        self._draw_color = ColorPicker(colors)
        self._draw_color.color_changed.connect(self.color_changed.emit)
        lay.addWidget(self._draw_color)

        lay.addSpacing(16)

        self._size = SizeSlider(widths, initial=default_w, label="굵기")
        self._size.value_changed.connect(self.width_changed.emit)
        lay.addWidget(self._size)

        lay.addStretch()
        return w

    def _make_text_page(self, colors: list, default_family: str, default_size: int) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(6, 2, 6, 2)
        lay.setSpacing(8)

        lay.addWidget(QLabel("색상"))
        self._text_color = ColorPicker(colors)
        self._text_color.color_changed.connect(self.color_changed.emit)
        lay.addWidget(self._text_color)

        lay.addSpacing(16)

        lay.addWidget(QLabel("글꼴"))
        self._font_family = QFontComboBox()
        self._font_family.setCurrentFont(QFont(default_family))
        self._font_family.setMaximumWidth(200)
        self._font_family.currentFontChanged.connect(
            lambda f: self.font_family_changed.emit(f.family()),
        )
        lay.addWidget(self._font_family)

        lay.addWidget(QLabel("크기"))
        self._font_size = QSpinBox()
        self._font_size.setRange(8, 144)
        self._font_size.setSuffix(" pt")
        self._font_size.setValue(default_size)
        self._font_size.setFixedWidth(68)
        self._font_size.valueChanged.connect(self.font_size_changed.emit)
        lay.addWidget(self._font_size)

        self._bold = QCheckBox("굵게")
        self._bold.toggled.connect(self.font_bold_changed.emit)
        lay.addWidget(self._bold)

        self._commit_btn = QPushButton("입력 ✓")
        self._commit_btn.setToolTip("텍스트 확정 (Ctrl+Enter)")
        self._commit_btn.setFixedWidth(80)
        self._commit_btn.clicked.connect(self.text_commit_requested.emit)
        lay.addWidget(self._commit_btn)

        lay.addStretch()
        return w

    def _make_mosaic_page(self, editor_cfg: dict) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(6, 2, 6, 2)
        lay.setSpacing(8)

        default_m = int(editor_cfg.get("default_mosaic_block_size", 10))

        lay.addWidget(QLabel("블록 크기"))

        self._mosaic_slider = QSlider(Qt.Orientation.Horizontal)
        self._mosaic_slider.setRange(2, 50)
        self._mosaic_slider.setValue(default_m)
        self._mosaic_slider.setFixedWidth(200)
        self._mosaic_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._mosaic_slider.setTickInterval(8)

        self._mosaic_val_lbl = QLabel(f"{default_m} px")
        self._mosaic_val_lbl.setFixedWidth(44)

        self._mosaic_slider.valueChanged.connect(self._on_mosaic_changed)

        lay.addWidget(self._mosaic_slider)
        lay.addWidget(self._mosaic_val_lbl)
        lay.addStretch()
        return w

    def _on_mosaic_changed(self, value: int) -> None:
        self._mosaic_val_lbl.setText(f"{value} px")
        self.mosaic_size_changed.emit(value)

    def _make_crop_page(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(6, 2, 6, 2)
        lay.addWidget(QLabel("드래그로 자를 영역을 선택하고 놓으면 확정됩니다"))
        lay.addStretch()
        return w

    # ---------------------------------------------------------------- public

    def set_tool(self, tool_id: str) -> None:
        self._stack.setCurrentIndex(_page(tool_id))

    def current_color(self) -> QColor:
        if self._stack.currentIndex() == 1:
            return self._text_color.current()
        return self._draw_color.current()

    def current_width(self) -> int:
        return self._size.value()

    def current_font_family(self) -> str:
        return self._font_family.currentFont().family()

    def current_font_size(self) -> int:
        return int(self._font_size.value())

    def current_bold(self) -> bool:
        return self._bold.isChecked()
