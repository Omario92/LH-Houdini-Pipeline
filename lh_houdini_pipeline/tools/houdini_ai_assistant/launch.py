"""
lh_houdini_pipeline.tools.houdini_ai_assistant.launch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Shelf entry point for the Houdini AI Assistant UI:

    from lh_houdini_pipeline.tools.houdini_ai_assistant import launch
    launch()
"""

from __future__ import annotations

from typing import Optional

_WINDOW = None  # type: Optional[object]


def launch() -> object:
    """Open the Houdini AI Assistant window/panel and return it."""
    global _WINDOW
    from lh_houdini_pipeline.tools.houdini_ai_assistant import ui as _ui
    _WINDOW = _ui.launch()
    return _WINDOW
