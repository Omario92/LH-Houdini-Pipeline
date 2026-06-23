"""
lh_houdini_pipeline.tools.houdini_ai_assistant.tools.scene_tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
AI tools related to querying scene context and viewports.
"""

from __future__ import annotations

import os
import tempfile
from typing import Any, Dict

from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.base import AITool


class GetSceneContextTool(AITool):
    """Tool that allows the AI to inspect selected nodes and current network paths."""

    @property
    def name(self) -> str:
        return "get_scene_context"

    @property
    def description(self) -> str:
        return (
            "Retrieve detailed information about the active Houdini scene, including the "
            "active network path, selected nodes, node input/output connections, "
            "attributes, active parameter expressions, and compile errors/warnings."
        )

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "include_viewport": {
                    "type": "boolean",
                    "description": "If True, captures a screenshot of the active 3D/Scene viewport.",
                    "default": False
                }
            }
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        from lh_houdini_pipeline.tools.houdini_ai_assistant.utils.context_inspector import get_full_scene_context
        from lh_houdini_pipeline.tools.houdini_ai_assistant.core.context_formatter import format_scene_context
        
        include_viewport = arguments.get("include_viewport", False)
        temp_path = None
        if include_viewport:
            temp_path = os.path.join(tempfile.gettempdir(), "houdini_ai_tool_viewport.png")

        try:
            context_data = get_full_scene_context(temp_path)
            # Format text representation
            markdown_summary = format_scene_context(context_data)
            
            result = {
                "success": True,
                "markdown_summary": markdown_summary
            }
            if context_data.get("viewport_image_b64"):
                result["viewport_image_b64"] = context_data["viewport_image_b64"]
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to retrieve scene context: {e}"
            }
