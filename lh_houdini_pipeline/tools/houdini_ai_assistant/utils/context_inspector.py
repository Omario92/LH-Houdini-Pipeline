"""
lh_houdini_pipeline.tools.houdini_ai_assistant.utils.context_inspector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Inspects the active Houdini session and extracts selected nodes, parameter expressions,
geometry attributes, and viewport screenshots.

Safe to import outside Houdini (returns empty/default data in headless environments).
"""

from __future__ import annotations

import base64
import os
from typing import Any, Dict, List, Optional

from lh_houdini_pipeline.core.logger import get_logger

_log = get_logger(__name__)

# Lazy import of hou
HAS_HOU = False
try:
    import hou  # type: ignore[import]
    HAS_HOU = True
except ImportError:
    pass


def is_houdini_available() -> bool:
    """Return True if the hou module is successfully imported."""
    return HAS_HOU


def get_current_desktop() -> str:
    """Return the name of the active desktop layout in Houdini."""
    if not HAS_HOU:
        return "Headless/Standalone Python"
    try:
        return hou.ui.currentDesktop().name()
    except Exception as e:
        _log.debug(f"Failed to get current desktop: {e}")
        return "Unknown Desktop"


def get_current_network_path() -> str:
    """Return the current path of the active network editor workspace."""
    if not HAS_HOU:
        return "/"
    try:
        # Query active network editor
        editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        if editor:
            return editor.pwd().path()
    except Exception as e:
        _log.debug(f"Failed to get current network path: {e}")
    return "/"


def get_selected_nodes_data() -> List[Dict[str, Any]]:
    """Inspect and extract structured details about all currently selected nodes.

    Returns:
        A list of dictionaries containing node info (name, type, connections, errors, etc.)
    """
    if not HAS_HOU:
        return []

    nodes = hou.selectedNodes()
    nodes_data = []

    for node in nodes:
        try:
            path = node.path()
            name = node.name()
            type_name = node.type().name()
            parent = node.parent()
            parent_path = parent.path() if parent else ""

            # Connections
            inputs = []
            for i, input_conn in enumerate(node.inputConnections()):
                if input_conn:
                    inputs.append({
                        "index": i,
                        "input_name": node.inputNames()[i] if i < len(node.inputNames()) else str(i),
                        "connected_to": input_conn.inputNode().path()
                    })

            outputs = []
            for i, output_conn in enumerate(node.outputConnections()):
                if output_conn:
                    outputs.append({
                        "index": i,
                        "connected_to": output_conn.outputNode().path()
                    })

            # Siblings (limit to 15 to conserve tokens)
            siblings = []
            if parent:
                sibling_nodes = [n for n in parent.children() if n != node]
                for s in sibling_nodes[:15]:
                    siblings.append({
                        "name": s.name(),
                        "type": s.type().name()
                    })
                if len(sibling_nodes) > 15:
                    siblings.append({
                        "name": f"... and {len(sibling_nodes) - 15} more siblings",
                        "type": ""
                    })

            # Children (if this is a subnetwork)
            children = []
            child_nodes = node.children()
            if child_nodes:
                for c in child_nodes[:15]:
                    children.append({
                        "name": c.name(),
                        "type": c.type().name()
                    })
                if len(child_nodes) > 15:
                    children.append({
                        "name": f"... and {len(child_nodes) - 15} more children",
                        "type": ""
                    })

            # Errors & Warnings
            errors = node.errors()
            warnings = node.warnings()

            # Parameter Expressions
            expressions = []
            modified_parms = {}
            for parm in node.parms():
                try:
                    # Check if parameter has an active expression
                    if parm.expression() is not None:
                        expressions.append({
                            "name": parm.name(),
                            "label": parm.label(),
                            "expression": parm.expression(),
                            "value": str(parm.eval())
                        })
                except (hou.OperationFailed, AttributeError):
                    pass
                
                # Check if value is modified from default
                if parm.isAtDefault():
                    continue
                modified_parms[parm.name()] = {
                    "label": parm.label(),
                    "value": str(parm.eval())
                }

            # Spare Parameters
            spare_parms = []
            try:
                for spare in node.spareParms():
                    spare_parms.append({
                        "name": spare.name(),
                        "label": spare.label(),
                        "value": str(spare.eval())
                    })
            except Exception:
                pass

            # Geometry Attributes & Groups (SOP / LOP)
            geom_info = {}
            try:
                # If node has geometry method
                geo = node.geometry()
                if geo:
                    geom_info = {
                        "points_count": len(geo.points()),
                        "prims_count": len(geo.prims()),
                        "attributes": {
                            "point": [a.name() for a in geo.pointAttribs()],
                            "primitive": [a.name() for a in geo.primAttribs()],
                            "vertex": [a.name() for a in geo.vertexAttribs()],
                            "global": [a.name() for a in geo.globalAttribs()]
                        },
                        "groups": {
                            "point": [g.name() for g in geo.pointGroups()],
                            "primitive": [g.name() for g in geo.primGroups()],
                            "edge": [g.name() for g in geo.edgeGroups()]
                        }
                    }
            except Exception:
                pass

            # USD Stage Info (if LOP node)
            usd_info = {}
            try:
                # If node has USD stage
                stage = node.stage()
                if stage:
                    root_prims = [p.GetName() for p in stage.GetPseudoRoot().GetChildren()]
                    usd_info = {
                        "root_prims": root_prims[:20],
                        "active_layer": stage.GetRootLayer().identifier if stage.GetRootLayer() else "Anonymous"
                    }
            except Exception:
                pass

            nodes_data.append({
                "path": path,
                "name": name,
                "type": type_name,
                "parent_path": parent_path,
                "inputs": inputs,
                "outputs": outputs,
                "siblings": siblings,
                "children": children,
                "errors": errors,
                "warnings": warnings,
                "expressions": expressions,
                "modified_parms": modified_parms,
                "spare_parms": spare_parms,
                "geometry": geom_info,
                "usd": usd_info
            })

        except Exception as e:
            _log.error(f"Failed to inspect node {node.path() if hasattr(node, 'path') else 'unknown'}: {e}")
            
    return nodes_data


