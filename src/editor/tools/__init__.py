"""Tool registry — single place to obtain tool instances for a canvas."""

from __future__ import annotations

from src.editor.tools.base_tool import BaseTool
from src.editor.tools.crop_tool import CropTool
from src.editor.tools.eraser_tool import EraserTool
from src.editor.tools.mosaic_tool import MosaicTool
from src.editor.tools.pen_tool import HighlighterTool, PenTool
from src.editor.tools.shape_tool import ShapeTool
from src.editor.tools.text_tool import TextTool


def build_tools(canvas, cfg: dict) -> dict[str, BaseTool]:
    """Instantiate one of each concrete tool. Ids match toolbar buttons."""
    hl_width = int(cfg.get("highlighter_width", 18))
    hl_opacity = float(cfg.get("highlighter_opacity", 0.35))
    mosaic_default = int(cfg.get("default_mosaic_block_size", 10))
    font_family = cfg.get("default_font_family", "Segoe UI")
    font_size = int(cfg.get("default_font_size", 16))

    tools: dict[str, BaseTool] = {
        "pen": PenTool(canvas),
        "highlighter": HighlighterTool(canvas, width=hl_width),
        "rectangle": ShapeTool(canvas, "rectangle"),
        "ellipse": ShapeTool(canvas, "ellipse"),
        "line": ShapeTool(canvas, "line"),
        "arrow": ShapeTool(canvas, "arrow"),
        "speech_bubble": ShapeTool(canvas, "speech_bubble"),
        "text": TextTool(canvas, font_family=font_family, font_size=font_size),
        "crop": CropTool(canvas),
        "mosaic": MosaicTool(canvas, block_size=mosaic_default),
        "eraser": EraserTool(canvas),
    }
    tools["highlighter"].opacity = hl_opacity
    return tools
