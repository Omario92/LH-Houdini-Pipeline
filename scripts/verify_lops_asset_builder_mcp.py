"""
Verify LOPs Asset Builder material paths through a running HoudiniMCP server.

Start the Houdini shelf MCP server first, then run:
    python scripts/verify_lops_asset_builder_mcp.py
"""

from __future__ import annotations

import json
import socket
import struct
import textwrap
from typing import Any, Dict


def send_command(cmd_type: str, params: Dict[str, Any] | None = None,
                 host: str = "127.0.0.1", port: int = 9876) -> Dict[str, Any]:
    """Send a command to a running HoudiniMCP plugin server.

    Args:
        cmd_type: HoudiniMCP command type.
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
    """Run the LOPs Asset Builder compatibility smoke through HoudiniMCP.

    Returns:
        Process exit code.
    """
    repo_root = str(__file__).replace("\\", "/").rsplit("/scripts/", 1)[0]
    code = textwrap.dedent(
        """
        import json
        import os
        import shutil
        import sys
        import tempfile

        repo_root = REPO_ROOT
        if repo_root in sys.path:
            sys.path.remove(repo_root)
        sys.path.insert(0, repo_root)
        for module_name in list(sys.modules):
            if module_name == "lh_houdini_pipeline" or module_name.startswith("lh_houdini_pipeline."):
                del sys.modules[module_name]

        import hou
        from lh_houdini_pipeline.tools.lops_asset_builder.core import plan_asset
        from lh_houdini_pipeline.tools.lops_asset_builder.service import build_asset

        stage = hou.node("/stage")
        for child_name in ("mcp_robot_geo", "mcp_robot_mtl", "mcp_robot_assign", "mcp_robot"):
            child = stage.node(child_name)
            if child is not None:
                child.destroy()

        temp_root = tempfile.mkdtemp(prefix="lh_lops_mcp_")
        try:
            geo_path = os.path.join(temp_root, "robot.fbx")
            tex_dir = os.path.join(temp_root, "tex")
            os.makedirs(tex_dir)
            open(geo_path, "w").close()
            open(os.path.join(tex_dir, "texture_pbr_20250901.png"), "w").close()
            open(os.path.join(tex_dir, "texture_pbr_20250901.rat"), "w").close()
            open(os.path.join(tex_dir, "texture_pbr_20250901_metallic.png"), "w").close()
            open(os.path.join(tex_dir, "texture_pbr_20250901_metallic.rat"), "w").close()
            open(os.path.join(tex_dir, "texture_pbr_20250901_roughness.png"), "w").close()
            open(os.path.join(tex_dir, "texture_pbr_20250901_roughness.rat"), "w").close()
            open(os.path.join(tex_dir, "texture_pbr_20250901_normal.png"), "w").close()
            open(os.path.join(tex_dir, "texture_pbr_20250901_normal.rat"), "w").close()

            plan = plan_asset("mcp_robot", geo_path=geo_path, tex_folder=tex_dir)
            assert len(plan.material_plans) == 1
            assert plan.material_plans[0].name == "texture_pbr"
            channels = {img.channel.value: img.file_path for img in plan.material_plans[0].images}
            assert set(channels) == {"baseColor", "metalness", "normal", "roughness"}
            assert channels["baseColor"].endswith("texture_pbr_20250901.rat")
            assert channels["metalness"].endswith("texture_pbr_20250901_metallic.rat")
            assert channels["roughness"].endswith("texture_pbr_20250901_roughness.rat")
            assert channels["normal"].endswith("texture_pbr_20250901_normal.rat")

            result = build_asset(plan)
            matlib = hou.node(result.material_lib)
            assign = hou.node(result.assign)
            material = matlib.node("texture_pbr")
            assert matlib is not None
            assert assign is not None
            assert material is not None
            assert assign.parm("matspecpath1").eval() == "/ASSET/materials/texture_pbr"
            flag = None
            if hasattr(material, "isMaterialFlagSet"):
                flag = material.isMaterialFlagSet()
            elif hasattr(material, "materialFlag"):
                flag = material.materialFlag()
            image_files = sorted(
                child.parm("file").eval()
                for child in material.children()
                if child.type().name() == "mtlximage" and child.parm("file") is not None
            )
            assert image_files and all(path.endswith(".rat") for path in image_files)

            out = {
                "hou": hou.applicationVersionString(),
                "image_files": image_files,
                "matpathprefix": matlib.parm("matpathprefix").eval(),
                "matspecpath1": assign.parm("matspecpath1").eval(),
                "material_node": material.path(),
                "material_flag": flag,
                "materials_built": list(result.materials_built),
                "channels": channels,
            }

            stage_obj = matlib.stage()
            prim = stage_obj.GetPrimAtPath("/ASSET/materials/texture_pbr")
            out["material_prim_valid"] = bool(prim and prim.IsValid())
            print("LH_LOPS_MCP_RESULT=" + json.dumps(out, sort_keys=True))
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)
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
