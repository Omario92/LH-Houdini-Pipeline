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

__all__ = [
    "ProjectPlan",
    "ProjectTemplate",
    "DEFAULT_TEMPLATE",
    "plan_project",
    "work_file_template",
    "CreateResult",
    "create_project",
    "scan_projects",
    "next_work_version",
    "list_work_files",
    "set_houdini_job",
    "launch",
]


def launch(*args, **kwargs):
    """Lazy proxy to the UI launcher (imports PySide only when called)."""
    from lh_houdini_pipeline.tools.project_manager.launch import launch as _l
    return _l()
