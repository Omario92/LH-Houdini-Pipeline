"""
lh_houdini_pipeline.tools.houdini_ai_assistant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A production-ready Houdini AI Assistant panel for scene exploration, USD/Solaris code generation,
debugging, and automated HDA architectural scaffolding using PySide6.

Composition & Layering:
    core/client.py       -> Pure Python LLM Clients (no hou)
    config.py            -> Configurations
    utils/async_utils.py -> QThread asynchronous LLM invocation
    ui/panel.py          -> Main PySide6 UI Panel
    tools/               -> Agent tool registration

Public surface:
--------------
* ``launch`` -- Open or register the panel inside Houdini (PySide6)
"""

from __future__ import annotations

from typing import Optional, Any

__all__ = ["launch"]

_PANEL = None  # keep a reference to the active widget to prevent GC


def launch(*args: Any, **kwargs: Any) -> object:
    """Launch the Houdini AI Assistant dockable panel.

    This function acts as the singleton launcher for the tool.
    """
    global _PANEL
    from lh_houdini_pipeline.tools.houdini_ai_assistant.ui import panel as _panel
    _PANEL = _panel.launch(*args, **kwargs)
    return _PANEL
