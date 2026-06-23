"""
lh_houdini_pipeline.tools.houdini_ai_assistant.tools.pipeline_tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
AI tools for interacting with other pipeline components, such as
the Project Manager and the Camera Manager.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.base import AITool


class ProjectManagerCreateTool(AITool):
    """Tool to scaffold a new pipeline project directory structure."""

    @property
    def name(self) -> str:
        return "project_manager_create_project"

    @property
    def description(self) -> str:
        return (
            "Scaffold a new pipeline project directory tree on disk and set Houdini's $JOB environment "
            "variable to point at the created project. Allows optionally creating initial asset and shot folders."
        )

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["root", "project"],
            "properties": {
                "root": {
                    "type": "string",
                    "description": "Absolute path to the root directory where the project directory will be created (e.g. 'E:/OneDrive/Documents/Claude/Projects')."
                },
                "project": {
                    "type": "string",
                    "description": "Name of the project. Sanitized automatically into a valid filesystem folder name."
                },
                "assets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of asset names to scaffold directories for (under assets/ folder)."
                },
                "shots": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of shot names to scaffold directories for (under shots/ folder)."
                }
            }
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        from lh_houdini_pipeline.tools.project_manager.core import plan_project
        from lh_houdini_pipeline.tools.project_manager.service import create_project, set_houdini_job

        root = arguments["root"]
        project = arguments["project"]
        assets = arguments.get("assets", [])
        shots = arguments.get("shots", [])

        try:
            plan = plan_project(root, project, assets=assets, shots=shots)
            result = create_project(plan, dry_run=False)
            
            if result.ok:
                # Attempt to set Houdini $JOB variable
                job_set = set_houdini_job(plan.project_root)
                return {
                    "success": True,
                    "message": f"Successfully created project structure for '{plan.project}' at '{plan.project_root}'.",
                    "summary": result.summary(),
                    "job_set": job_set,
                    "directories": list(plan.directories)
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create project directory structure. Details: {result.failed}"
                }
        except Exception as e:
            return {"success": False, "error": f"Exception encountered: {e}"}


class CameraManagerTurntableTool(AITool):
    """Tool to create a 360-degree lookdev turntable camera in Solaris /stage."""

    @property
    def name(self) -> str:
        return "camera_manager_create_turntable"

    @property
    def description(self) -> str:
        return (
            "Create a 360-degree native USD turntable camera in the Solaris /stage network. "
            "Keyframes its translate and rotate values to orbit a target node or a specific coordinate center."
        )

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the camera node (defaults to 'turntable_cam')."
                },
                "total_frames": {
                    "type": "integer",
                    "description": "Total frames for one full 360-degree rotation (defaults to 120)."
                },
                "start_frame": {
                    "type": "integer",
                    "description": "The starting frame number (defaults to 1)."
                },
                "pitch_deg": {
                    "type": "number",
                    "description": "Downward angle pitch of camera in degrees (defaults to 20.0)."
                },
                "focal_length": {
                    "type": "number",
                    "description": "Camera focal length in mm (defaults to 35.0)."
                },
                "aperture": {
                    "type": "number",
                    "description": "Camera horizontal and vertical aperture in mm (defaults to 10.0, generating a 1:1 aspect ratio)."
                },
                "center": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 3,
                    "maxItems": 3,
                    "description": "The explicit center of rotation [x, y, z] to orbit (defaults to [0, 0, 0])."
                },
                "radius": {
                    "type": "number",
                    "description": "The orbit radius from the rotation center (defaults to 10.0)."
                },
                "target_path": {
                    "type": "string",
                    "description": "Optional path to a LOP node in the scene. If provided, center and radius are automatically calculated from bounds."
                },
                "parent_path": {
                    "type": "string",
                    "description": "Optional parent network path to build the camera node inside (defaults to '/stage')."
                }
            }
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        from lh_houdini_pipeline.tools.camera_manager.core import TurntableSpec
        from lh_houdini_pipeline.tools.camera_manager.service import create_turntable

        # Parse spec arguments
        spec_kwargs = {}
        for key in ("total_frames", "start_frame", "pitch_deg", "focal_length", "aperture", "name"):
            if key in arguments:
                spec_kwargs[key] = arguments[key]
        
        spec = TurntableSpec(**spec_kwargs)

        center = tuple(arguments.get("center", (0.0, 0.0, 0.0)))
        radius = arguments.get("radius", 10.0)
        parent_path = arguments.get("parent_path", "/stage")
        target_path = arguments.get("target_path")
        name = arguments.get("name")

        try:
            cam_path = create_turntable(
                spec=spec,
                center=center,
                radius=radius,
                parent_path=parent_path,
                target_path=target_path,
                name=name
            )

            if cam_path:
                return {
                    "success": True,
                    "message": f"Successfully created turntable camera node at '{cam_path}' orbiting '{target_path or center}' over {spec.total_frames} frames.",
                    "node_path": cam_path
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create turntable camera node (create_turntable service returned None)."
                }
        except Exception as e:
            return {"success": False, "error": f"Exception encountered: {e}"}
