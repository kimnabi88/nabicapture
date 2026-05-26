"""Editor main window — wires canvas + toolbar + options bar + history panel + statusbar."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDockWidget,
    QMainWindow,
    QMessageBox,
)

from src import __app_name__, __version__
from src.core.clipboard_manager import copy_image
from src.core.config_manager import ConfigManager
from src.core.history_manager import CaptureItem, HistoryManager
from src.editor.canvas import Canvas
from src.editor.history_panel import HistoryPanel
from src.editor.options_bar import OptionsBar
from src.editor.status_bar import EditorStatusBar
from src.editor.toolbar import EditorToolbar
from src.editor.tools import build_tools
from src.utils import logger
from src.utils.image_io import save_image

log = logger.get(__name__)


class EditorWindow(QMainWindow):
    saved = pyqtSignal(str)
    settings_requested = pyqtSignal()   # open settings dialog

    def __init__(self, config: ConfigManager, history: HistoryManager):
        super().__init__()
        self._config = config
        self._history = history
        self._shortcuts: list[QShortcut] = []

        editor_cfg = config.get("editor")
        self.setObjectName("EditorMain")
        self.setWindowTitle(f"{__app_name__} v{__version__} - Editor")
        self.resize(1280, 800)

        self._canvas = Canvas()
        self.setCentralWidget(self._canvas)

        self._toolbar = EditorToolbar()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._toolbar)

        # Row 2: per-tool options (color / size / font / mosaic block …)
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)
        self._options = OptionsBar(editor_cfg)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._options)

        self._status = EditorStatusBar()
        self.setStatusBar(self._status)

        thumb = int(editor_cfg.get("thumbnail_size", 96))
        self._panel = HistoryPanel(history, thumbnail_size=thumb)
        dock = QDockWidget("캡쳐 리스트", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        dock.setWidget(self._panel)
        dock.setMinimumWidth(200)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

        self._tools = build_tools(self._canvas, editor_cfg)
        self._wire()
        self._toolbar.select_tool("pen")

    # --- wiring ---------------------------------------------------------
    def _wire(self) -> None:
        # Toolbar: tool selection + global actions
        self._toolbar.tool_selected.connect(self._on_tool_selected)
        self._toolbar.undo_requested.connect(lambda: self._canvas.undo_stack.undo())
        self._toolbar.redo_requested.connect(lambda: self._canvas.undo_stack.redo())
        self._toolbar.save_requested.connect(self.save_current)
        self._toolbar.copy_requested.connect(self.copy_current)
        self._toolbar.settings_requested.connect(self.settings_requested.emit)
        self._toolbar.zoom_in_requested.connect(self._canvas.zoom_in)
        self._toolbar.zoom_out_requested.connect(self._canvas.zoom_out)
        self._toolbar.zoom_actual_requested.connect(self._canvas.zoom_actual)
        self._toolbar.zoom_fit_requested.connect(self._canvas.zoom_fit)
        self._toolbar.zoom_percent_requested.connect(self._canvas.set_zoom_percent)

        # Options bar: per-tool parameter changes
        self._options.color_changed.connect(self._on_color)
        self._options.width_changed.connect(self._on_width)
        self._options.mosaic_size_changed.connect(self._on_mosaic_size)
        self._options.font_family_changed.connect(self._on_font_family)
        self._options.font_size_changed.connect(self._on_font_size)
        self._options.font_bold_changed.connect(self._on_font_bold)
        self._options.text_commit_requested.connect(self._on_text_commit)

        self._canvas.base_changed.connect(self._status.set_size)
        self._canvas.zoom_changed.connect(self._toolbar.set_zoom_percent)
        self._canvas.zoom_changed.connect(self._status.set_zoom)

        self._panel.item_activated.connect(self._on_panel_activated)
        self._panel.item_deleted.connect(self._on_panel_deleted)

        self._history.current_changed.connect(self._on_current_changed)

        del_sc = QShortcut(QKeySequence("Delete"), self)
        del_sc.activated.connect(self._delete_selected)

        esc_sc = QShortcut(QKeySequence("Esc"), self)
        esc_sc.activated.connect(self._on_escape)
        self.reload_shortcuts()

    def reload_shortcuts(self) -> None:
        """Rebuild editor-local shortcuts from current configuration."""
        for shortcut in self._shortcuts:
            shortcut.setEnabled(False)
            shortcut.setParent(None)
            shortcut.deleteLater()
        self._shortcuts.clear()
        bindings = self._config.get("editor_shortcuts") or {}
        actions = {
            "zoom_in": self._canvas.zoom_in,
            "zoom_out": self._canvas.zoom_out,
            "zoom_actual": self._canvas.zoom_actual,
            "zoom_fit": self._canvas.zoom_fit,
        }
        for key, slot in actions.items():
            combo = str(bindings.get(key, "") or "")
            if not combo:
                continue
            shortcut = QShortcut(QKeySequence(combo), self)
            shortcut.activated.connect(slot)
            self._shortcuts.append(shortcut)

    # --- tool configuration --------------------------------------------
    def _on_tool_selected(self, tool_id: str) -> None:
        tool = self._tools.get(tool_id)
        if tool is None:
            return
        self._options.set_tool(tool_id)
        tool.set_color(self._options.current_color())
        tool.set_width(self._options.current_width())
        if tool_id == "text":
            if hasattr(tool, "set_font_family"):
                tool.set_font_family(self._options.current_font_family())
            if hasattr(tool, "set_font_size"):
                tool.set_font_size(self._options.current_font_size())
            if hasattr(tool, "set_bold"):
                tool.set_bold(self._options.current_bold())
        self._canvas.set_active_tool(tool)
        self._status.set_info(f"도구: {tool_id}")

    def _on_color(self, color: QColor) -> None:
        self._canvas.active_tool().set_color(color)

    def _on_width(self, width: int) -> None:
        self._canvas.active_tool().set_width(width)

    def _on_mosaic_size(self, size: int) -> None:
        mosaic = self._tools.get("mosaic")
        if mosaic is not None and hasattr(mosaic, "set_block_size"):
            mosaic.set_block_size(size)

    def _on_font_family(self, family: str) -> None:
        text = self._tools.get("text")
        if text is not None and hasattr(text, "set_font_family"):
            text.set_font_family(family)

    def _on_font_size(self, size: int) -> None:
        text = self._tools.get("text")
        if text is not None and hasattr(text, "set_font_size"):
            text.set_font_size(size)

    def _on_font_bold(self, bold: bool) -> None:
        text = self._tools.get("text")
        if text is not None and hasattr(text, "set_bold"):
            text.set_bold(bold)

    def _on_text_commit(self) -> None:
        text = self._tools.get("text")
        if text is not None and hasattr(text, "commit_current"):
            text.commit_current()

    # --- panel handlers -------------------------------------------------
    def _on_panel_activated(self, item_id: int) -> None:
        if self._history.current() and self._history.current().id == item_id:
            return
        self._history.set_current(item_id)

    def _on_panel_deleted(self, item_id: int) -> None:
        self._history.remove(item_id)

    def _on_current_changed(self, item_id: int) -> None:
        cap = self._history.by_id(item_id)
        if cap is None:
            return
        self._canvas.set_image(cap.image)

    def _delete_selected(self) -> None:
        cur = self._history.current()
        if cur is not None:
            self._history.remove(cur.id)

    def _on_escape(self) -> None:
        self.hide()

    # --- public actions -------------------------------------------------
    def copy_current(self) -> None:
        image = self._canvas.render_flat()
        copy_image(image)
        self._status.set_info("클립보드에 복사됨")

    def save_current(self) -> str | None:
        image = self._canvas.render_flat()
        try:
            path = save_image(image, self._config.get("save"))
        except Exception as exc:  # noqa: BLE001
            log.exception("save failed")
            QMessageBox.critical(self, "저장 실패", str(exc))
            return None
        cur = self._history.current()
        if cur is not None:
            cur.saved_path = path
        self._status.set_info(f"저장됨: {path}")
        self.saved.emit(str(path))
        return str(path)

    def open_capture(self, image: QImage, *, auto_copy: bool = False) -> CaptureItem:
        item = CaptureItem(image=image)
        self._history.add(item)
        self.show()
        self.raise_()
        self.activateWindow()
        if auto_copy:
            copy_image(image)
        return item
