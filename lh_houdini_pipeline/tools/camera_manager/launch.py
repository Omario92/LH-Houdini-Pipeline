"""
lh_houdini_pipeline.tools.camera_manager.launch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Shelf entry point::

    from lh_houdini_pipeline.tools.camera_manager import launch
    launch()
"""

from __future__ import annotations

from typing import Optional

_WINDOW = None  # type: Optional[object]


def launch() -> object:
    """Open the Camera Manager window and return it (cached module-side)."""
    global _WINDOW
    from lh_houdini_pipeline.tools.camera_manager import ui as _ui
    _WINDOW = _ui.launch()
    return _WINDOW
