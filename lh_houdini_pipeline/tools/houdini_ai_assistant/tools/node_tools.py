"""
lh_houdini_pipeline.tools.houdini_ai_assistant.tools.node_tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
AI tools related to node management, parameter manipulation, layout,
and Python script runs.
"""

from __future__ import annotations

import io
import sys
from typing import Any, Dict, List, Optional

from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.base import AITool


class CreateNodeTool(AITool):
    """Tool to create a Houdini node in a specified parent network."""

    @property
    def name(self) -> str:
        return "create_node"

    @property
    def description(self) -> str:
        return "Create a node of a given type in the specified parent path network."

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["parent_path", "node_type"],
            "properties": {
                "parent_path": {
                    "type": "string",
                    "description": "Absolute path to the parent node network (e.g., '/obj' or '/stage')."
                },
                "node_type": {
                    "type": "string",
                    "description": "Type name of the node to create (e.g., 'null', 'geo', 'usdimport')."
                },
                "node_name": {
                    "type": "string",
                    "description": "Optional desired name for the node. If omitted, Houdini defaults apply."
                }
            }
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        import hou
        parent_path = arguments["parent_path"]
        node_type = arguments["node_type"]
        node_name = arguments.get("node_name")

        try:
            parent = hou.node(parent_path)
            if not parent:
                return {"success": False, "error": f"Parent node not found at: '{parent_path}'"}
            
            node = parent.createNode(node_type, node_name)
            node.moveToGoodPosition()
            return {
                "success": True,
                "node_path": node.path(),
                "node_name": node.name()
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to create node: {e}"}


class SetParmTool(AITool):
    """Tool to set one or more parameters on a target node."""

    @property
    def name(self) -> str:
        return "set_parm"

    @property
    def description(self) -> str:
        return "Set one or more parameter values on a target node path."

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["node_path", "parm_values"],
            "properties": {
                "node_path": {
                    "type": "string",
                    "description": "Absolute path to the target node (e.g., '/obj/geo1')."
                },
                "parm_values": {
                    "type": "object",
                    "description": "Dictionary mapping parameter names to their new values (e.g., {'tx': 5.0, 'scale': 2.0})."
                }
            }
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        import hou
        node_path = arguments["node_path"]
        parm_values = arguments["parm_values"]

        try:
            node = hou.node(node_path)
            if not node:
                return {"success": False, "error": f"Target node not found at: '{node_path}'"}
            
            node.setParms(parm_values)
            return {
                "success": True,
                "message": f"Successfully updated parameters on node '{node_path}'."
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to set parameters: {e}"}


class LayoutNetworkTool(AITool):
    """Tool to layout nodes inside a subnetwork path."""

    @property
    def name(self) -> str:
        return "layout_network"

    @property
    def description(self) -> str:
        return "Organize/clean up node layout nodes inside a parent network path."

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["parent_path"],
            "properties": {
                "parent_path": {
                    "type": "string",
                    "description": "Absolute path to parent network whose children will be aligned (e.g., '/obj' or '/stage')."
                }
            }
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        import hou
        parent_path = arguments["parent_path"]

        try:
            parent = hou.node(parent_path)
            if not parent:
                return {"success": False, "error": f"Network path not found: '{parent_path}'"}
            
            parent.layoutChildren()
            return {
                "success": True,
                "message": f"Successfully aligned nodes inside '{parent_path}'."
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to layout network: {e}"}


class RunPythonSnippetTool(AITool):
    """Tool to execute a raw Python code block on the main thread."""

    @property
    def name(self) -> str:
        return "run_python_snippet"

    @property
    def description(self) -> str:
        return "Execute a Python code block safely inside Houdini on the main thread. Always requests user approval."

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["code"],
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python source code snippet to run. Has access to the 'hou' module."
                }
            }
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        import hou
        code = arguments["code"]

        # Catch stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = buffer_out = io.StringIO()
        sys.stderr = buffer_err = io.StringIO()

        exec_globals = {"hou": hou, "sys": sys}
        exec_locals: Dict[str, Any] = {}

        try:
            # Execute Python snippet
            exec(code, exec_globals, exec_locals)
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            stdout_str = buffer_out.getvalue()
            stderr_str = buffer_err.getvalue()

            return {
                "success": True,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "message": "Script executed successfully."
            }
        except Exception as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            return {
                "success": False,
                "error": f"Execution error: {e}",
                "stdout": buffer_out.getvalue(),
                "stderr": buffer_err.getvalue()
            }


class GenerateHdaScaffoldTool(AITool):
    """Tool to scaffold a basic Houdini Digital Asset network setup."""

    @property
    def name(self) -> str:
        return "generate_hda_scaffold"

    @property
    def description(self) -> str:
        return "Scaffold a new Houdini Digital Asset node network structure first, ready to be wrapped in an HDA."

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["parent_path", "node_type", "hda_name"],
            "properties": {
                "parent_path": {
                    "type": "string",
                    "description": "Parent network path (e.g., '/obj' or '/stage')."
                },
                "node_type": {
                    "type": "string",
                    "description": "Base node type for HDA (e.g., 'subnet' or 'geo')."
                },
                "hda_name": {
                    "type": "string",
                    "description": "Unique identifier name for the HDA."
                },
                "hda_label": {
                    "type": "string",
                    "description": "Optional human-readable label."
                }
            }
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        import hou
        parent_path = arguments["parent_path"]
        node_type = arguments["node_type"]
        hda_name = arguments["hda_name"]
        hda_label = arguments.get("hda_label", hda_name)

        try:
            parent = hou.node(parent_path)
            if not parent:
                return {"success": False, "error": f"Parent node not found at: '{parent_path}'"}

            # Create base node subnet
            base_node = parent.createNode(node_type, hda_name)
            
            # Label
            base_node.setComment(f"HDA Scaffold: {hda_label}")
            base_node.moveToGoodPosition()
            
            return {
                "success": True,
                "node_path": base_node.path(),
                "message": f"Scaffold subnet created at {base_node.path()}. Ready for parameter promotions."
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to generate HDA scaffold: {e}"}