def capture_viewport(temp_path: str) -> Optional[str]:
    """Capture the active viewport viewer and save to temporary file, returning base64.

    Args:
        temp_path: Filepath to write the screen capture to (e.g. .png).

    Returns:
        Base64-encoded string of the captured image, or None if failed.
    """
    if not HAS_HOU:
        return None

    try:
        # Find active Scene Viewer pane
        viewer = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
        if not viewer:
            _log.debug("No active Scene Viewer pane found.")
            return None

        # Grab viewport
        viewport = viewer.curViewport()
        if not viewport:
            _log.debug("No active viewport inside Scene Viewer.")
            return None

        # Save view to temporary image
        viewport.saveImage(temp_path)
        if not os.path.exists(temp_path):
            _log.warning(f"Viewport capture failed; {temp_path} was not created.")
            return None

        # Read file as base64
        with open(temp_path, "rb") as f:
            encoded_bytes = base64.b64encode(f.read())
            
        # Delete temporary file
        try:
            os.remove(temp_path)
        except OSError as oe:
            _log.warning(f"Could not clean up temporary viewport image {temp_path}: {oe}")

        return encoded_bytes.decode("utf-8")

    except Exception as e:
        _log.error(f"Failed to capture viewport screenshot: {e}")
        return None


def get_full_scene_context(temp_img_path: Optional[str] = None) -> Dict[str, Any]:
    """Extract a complete scene context overview.

    Args:
        temp_img_path: Path to write temporary image if viewport capture is requested.

    Returns:
        A dictionary summarizing desktop, current network editor state, and node selection.
    """
    context = {
        "desktop": get_current_desktop(),
        "network_path": get_current_network_path(),
        "selected_nodes": get_selected_nodes_data(),
        "viewport_image_b64": None
    }

    if temp_img_path:
        context["viewport_image_b64"] = capture_viewport(temp_img_path)

    return context
