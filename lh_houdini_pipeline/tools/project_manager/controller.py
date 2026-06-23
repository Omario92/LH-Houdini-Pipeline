"""
lh_houdini_pipeline.tools.project_manager.controller
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Controller bridging the Project Manager UI to the pure ``core`` planner and
the side-effecting ``service`` layer.

The UI imports *only* this controller (never ``core``/``service`` directly),
so the view stays free of business logic.  Communication is via Qt
``Signal``/slot so the UI can react to results without blocking or polling.

Signals
-------
* ``statusChanged(str message, str level)`` -- one-line status; *level* is one
  of ``"info" | "working" | "done" | "error"``.
* ``logMessage(str)``                       -- a line for the log panel.
* ``validationChanged(bool can_create, str message, str level)`` -- result of
  real-time validation; *level* ``"" | "warn" | "error"``.
* ``previewReady(object plan)``             -- a ``ProjectPlan`` to render.
* ``createFinished(object result, object plan)`` -- a ``CreateResult`` + plan.
"""

from __future__ import annotations

from typing import List, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.project_manager import core as _core
from lh_houdini_pipeline.tools.project_manager import service as _service
from lh_houdini_pipeline.tools.project_manager import settings as _settings

_log = get_logger(__name__)

try:  # pragma: no cover - binding choice is environment-specific
    from PySide6 import QtCore  # type: ignore
except ImportError:  # pragma: no cover
    from PySide2 import QtCore  # type: ignore


