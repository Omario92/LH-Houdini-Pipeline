"""
lh_houdini_pipeline.tools.houdini_ai_assistant.tools.node_tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
AI tools related to node management, parameter manipulation, layout,
and Python script runs.
"""

from __future__ import annotations

import io
import os
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
    """Tool to scaffold a basic Houdini Digital Asset network setup and compile HDA definitions."""

    @property
    def name(self) -> str:
        return "generate_hda_scaffold"

    @property
    def description(self) -> str:
        return (
            "Create a new subnet-like node, package it into an HDA library file on disk, "
            "promote custom parameter templates, and inject PythonModule or Event Scripts."
        )

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["parent_path", "node_type", "hda_name"],
            "properties": {
                "parent_path": {
                    "type": "string",
                    "description": "Absolute path to parent network (e.g., '/obj' or '/stage')."
                },
                "node_type": {
                    "type": "string",
                    "description": "Subnet-like node type to package (e.g., 'subnet', 'geo', 'materiallibrary')."
                },
                "hda_name": {
                    "type": "string",
                    "description": "Unique node type name for the HDA (e.g., 'sop_terrain_gen')."
                },
                "hda_label": {
                    "type": "string",
                    "description": "User-facing label for the HDA."
                },
                "hda_file_path": {
                    "type": "string",
                    "description": "Optional absolute path to write the .hda file. Defaults to $HIP/otls/name.hda."
                },
                "python_module": {
                    "type": "string",
                    "description": "Optional Python script to package inside the HDA's 'PythonModule' section."
                },
                "on_created": {
                    "type": "string",
                    "description": "Optional Python script to package inside the HDA's 'OnCreated' event section."
                },
                "parameters": {
                    "type": "array",
                    "description": "List of parameter templates to promote and lay out on the HDA interface.",
                    "items": {
                        "type": "object",
                        "required": ["name", "type"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Unique variable name for the parameter."
                            },
                            "label": {
                                "type": "string",
                                "description": "Human-readable label."
                            },
                            "type": {
                                "type": "string",
                                "enum": ["float", "int", "string", "toggle", "button", "file"],
                                "description": "Parameter data type."
                            },
                            "default": {
                                "type": "string",
                                "description": "Default starting value."
                            },
                            "min_range": {
                                "type": "number",
                                "description": "Slider minimum limit."
                            },
                            "max_range": {
                                "type": "number",
                                "description": "Slider maximum limit."
                            },
                            "callback_script": {
                                "type": "string",
                                "description": "Python snippet to run on change/click (e.g., 'hou.phm().my_callback(kwargs[\"node\"])')."
                            },
                            "help_text": {
                                "type": "string",
                                "description": "Help tooltip text."
                            }
                        }
                    }
                }
            }
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        import hou
        from lh_houdini_pipeline.houdini.hda import (
            create_hda_from_subnet,
            set_hda_python_module,
            set_hda_event_script,
            set_hda_parm_template_group,
            save_and_reload_hda,
        )

        parent_path = arguments["parent_path"]
        node_type = arguments["node_type"]
        hda_name = arguments["hda_name"]
        hda_label = arguments.get("hda_label", hda_name)
        hda_file_path = arguments.get("hda_file_path")
        python_module_code = arguments.get("python_module")
        on_created_code = arguments.get("on_created")
        parameters_data = arguments.get("parameters", [])

        # 1. Resolve HDA path
        if not hda_file_path:
            hip = hou.getenv("HIP", "")
            otls_dir = os.path.join(hip, "otls")
            hda_file_path = os.path.join(otls_dir, f"{hda_name}.hda")

        try:
            parent = hou.node(parent_path)
            if not parent:
                return {"success": False, "error": f"Parent node not found: '{parent_path}'"}

            # 2. Create the base node subnet
            subnet = parent.createNode(node_type, hda_name)
            
            # 3. Create HDA definition
            definition = create_hda_from_subnet(subnet, hda_file_path, hda_name, hda_label)
            if not definition:
                return {"success": False, "error": f"Failed to package subnet into HDA definition."}

            # 4. Inject script sections
            if python_module_code:
                set_hda_python_module(definition, python_module_code)
            if on_created_code:
                set_hda_event_script(definition, "OnCreated", on_created_code)

            # 5. Build and promote parameter templates
            if parameters_data:
                group = definition.parmTemplateGroup()
                for p_data in parameters_data:
                    template = self._create_parm_template(p_data)
                    if template:
                        group.append(template)
                set_hda_parm_template_group(definition, group)

            # 6. Save and reload
            save_and_reload_hda(definition, subnet)

            return {
                "success": True,
                "node_path": subnet.path(),
                "hda_file_path": hda_file_path,
                "message": f"Successfully created and compiled HDA '{hda_name}' at '{hda_file_path}'."
            }
        except Exception as e:
            return {"success": False, "error": f"HDA scaffolding failed: {e}"}

    def _create_parm_template(self, p_data: Dict[str, Any]) -> Optional[hou.ParmTemplate]:
        """Convert dictionary parameter definitions into native hou.ParmTemplate classes."""
        import hou
        name = p_data["name"]
        label = p_data.get("label", name)
        ptype = p_data["type"].lower()
        default = p_data.get("default")
        help_text = p_data.get("help_text", "")
        callback = p_data.get("callback_script", "")

        template: Optional[hou.ParmTemplate] = None

        if ptype == "float":
            default_val = (float(default),) if default is not None else (0.0,)
            t = hou.FloatParmTemplate(name, label, 1, default_value=default_val, help=help_text)
            min_val = p_data.get("min_range")
            max_val = p_data.get("max_range")
            if min_val is not None and max_val is not None:
                t.setRange(float(min_val), float(max_val))
            template = t
        elif ptype == "int":
            default_val = (int(default),) if default is not None else (0,)
            t = hou.IntParmTemplate(name, label, 1, default_value=default_val, help=help_text)
            min_val = p_data.get("min_range")
            max_val = p_data.get("max_range")
            if min_val is not None and max_val is not None:
                t.setRange(int(min_val), int(max_val))
            template = t
        elif ptype == "string":
            default_val = (str(default),) if default is not None else ("",)
            template = hou.StringParmTemplate(name, label, 1, default_value=default_val, help=help_text)
        elif ptype == "toggle":
            default_val = str(default).lower() in ("true", "1", "yes") if default is not None else False
            template = hou.ToggleParmTemplate(name, label, default_value=default_val, help=help_text)
        elif ptype == "button":
            t = hou.ButtonParmTemplate(name, label, help=help_text)
            template = t
        elif ptype == "file":
            default_val = (str(default),) if default is not None else ("",)
            template = hou.StringParmTemplate(
                name, label, 1, default_value=default_val,
                string_type=hou.stringParmType.FileReference, help=help_text
            )

        if template and callback:
            template.setCallbackScript(callback)
            template.setCallbackScriptLanguage(hou.scriptLanguage.Python)

        return template

