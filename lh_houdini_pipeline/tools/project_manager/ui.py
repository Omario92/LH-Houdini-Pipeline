"""
lh_houdini_pipeline.tools.project_manager.ui
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PySide UI for the Project Manager -- a thin view over ``core`` (pure planning)
and ``service`` (filesystem + ``$JOB``).

No business logic lives here: handlers call ``core.plan_project`` /
``service.create_project`` and only update the preview / status.  Directory
creation is pure Python and fast, so it runs synchronously on the main thread.
"""

from __future__ import annotations

from typing import List, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.project_manager import core as _core
from lh_houdini_pipeline.tools.project_manager import service as _service

_log = get_logger(__name__)

try:  # pragma: no cover - binding choice is environment-specific
    from PySide2 import QtCore, QtWidgets  # type: ignore
    _QT = "PySide2"
except ImportError:  # pragma: no cover
    from PySide6 import QtCore, QtWidgets  # type: ignore
    _QT = "PySide6"


class ProjectManagerWidget(QtWidgets.QWidget):
    """Plan + create a Houdini project folder structure from a few fields."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Project Manager  (MVP)")
        self._plan = None
        self._build_ui()

    # -- construction ---------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble the form, preview list, action buttons and status."""
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self._root_edit = QtWidgets.QLineEdit()
        root_row = QtWidgets.QHBoxLayout()
        browse = QtWidgets.QPushButton("...")
        browse.setFixedWidth(30)
        browse.clicked.connect(self._on_browse)
        rc = QtWidgets.QWidget()
        rc.setLayout(root_row)
        root_row.setContentsMargins(0, 0, 0, 0)
        root_row.addWidget(self._root_edit, 1)
        root_row.addWidget(browse)
        form.addRow("Root:", rc)

        self._name_edit = QtWidgets.QLineEdit()
        self._name_edit.setPlaceholderText("projectName")
        form.addRow("Project:", self._name_edit)

        self._assets_edit = QtWidgets.QLineEdit()
        self._assets_edit.setPlaceholderText("hero, prop_a, env  (comma-separated, optional)")
        form.addRow("Assets:", self._assets_edit)

        self._shots_edit = QtWidgets.QLineEdit()
        self._shots_edit.setPlaceholderText("sh0010, sh0020  (comma-separated, optional)")
        form.addRow("Shots:", self._shots_edit)

        layout.addLayout(form)

        # Options
        opt_row = QtWidgets.QHBoxLayout()
        self._setjob_cb = QtWidgets.QCheckBox("Set $JOB on create")
        self._setjob_cb.setChecked(True)
        preview_btn = QtWidgets.QPushButton("Preview")
        preview_btn.clicked.connect(self._on_preview)
        opt_row.addWidget(self._setjob_cb)
        opt_row.addStretch(1)
        opt_row.addWidget(preview_btn)
        layout.addLayout(opt_row)

        # Preview of planned directories
        self._list = QtWidgets.QListWidget()
        layout.addWidget(self._list, 1)

        # Actions
        btn_row = QtWidgets.QHBoxLayout()
        dry_btn = QtWidgets.QPushButton("Dry-run")
        dry_btn.clicked.connect(lambda: self._create(dry_run=True))
        create_btn = QtWidgets.QPushButton("Create Project")
        create_btn.clicked.connect(lambda: self._create(dry_run=False))
        btn_row.addWidget(dry_btn)
        btn_row.addWidget(create_btn)
        layout.addLayout(btn_row)

        self._status = QtWidgets.QLabel("Ready.")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        self.resize(560, 460)

    # -- handlers -------------------------------------------------------

    def _on_browse(self) -> None:
        """Choose the project root directory."""
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose project root", self._root_edit.text() or ""
        )
        if path:
            self._root_edit.setText(path)

    def _parse_csv(self, text: str) -> List[str]:
        """Split a comma-separated field into a clean list."""
        return [t.strip() for t in text.split(",") if t.strip()]

    def _plan_from_fields(self):
        """Build a ProjectPlan from the form, or ``None`` on bad input."""
        root = self._root_edit.text().strip()
        name = self._name_edit.text().strip()
        if not root:
            self._set_status("Choose a root folder.", error=True)
            return None
        if not name:
            self._set_status("Enter a project name.", error=True)
            return None
        try:
            return _core.plan_project(
                root, name,
                assets=self._parse_csv(self._assets_edit.text()),
                shots=self._parse_csv(self._shots_edit.text()),
            )
        except ValueError as exc:
            self._set_status(str(exc), error=True)
            return None

    def _on_preview(self) -> None:
        """Plan (without writing) and list the directories that would be made."""
        plan = self._plan_from_fields()
        if plan is None:
            return
        self._plan = plan
        self._list.clear()
        for d in plan.directories:
            self._list.addItem(d)
        self._set_status(plan.summary())

    def _create(self, dry_run: bool) -> None:
        """Realise the planned structure on disk (or dry-run)."""
        plan = self._plan_from_fields()
        if plan is None:
            return
        self._plan = plan
        self._list.clear()
        for d in plan.directories:
            self._list.addItem(d)

        result = _service.create_project(plan, dry_run=dry_run)
        msg = plan.summary() + "  |  " + result.summary()
        if not dry_run and result.ok and self._setjob_cb.isChecked():
            if _service.set_houdini_job(plan.project_root):
                msg += "  |  $JOB set"
        self._set_status(msg, error=not result.ok)

    # -- helpers --------------------------------------------------------

    def _set_status(self, message: str, error: bool = False) -> None:
        """Update the status label (red on error)."""
        self._status.setStyleSheet("color: #cc5555;" if error else "")
        self._status.setText(message)


def launch(parent: Optional[object] = None) -> "ProjectManagerWidget":
    """Create, show, and return a :class:`ProjectManagerWidget`."""
    if parent is None:
        parent = _houdini_main_window()
    widget = ProjectManagerWidget(parent)
    widget.setWindowFlags(QtCore.Qt.Window)
    widget.show()
    return widget


def _houdini_main_window() -> Optional[object]:
    """Return Houdini's main Qt window, or ``None`` outside Houdini."""
    try:
        import hou  # noqa: PLC0415
        return hou.qt.mainWindow()
    except Exception:  # noqa: BLE001
        return None