class ProjectController(QtCore.QObject):
    """Stateless-ish coordinator: validate, preview, and create projects.

    Args:
        parent: Optional Qt parent.
    """

    statusChanged = QtCore.Signal(str, str)
    logMessage = QtCore.Signal(str)
    validationChanged = QtCore.Signal(bool, str, str)
    previewReady = QtCore.Signal(object)
    createFinished = QtCore.Signal(object, object)

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self._settings = _settings.load_settings()

    # -- helpers --------------------------------------------------------

    @staticmethod
    def suggest_name(name: str) -> str:
        """Return the sanitised folder name for a live UI hint (pure)."""
        return _core.sanitize_name(name)

    @staticmethod
    def _parse_csv(text: str) -> List[str]:
        """Split a comma-separated field into a clean list of tokens."""
        return [t.strip() for t in (text or "").split(",") if t.strip()]

    def _template(self, default_structure: bool):
        """Pick the folder template based on the 'default structure' toggle."""
        if default_structure:
            return _core.ProjectTemplate(
                name="user",
                project_folders=self._settings.project_folders,
            )
        # Minimal: project root + assets/shots only, no studio sub-folders.
        return _core.ProjectTemplate(name="minimal", project_folders=())

    def settings(self) -> _settings.ProjectManagerSettings:
        """Return the currently loaded Project Manager settings.

        Returns:
            Settings used by subsequent preview/create operations.
        """
        return self._settings

    def reload_settings(self) -> _settings.ProjectManagerSettings:
        """Reload persistent settings from disk.

        Returns:
            Fresh settings used by subsequent preview/create operations.
        """
        self._settings = _settings.load_settings()
        self.statusChanged.emit(
            "Project folders: " + str(len(self._settings.project_folders)) + " selected.",
            "info",
        )
        return self._settings

    def save_settings(self, folders: List[str]) -> _settings.ProjectManagerSettings:
        """Persist selected project folders and update this controller.

        Args:
            folders: Folder paths selected by the Settings dialog.

        Returns:
            Settings saved to disk and activated for future plans.
        """
        self._settings = _settings.ProjectManagerSettings(
            project_folders=_settings.validate_folders(folders),
        )
        path = _settings.save_settings(self._settings)
        self.statusChanged.emit("Settings saved: " + str(path), "done")
        self.logMessage.emit("Settings -> " + str(path))
        return self._settings

    def reset_settings(self) -> _settings.ProjectManagerSettings:
        """Reset persistent settings to the full default folder set.

        Returns:
            Reset settings saved to disk and activated for future plans.
        """
        _settings.reset_settings()
        return self.reload_settings()

    def build_plan(
        self,
        root: str,
        name: str,
        assets_text: str,
        shots_text: str,
        default_structure: bool = True,
    ):
        """Build a ``ProjectPlan`` from raw UI fields (pure; may raise).

        Returns ``None`` and emits an error status on invalid input.
        """
        try:
            return _core.plan_project(
                root, name,
                assets=self._parse_csv(assets_text),
                shots=self._parse_csv(shots_text),
                template=self._template(default_structure),
            )
        except ValueError as exc:
            self.statusChanged.emit(str(exc), "error")
            return None

    # -- slots (called by the UI) ---------------------------------------

    @QtCore.Slot(str, str)
    def validate(self, root: str, name: str) -> None:
        """Real-time validation; emits :attr:`validationChanged`.

        Rules: root and name required; name must sanitise to something;
        warns (does not block) if the target project folder already exists.
        """
        root = (root or "").strip()
        name = (name or "").strip()
        if not root:
            self.validationChanged.emit(False, "Choose a root directory.", "")
            return
        if not name:
            self.validationChanged.emit(False, "Enter a project name.", "")
            return
        safe = _core.sanitize_name(name)
        if not safe:
            self.validationChanged.emit(False, "Project name has no valid characters.", "error")
            return
        # Existence check (cheap local stat; UI debounces calls).
        try:
            existing = set(_service.scan_projects(root))
        except Exception:  # noqa: BLE001
            existing = set()
        if safe in existing:
            self.validationChanged.emit(
                True, "Project '" + safe + "' already exists -- files will be merged.", "warn")
            return
        self.validationChanged.emit(True, "Ready to create '" + safe + "'.", "")

    @QtCore.Slot(str, str, str, str, bool)
    def preview(self, root: str, name: str, assets_text: str,
                shots_text: str, default_structure: bool) -> None:
        """Build a plan and emit :attr:`previewReady` for the tree view."""
        plan = self.build_plan(root, name, assets_text, shots_text, default_structure)
        if plan is None:
            return
        self.previewReady.emit(plan)
        self.statusChanged.emit("Preview: " + plan.summary(), "info")

    def create(
        self,
        root: str,
        name: str,
        assets_text: str,
        shots_text: str,
        default_structure: bool = True,
        dry_run: bool = False,
        set_job: bool = True,
    ) -> None:
        """Create (or dry-run) the project; emits status/log/createFinished."""
        plan = self.build_plan(root, name, assets_text, shots_text, default_structure)
        if plan is None:
            return
        self.previewReady.emit(plan)

        verb = "Planning" if dry_run else "Creating"
        self.statusChanged.emit(verb + " " + plan.summary() + "...", "working")
        self.logMessage.emit("--- " + verb + " project '" + plan.project + "' ---")
        self.logMessage.emit("Root: " + plan.project_root)

        try:
            result = _service.create_project(plan, dry_run=dry_run)
        except Exception as exc:  # noqa: BLE001
            self.statusChanged.emit("Failed: " + str(exc), "error")
            self.logMessage.emit("ERROR: " + str(exc))
            _log.exception("create_project failed")
            return

        for d in result.created:
            self.logMessage.emit(("[plan] " if dry_run else "[made] ") + d)
        for path, err in result.failed:
            self.logMessage.emit("[FAIL] " + path + " -> " + err)

        job_msg = ""
        if not dry_run and result.ok and set_job:
            if _service.set_houdini_job(plan.project_root):
                job_msg = "  |  $JOB set"
                self.logMessage.emit("$JOB -> " + plan.project_root)

        level = "done" if result.ok else "error"
        self.statusChanged.emit(plan.summary() + "  |  " + result.summary() + job_msg, level)
        self.createFinished.emit(result, plan)
