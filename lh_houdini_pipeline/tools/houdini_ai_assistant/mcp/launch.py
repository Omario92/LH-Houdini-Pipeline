"""
lh_houdini_pipeline.tools.houdini_ai_assistant.mcp.launch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Shelf entry point (``LH Pipeline > Houdini MCP``) that starts/stops a
standalone MCP server without opening the AI Assistant panel.

External clients reach it through ``scripts/lh_mcp_stdio.py``. Every
modifying tool still opens the artist approval dialog on the main thread.
Must be called from Houdini's main (UI) thread, e.g. a shelf tool.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.houdini_ai_assistant.mcp import auth as _auth
from lh_houdini_pipeline.tools.houdini_ai_assistant.mcp.server import McpTcpServer

_log = get_logger(__name__)

_SERVER: Optional[McpTcpServer] = None


def _main_window() -> Any:
    """Return Houdini's main Qt window, or ``None`` outside Houdini."""
    try:
        import hou
        return hou.qt.mainWindow()
    except Exception:
        return None


def _approve(name: str, arguments: Dict[str, Any]) -> bool:
    """Ask the artist to approve a modifying tool (main thread).

    Args:
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        ``True`` if approved.
    """
    from lh_houdini_pipeline.tools.houdini_ai_assistant.ui.approval import request_approval
    return request_approval(name, arguments, parent=_main_window())


def _notify(message: str, error: bool = False) -> None:
    """Show *message* in Houdini's status bar (falls back to the log)."""
    (_log.error if error else _log.info)(message)
    try:
        import hou
        severity = hou.severityType.Error if error else hou.severityType.Message
        hou.ui.setStatusMessage(message, severity=severity)
    except Exception:
        pass


def is_running() -> bool:
    """Return whether the standalone shelf server is running."""
    return _SERVER is not None and _SERVER.is_running()


def start(port: int = 14848, pipe_name: Optional[str] = None) -> bool:
    """Start the standalone server (named pipe on Windows + loopback TCP).

    Args:
        port: TCP fallback port.
        pipe_name: Named pipe; defaults to :data:`auth.DEFAULT_PIPE` on Windows.

    Returns:
        ``True`` if the server is running afterwards.
    """
    global _SERVER
    if is_running():
        return True
    if pipe_name is None and os.name == "nt":
        pipe_name = _auth.DEFAULT_PIPE
    server = McpTcpServer(_main_window())
    server.use_thread_dispatch = True  # HOM work + approval on the main thread
    server.approval_callback = _approve
    if not server.start(port=port, pipe_name=pipe_name):
        _notify("Houdini MCP failed to start (already running in another "
                "session or the AI Assistant panel?). See the console log.", error=True)
        return False
    _SERVER = server
    _notify("Houdini MCP running (" + (pipe_name or "tcp") + ", port "
            + str(port) + "). Credential: " + str(server.auth_file))
    return True


def stop() -> None:
    """Stop the standalone server and remove its credential file."""
    global _SERVER
    if _SERVER is not None:
        _SERVER.stop()
        _SERVER = None
    _notify("Houdini MCP stopped.")


def toggle() -> bool:
    """Start the server if stopped, otherwise stop it (shelf button).

    Returns:
        ``True`` if the server is running after the call.
    """
    if is_running():
        stop()
        return False
    return start()
