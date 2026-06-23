"""
lh_houdini_pipeline.tools.houdini_ai_assistant.tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A registry of agentic tools that can be invoked by the LLM client.
"""

from __future__ import annotations

from typing import List

from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.base import AITool
from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.node_tools import (
    CreateNodeTool,
    GenerateHdaScaffoldTool,
    LayoutNetworkTool,
    RunPythonSnippetTool,
    SetParmTool,
)
from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.scene_tools import GetSceneContextTool
from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.pipeline_tools import (
    ProjectManagerCreateTool,
    CameraManagerTurntableTool,
)


def get_default_tools() -> List[AITool]:
    """Return a list of initialized default AITool instances."""
    return [
        GetSceneContextTool(),
        CreateNodeTool(),
        SetParmTool(),
        LayoutNetworkTool(),
        RunPythonSnippetTool(),
        GenerateHdaScaffoldTool(),
        ProjectManagerCreateTool(),
        CameraManagerTurntableTool(),
    ]
