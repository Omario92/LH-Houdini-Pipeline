"""
lh_houdini_pipeline.tools.project_manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Create and manage Houdini project directory structures.

Composition (no monolith):

    core.path        -> path composition / directory creation
    file.scanner     -> discover existing projects / work files
    file.versioning  -> next work-file version
    core.logger      -> logging

Public surface
--------------
* ``plan_project`` / ``ProjectPlan`` / ``ProjectTemplate`` -- pure (dry-run + tests)
* ``create_project`` / ``scan_projects`` / ``next_work_version`` -- filesystem
* ``set_houdini_job`` -- sets $JOB (Houdini only, lazy)
* ``launch`` -- open the PySide UI (Houdini only)

Everything except ``set_houdini_job`` / ``launch`` is hou-free.
"""

from __future__ import annotations

from lh_houdini_pipeline.tools.project_manager.core import (
    DEFAULT_TEMPLATE,
    ProjectPlan,
    ProjectTemplate,
    plan_project,
    sanitize_name,
    work_file_template,
)
from lh_houdini_pipeline.tools.project_manager.service import (
    CreateResult,
    create_project,
    list_work_files,
    next_work_version,
    scan_projects,
    set_houdini_job,
)
from lh_houdini_pipeline.tools.project_manager.settings import (
    ProjectManagerSettings,
    available_folders,
    load_settings,
    preset_full,
    preset_lookdev,
    preset_minimal,
    reset_settings,
    save_settings,
    validate_folders,
)

__all__ = [
    "ProjectPlan",
    "ProjectTemplate",
    "DEFAULT_TEMPLATE",
    "plan_project",
    "sanitize_name",
    "work_file_template",
    "CreateResult",
    "create_project",
    "scan_projects",
    "next_work_version",
    "list_work_files",
    "set_houdini_job",
    "ProjectManagerSettings",
    "available_folders",
    "load_settings",
    "save_settings",
    "reset_settings",
    "validate_folders",
    "preset_full",
    "preset_minimal",
    "preset_lookdev",
    "launch",
]


_WINDOW = None  # keep a reference so the window is not garbage-collected


def launch(*args, **kwargs):
    """Open the Project Manager window and return it (cached module-side).

    Imports the ``ui`` submodule directly (never a ``launch`` submodule),
    so the package attribute ``launch`` stays this function across repeated
    calls -- importing a same-named submodule would otherwise shadow it.
    """
    global _WINDOW
    from lh_houdini_pipeline.tools.project_manager import ui as _ui
    _WINDOW = _ui.launch()
    return _WINDOW
