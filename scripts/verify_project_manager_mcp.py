"""
Verify Project Manager settings through a running HoudiniMCP TCP server.

This talks to the same localhost bridge used by the MCP tool layer.  Start the
Houdini shelf MCP server first, then run:
    python scripts/verify_project_manager_mcp.py
"""

from __future__ import annotations

import json
import socket
import struct
import sys
import textwrap
from typing import Any, Dict


def send_command(cmd_type: str, params: Dict[str, Any] | None = None,
                 host: str = "127.0.0.1", port: int = 9876) -> Dict[str, Any]:
    """Send a command to a running HoudiniMCP plugin server.

    Args:
        cmd_type: HoudiniMCP command type, such as ``"ping"``.
        params: Optional command parameters.
        host: TCP host for the Houdini plugin server.
        port: TCP port for the Houdini plugin server.

    Returns:
        Decoded JSON response from HoudiniMCP.
    """
    payload = json.dumps({"type": cmd_type, "params": params or {}}).encode("utf-8")
    with socket.create_connection((host, port), timeout=10) as sock:
        sock.sendall(struct.pack(">I", len(payload)) + payload)
        header = _recv_exact(sock, 4)
        msg_len = struct.unpack(">I", header)[0]
        return json.loads(_recv_exact(sock, msg_len).decode("utf-8"))


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    """Read exactly ``size`` bytes from a socket.

    Args:
        sock: Connected socket.
        size: Number of bytes to read.

    Returns:
        Received bytes.

    Raises:
        ConnectionError: If the socket closes early.
    """
    chunks = []
    remaining = size
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("HoudiniMCP socket closed early")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def main() -> int:
    """Run the Project Manager compatibility smoke through HoudiniMCP.

    Returns:
        Process exit code.
    """
    repo_root = str(__file__).replace("\\", "/").rsplit("/scripts/", 1)[0]
    code = textwrap.dedent(
        """
        import json
        import sys

        repo_root = REPO_ROOT
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        else:
            sys.path.remove(repo_root)
            sys.path.insert(0, repo_root)

        for module_name in list(sys.modules):
            if module_name == "lh_houdini_pipeline" or module_name.startswith("lh_houdini_pipeline."):
                del sys.modules[module_name]

        import hou
        from lh_houdini_pipeline.tools.project_manager.controller import ProjectController
        from lh_houdini_pipeline.tools.project_manager.settings import ProjectManagerSettings
        from lh_houdini_pipeline.tools.project_manager.ui import ProjectSettingsDialog

        try:
            from PySide6 import QtWidgets
            qt_binding = "PySide6"
        except ImportError:
            from PySide2 import QtWidgets
            qt_binding = "PySide2"

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        controller = ProjectController()
        controller._settings = ProjectManagerSettings(project_folders=("geo", "tex"))

        plan = controller.build_plan("C:/tmp", "mcp settings smoke", "", "", True)
        assert plan is not None
        assert plan.project_root + "/geo" in plan.directories
        assert plan.project_root + "/tex" in plan.directories
        assert plan.project_root + "/render" not in plan.directories

        dialog = ProjectSettingsDialog(("geo", "tex"))
        assert dialog.selected_folders() == ["geo", "tex"]
        dialog.set_selected(("geo", "tex", "render"))
        assert "render" in dialog.selected_folders()
        dialog.close()

        result = {
            "hou": hou.applicationVersionString(),
            "qt": qt_binding,
            "project": plan.project,
            "directories": list(plan.directories),
            "dialog_selection": ["geo", "tex", "render"],
        }
        print("LH_PM_MCP_RESULT=" + json.dumps(result, sort_keys=True))
        app.processEvents()
        """
    ).replace("REPO_ROOT", repr(repo_root))

    ping = send_command("ping")
    if ping.get("status") != "success":
        print(json.dumps(ping, indent=2))
        return 1
    response = send_command("execute_code", {"code": code})
    print(json.dumps(response, indent=2))
    return 0 if response.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
