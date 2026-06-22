"""
lh_houdini_pipeline.tools.lops_asset_builder.launch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Shelf entry point for the LOPs Asset Builder UI.

Usage::

    from lh_houdini_pipeline.tools.lops_asset_builder import launch
    launch()
"""

from __future__ import annotations

from typing import Optional

_WINDOW = None  # type: Optional[object]


def launch() -> object:
    """Open the LOPs Asset Builder window and return it (cached module-side)."""
    global _WINDOW
    from lh_houdini_pipeline.tools.lops_asset_builder import ui as _ui
    _WINDOW = _ui.launch()
    return _WINDOW
