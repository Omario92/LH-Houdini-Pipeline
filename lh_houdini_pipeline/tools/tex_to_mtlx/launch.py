"""
lh_houdini_pipeline.tools.tex_to_mtlx.launch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Single entry point for launching the TexToMtlx UI from a Houdini shelf.

Usage (shelf tool / Python Source Editor)::

    from lh_houdini_pipeline.tools.tex_to_mtlx import launch
    launch()

Keeping the launcher separate from ``ui`` lets the shelf import succeed even
while iterating on widget internals, and gives one stable import path.
"""

from __future__ import annotations

from typing import Optional

# Keep a module-level reference so the window is not garbage-collected the
# instant the shelf script finishes running.
_WINDOW = None  # type: Optional[object]


def launch() -> object:
    """Open the TexToMtlx window and return it (also cached module-side)."""
    global _WINDOW
    from lh_houdini_pipeline.tools.tex_to_mtlx import ui as _ui
    _WINDOW = _ui.launch()
    return _WINDOW
