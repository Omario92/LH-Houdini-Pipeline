"""
lh_houdini_pipeline.tools.camera_manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Create and list cameras in OBJ (/obj 'cam') or Solaris (/stage 'camera').

Composition:

    core (pure)        -> CameraSpec + per-context parm mapping
    houdini.lop        -> node create / set parms
    core.logger        -> logging

Public surface
--------------
* ``CameraSpec`` / ``CameraContext`` / ``ResolutionPreset`` / ``spec_from_preset``
  -- pure, hou-free (tests).
* ``create_camera`` / ``list_cameras`` / ``apply_resolution`` -- hou-side.
* ``launch`` -- open the PySide UI (Houdini only).
"""

from __future__ import annotations

from lh_houdini_pipeline.tools.camera_manager.core import (
    CameraContext,
    CameraSpec,
    ResolutionPreset,
    spec_from_preset,
)
from lh_houdini_pipeline.tools.camera_manager.service import (
    CameraInfo,
    apply_resolution,
    create_camera,
    list_cameras,
)

__all__ = [
    "CameraSpec",
    "CameraContext",
    "ResolutionPreset",
    "spec_from_preset",
    "CameraInfo",
    "create_camera",
    "list_cameras",
    "apply_resolution",
    "launch",
]


_WINDOW = None  # keep a reference so the window is not garbage-collected


def launch(*args, **kwargs):
    """Open the Camera Manager window and return it (cached module-side).

    Imports the ``ui`` submodule directly (never a ``launch`` submodule),
    so the package attribute ``launch`` stays this function across repeated
    calls -- importing a same-named submodule would otherwise shadow it.
    """
    global _WINDOW
    from lh_houdini_pipeline.tools.camera_manager import ui as _ui
    _WINDOW = _ui.launch()
    return _WINDOW
