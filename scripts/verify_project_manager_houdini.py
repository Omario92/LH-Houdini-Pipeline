"""
Verify Project Manager settings inside Houdini's Python runtime.

Run with:
    hython scripts/verify_project_manager_houdini.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


def main() -> int:
    """Run Houdini/PySide compatibility checks for Project Manager settings.

    Returns:
        Process exit code: ``0`` for success, ``1`` for failure.
    """
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    import hou  # noqa: PLC0415
    from lh_houdini_pipeline.tools.project_manager.controller import ProjectController
    from lh_houdini_pipeline.tools.project_manager.settings import ProjectManagerSettings
    from lh_houdini_pipeline.tools.project_manager.ui import ProjectSettingsDialog

    try:
        from PySide6 import QtWidgets  # type: ignore  # noqa: PLC0415
        qt_binding = "PySide6"
    except ImportError:
        from PySide2 import QtWidgets  # type: ignore  # noqa: PLC0415
        qt_binding = "PySide2"

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    controller = ProjectController()
    controller._settings = ProjectManagerSettings(project_folders=("geo", "tex"))  # noqa: SLF001
    plan = controller.build_plan(
        str(repo_root),
        "houdini settings smoke",
        "",
        "",
        default_structure=True,
    )
    if plan is None:
        raise AssertionError("controller failed to build a settings-driven plan")
    expected = plan.project_root + "/geo"
    unexpected = plan.project_root + "/render"
    if expected not in plan.directories:
        raise AssertionError("selected folder was not planned: " + expected)
    if unexpected in plan.directories:
        raise AssertionError("unselected folder was planned: " + unexpected)

    dialog = ProjectSettingsDialog(("geo", "tex"))
    selected = dialog.selected_folders()
    if selected != ["geo", "tex"]:
        raise AssertionError("dialog selection mismatch: " + repr(selected))
    dialog.set_selected(("geo", "tex", "render"))
    if "render" not in dialog.selected_folders():
        raise AssertionError("dialog did not update checkbox selection")
    dialog.close()

    with tempfile.TemporaryDirectory(prefix="lh_pm_houdini_", dir=str(repo_root)) as temp_root:
        result_plan = controller.build_plan(
            temp_root,
            "tiny",
            "",
            "",
            default_structure=True,
        )
        if result_plan is None:
            raise AssertionError("controller failed to build temp dry-run plan")
        from lh_houdini_pipeline.tools.project_manager.service import create_project

        result = create_project(result_plan, dry_run=True)
        if not result.ok or not result.dry_run:
            raise AssertionError("dry-run failed: " + result.summary())

    print("hou version:", hou.applicationVersionString())
    print("qt binding:", qt_binding)
    print("planned dirs:", len(plan.directories))
    print("dialog selected:", ", ".join(selected))
    print("dry-run:", result.summary())
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
