"""Settings dialog — 4 tabs (일반/캡쳐/저장/단축키)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.config_manager import ConfigManager

CLOSE_OPTIONS = [("minimize", "최소화 (트레이로 이동)"), ("quit", "종료")]
ESC_OPTIONS = [("tray", "트레이로 최소화"), ("quit", "프로그램 종료")]
FORMAT_OPTIONS = ["png", "jpg", "webp", "bmp"]

HOTKEY_LABELS = [
    ("region",     "직접지정"),
    ("window",     "창 캡처"),
    ("monitor",    "단위영역"),
    ("fullscreen", "전체캡처"),
    ("fixed_size", "크기지정"),
    ("last_repeat","마지막 반복"),
]

PS_ACTIONS = [
    ("region",     "직접 지정 캡처"),
    ("window",     "창 캡처"),
    ("monitor",    "단위영역 캡처"),
    ("fullscreen", "전체화면 캡처"),
    ("fixed_size", "크기지정 캡처"),
]

# Keys available in the drop-down (display = uppercase, value = lowercase)
_KEYS: list[str] = (
    [chr(c) for c in range(ord("A"), ord("Z") + 1)] +
    [str(d) for d in range(0, 10)] +
    [f"F{n}" for n in range(1, 13)]
)


def _parse_combo(combo: str) -> tuple[bool, bool, bool, bool, bool, str]:
    """Parse "ctrl+shift+a" → (enabled, win, ctrl, shift, alt, key_upper)."""
    if not combo:
        return False, False, False, False, False, "A"
    parts = [p.strip().lower() for p in combo.split("+")]
    mods = set(parts)
    key_parts = [p for p in parts if p not in {"win", "ctrl", "shift", "alt"}]
    key = key_parts[0].upper() if key_parts else "A"
    return True, "win" in mods, "ctrl" in mods, "shift" in mods, "alt" in mods, key


def _build_combo(combo: str) -> str:
    """Re-assemble a keyboard-library combo string from "ctrl+shift+A"."""
    parts = [p.strip().lower() for p in combo.split("+")]
    # keep canonical order: win ctrl shift alt <key>
    mods = []
    keys = []
    for p in parts:
        if p in {"win", "ctrl", "shift", "alt"}:
            mods.append(p)
        else:
            keys.append(p)
    ordered: list[str] = []
    for m in ("win", "ctrl", "shift", "alt"):
        if m in mods:
            ordered.append(m)
    ordered.extend(keys)
    return "+".join(ordered)


class SettingsDialog(QDialog):
    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsDialog")
        self.setWindowTitle("환경설정")
        self.resize(560, 480)
        self._config = config

        tabs = QTabWidget()
        tabs.addTab(self._build_general(), "일반 설정")
        tabs.addTab(self._build_capture(), "고급 설정")
        tabs.addTab(self._build_hotkeys(), "단축키 설정")
        tabs.addTab(self._build_save(),    "캡쳐목록 설정")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
        )
        reset_btn = QPushButton("기본값으로")
        buttons.addButton(reset_btn, QDialogButtonBox.ButtonRole.ResetRole)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        reset_btn.clicked.connect(self._reset)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

    # ----------------------------------------------------------------- tabs

    def _build_general(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self._run_on_boot = QCheckBox("Windows 시작 시 자동 실행")
        self._run_on_boot.setChecked(bool(self._config.get("startup", "run_on_boot", False)))
        form.addRow(self._run_on_boot)

        self._auto_update = QCheckBox("자동 업데이트 확인 (시작 시 GitHub에서 새 버전 확인)")
        self._auto_update.setChecked(bool(self._config.get("startup", "auto_update", True)))
        form.addRow(self._auto_update)
        self._close_behavior = QComboBox()
        for val, label in CLOSE_OPTIONS:
            self._close_behavior.addItem(label, val)
        cur = self._config.get("startup", "close_behavior", "minimize")
        self._close_behavior.setCurrentIndex(max(0, self._close_behavior.findData(cur)))
        form.addRow("창 닫기(X) 동작", self._close_behavior)

        self._esc_behavior = QComboBox()
        for val, label in ESC_OPTIONS:
            self._esc_behavior.addItem(label, val)
        cur_esc = self._config.get("capture", "esc_behavior", "tray")
        self._esc_behavior.setCurrentIndex(max(0, self._esc_behavior.findData(cur_esc)))
        form.addRow("캡쳐 중 ESC 동작", self._esc_behavior)
        return w

    def _build_capture(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self._copy_to_cb = QCheckBox("캡쳐 후 항상 클립보드로 복사")
        self._copy_to_cb.setChecked(bool(self._config.get("capture", "copy_to_clipboard", True)))
        form.addRow(self._copy_to_cb)
        self._show_magnifier = QCheckBox("드래그 중 확대경 표시 (추후)")
        self._show_magnifier.setChecked(bool(self._config.get("capture", "show_magnifier", True)))
        form.addRow(self._show_magnifier)
        self._guideline_color = QLineEdit(self._config.get("capture", "guideline_color", "#FF5555"))
        self._guideline_color.setPlaceholderText("#RRGGBB")
        form.addRow("가이드라인 색상", self._guideline_color)
        self._guideline_thickness = QSpinBox()
        self._guideline_thickness.setRange(1, 8)
        self._guideline_thickness.setValue(int(self._config.get("capture", "guideline_thickness", 1)))
        form.addRow("가이드라인 굵기", self._guideline_thickness)
        return w

    def _build_hotkeys(self) -> QWidget:
        w = QWidget()
        root = QVBoxLayout(w)
        root.setSpacing(12)

        # ── PrintScreen section ──────────────────────────────────────────
        ps_group = QGroupBox("Print Screen 키 사용")
        ps_lay = QHBoxLayout(ps_group)
        self._ps_enabled = QCheckBox("PrintScreen 키를")
        self._ps_enabled.setChecked(bool(self._config.get("capture", "use_printscreen", True)))
        self._ps_action = QComboBox()
        for val, label in PS_ACTIONS:
            self._ps_action.addItem(label, val)
        cur_ps = self._config.get("capture", "printscreen_action", "region")
        self._ps_action.setCurrentIndex(max(0, self._ps_action.findData(cur_ps)))
        self._ps_action.setEnabled(self._ps_enabled.isChecked())
        self._ps_enabled.toggled.connect(self._ps_action.setEnabled)
        ps_lay.addWidget(self._ps_enabled)
        ps_lay.addWidget(self._ps_action)
        ps_lay.addWidget(QLabel("기능으로 사용"))
        ps_lay.addStretch()
        root.addWidget(ps_group)

        # ── Per-action hotkeys ───────────────────────────────────────────
        hk_group = QGroupBox("캡쳐 단축키 설정")
        hk_inner = QVBoxLayout(hk_group)
        hk_inner.addWidget(QLabel("캡쳐 옵션별 단축키를 지정하거나 끌 수 있습니다."))

        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)

        # Header row
        for col, hdr in enumerate(["", "윈도우 키", "Ctrl", "Shift", "Alt", "키"], 0):
            lbl = QLabel(hdr)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(lbl, 0, col)

        self._hk_rows: dict[str, tuple] = {}
        for row, (key, label) in enumerate(HOTKEY_LABELS, 1):
            cur = str(self._config.get("hotkeys", key, "") or "")
            enabled_f, win_f, ctrl_f, shift_f, alt_f, key_str = _parse_combo(cur)

            chk_en = QCheckBox(label)
            chk_en.setChecked(enabled_f)
            chk_win = QCheckBox()
            chk_win.setChecked(win_f)
            chk_ctrl = QCheckBox()
            chk_ctrl.setChecked(ctrl_f)
            chk_shift = QCheckBox()
            chk_shift.setChecked(shift_f)
            chk_alt = QCheckBox()
            chk_alt.setChecked(alt_f)

            key_box = QComboBox()
            key_box.setFixedWidth(64)
            for k in _KEYS:
                key_box.addItem(k, k.lower())
            idx = key_box.findText(key_str)
            key_box.setCurrentIndex(max(0, idx))

            # Disable modifier/key widgets when action is unchecked
            for widget in (chk_win, chk_ctrl, chk_shift, chk_alt, key_box):
                widget.setEnabled(enabled_f)
            chk_en.toggled.connect(
                lambda on, ws=(chk_win, chk_ctrl, chk_shift, chk_alt, key_box):
                    [w.setEnabled(on) for w in ws]
            )

            grid.addWidget(chk_en,    row, 0)
            grid.addWidget(chk_win,   row, 1, Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(chk_ctrl,  row, 2, Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(chk_shift, row, 3, Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(chk_alt,   row, 4, Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(key_box,   row, 5)

            self._hk_rows[key] = (chk_en, chk_win, chk_ctrl, chk_shift, chk_alt, key_box)

        grid.setColumnStretch(6, 1)
        hk_inner.addLayout(grid)
        root.addWidget(hk_group)
        root.addStretch()
        return w

    def _build_save(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        dir_row = QHBoxLayout()
        self._save_dir = QLineEdit(self._config.get("save", "directory", "./captures"))
        browse = QPushButton("찾아보기")
        browse.clicked.connect(self._pick_dir)
        dir_row.addWidget(self._save_dir)
        dir_row.addWidget(browse)
        form.addRow("저장 위치", dir_row)
        self._format = QComboBox()
        for f in FORMAT_OPTIONS:
            self._format.addItem(f.upper(), f)
        self._format.setCurrentIndex(max(0, self._format.findData(
            self._config.get("save", "format", "png"))))
        form.addRow("이미지 포맷", self._format)
        self._quality = QSpinBox()
        self._quality.setRange(1, 100)
        self._quality.setValue(int(self._config.get("save", "quality", 95)))
        form.addRow("품질 (JPEG/WebP)", self._quality)
        self._pattern = QLineEdit(self._config.get(
            "save", "filename_pattern", "nabi_{yyyy}{MM}{dd}_{HH}{mm}{ss}"))
        form.addRow("파일명 패턴", self._pattern)
        form.addRow(QLabel("토큰: {yyyy} {MM} {dd} {HH} {mm} {ss}"))
        return w

    # ---------------------------------------------------------------- actions

    def _pick_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "저장 폴더 선택", self._save_dir.text())
        if path:
            self._save_dir.setText(path)

    def _accept(self) -> None:
        self._config.update_section("startup", {
            "run_on_boot": self._run_on_boot.isChecked(),
            "close_behavior": self._close_behavior.currentData(),
            "auto_update": self._auto_update.isChecked(),
        })
        self._config.update_section("capture", {
            "copy_to_clipboard": self._copy_to_cb.isChecked(),
            "use_printscreen": self._ps_enabled.isChecked(),
            "printscreen_action": self._ps_action.currentData(),
            "show_magnifier": self._show_magnifier.isChecked(),
            "guideline_color": self._guideline_color.text().strip() or "#FF5555",
            "guideline_thickness": self._guideline_thickness.value(),
            "esc_behavior": self._esc_behavior.currentData(),
        })
        self._config.update_section("save", {
            "directory": self._save_dir.text().strip() or "./captures",
            "format": self._format.currentData(),
            "quality": self._quality.value(),
            "filename_pattern": self._pattern.text().strip() or "nabi_{yyyy}{MM}{dd}_{HH}{mm}{ss}",
        })
        hotkeys: dict[str, str] = {}
        for key, (en, win, ctrl, shift, alt, key_box) in self._hk_rows.items():
            if not en.isChecked():
                hotkeys[key] = ""
                continue
            parts: list[str] = []
            if win.isChecked():   parts.append("win")
            if ctrl.isChecked():  parts.append("ctrl")
            if shift.isChecked(): parts.append("shift")
            if alt.isChecked():   parts.append("alt")
            k = key_box.currentData() or ""
            if k:
                parts.append(k)
            hotkeys[key] = "+".join(parts)
        self._config.update_section("hotkeys", hotkeys)
        self._config.save()
        self.accept()

    def _reset(self) -> None:
        self._config.reset_to_defaults()
        self._config.save()
        self.accept()
