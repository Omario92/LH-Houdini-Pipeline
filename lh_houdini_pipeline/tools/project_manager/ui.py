"""
lh_houdini_pipeline.tools.project_manager.ui
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Modern dark-theme PySide6 UI for the Project Manager.

The view is deliberately thin: it collects input and renders results, and
talks to :class:`ProjectController` purely through Qt signals/slots -- it never
imports ``core``/``service`` or creates folders itself.  Layout follows the
three-zone design (Configuration / Preview / Actions) with card-style
``QGroupBox`` grouping, drag-and-drop onto the root field, real-time
validation, a folder-tree preview, a status bar, and a collapsible log.

Houdini integration notes are in :func:`launch`.
"""

from __future__ import annotations

from typing import List, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.project_manager.controller import ProjectController

_log = get_logger(__name__)

try:  # pragma: no cover - PySide6 in Houdini 19.5+/20+, PySide2 fallback
    from PySide6 import QtCore, QtGui, QtWidgets  # type: ignore
    _QT = "PySide6"
except ImportError:  # pragma: no cover
    from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore
    _QT = "PySide2"


# ---------------------------------------------------------------------------
# Dark theme stylesheet (Houdini-friendly, blue accent + amber for dry-run)
# ---------------------------------------------------------------------------

_ACCENT = "#4a90d9"
_AMBER = "#e0a33c"

_STYLESHEET = """
* { font-family: "Segoe UI", "Roboto", sans-serif; font-size: 12px; color: #d4d4d4; }
QWidget#pmRoot { background: #2b2b2b; }
QGroupBox {
    background: #323232; border: 1px solid #3c3c3c; border-radius: 8px;
    margin-top: 14px; padding: 10px 12px 12px 12px;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 12px; padding: 2px 8px;
    color: #9aa6b2; font-weight: 600; text-transform: uppercase;
    letter-spacing: 1px; font-size: 11px;
}
QLabel#fieldLabel { color: #b8b8b8; }
QLabel#hintLabel  { color: #6f8db5; font-style: italic; }
QLineEdit, QPlainTextEdit, QTreeWidget {
    background: #232323; border: 1px solid #3a3a3a; border-radius: 5px;
    padding: 5px 7px; selection-background-color: #4a90d9;
}
QLineEdit:focus, QPlainTextEdit:focus { border: 1px solid #4a90d9; }
QLineEdit[dropActive="true"] { border: 1px dashed #4a90d9; background: #25303c; }
QPushButton {
    background: #3a3a3a; border: 1px solid #474747; border-radius: 6px;
    padding: 7px 14px; color: #e0e0e0;
}
QPushButton:hover { background: #444444; }
QPushButton:disabled { background: #2f2f2f; color: #6a6a6a; border-color: #3a3a3a; }
QPushButton#createBtn {
    background: #4a90d9; border: 1px solid #5a9fe0; color: #ffffff; font-weight: 600;
}
QPushButton#createBtn:hover { background: #5a9fe0; }
QPushButton#createBtn:disabled { background: #34465a; color: #7e8b99; border-color: #34465a; }
QPushButton#dryRunBtn { background: #5a4a2c; border: 1px solid #7a6336; color: #f0d6a8; }
QPushButton#dryRunBtn:hover { background: #6d5836; }
QCheckBox { spacing: 7px; }
QCheckBox::indicator { width: 15px; height: 15px; border-radius: 4px;
    border: 1px solid #555; background: #232323; }
QCheckBox::indicator:checked { background: #4a90d9; border-color: #4a90d9; }
QTreeWidget { alternate-background-color: #272727; }
QTreeWidget::item { padding: 2px 0; }
QScrollBar:vertical { background: #2b2b2b; width: 11px; margin: 0; }
QScrollBar::handle:vertical { background: #484848; border-radius: 5px; min-height: 24px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QFrame#statusBar { background: #232323; border: 1px solid #3a3a3a; border-radius: 5px; }
"""

_STATUS_COLORS = {
    "info": "#9aa0a6", "working": _AMBER, "done": "#5cb85c", "error": "#d9534f",
}
_VALID_COLORS = {"": "#6f8db5", "warn": _AMBER, "error": "#d9534f"}


# ---------------------------------------------------------------------------
# Drag-and-drop aware line edit (for the Root Directory field)
# ---------------------------------------------------------------------------

class DropLineEdit(QtWidgets.QLineEdit):
    """A ``QLineEdit`` that accepts a dropped folder and fills itself with it."""

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:  # noqa: N802
        """Accept the drag only if it carries a local directory."""
        if self._first_dir(event.mimeData()) is not None:
            self.setProperty("dropActive", True)
            self._restyle()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QtCore.QEvent) -> None:  # noqa: N802
        """Clear the drop-hover styling."""
        self.setProperty("dropActive", False)
        self._restyle()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:  # noqa: N802
        """Set the field to the dropped folder path."""
        path = self._first_dir(event.mimeData())
        self.setProperty("dropActive", False)
        self._restyle()
        if path:
            self.setText(path)
            event.acceptProposedAction()

    @staticmethod
    def _first_dir(mime: QtCore.QMimeData) -> Optional[str]:
        """Return the first dropped local directory path, or ``None``."""
        if not mime.hasUrls():
            return None
        import os
        for url in mime.urls():
            if url.isLocalFile():
                p = url.toLocalFile()
                if os.path.isdir(p):
                    return p
        return None

    def _restyle(self) -> None:
        """Re-evaluate the dynamic ``dropActive`` style property."""
        self.style().unpolish(self)
        self.style().polish(self)


# ---------------------------------------------------------------------------
# Main widget
# ---------------------------------------------------------------------------

class ProjectManagerUI(QtWidgets.QWidget):
    """Three-zone project scaffolding UI (Configuration / Preview / Actions)."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("pmRoot")
        self.setWindowTitle("Project Manager")
        self.setMinimumSize(640, 680)

        self._controller = ProjectController(self)
        self._can_create = False

        # Debounce timer so validation/preview don't fire on every keystroke.
        self._debounce = QtCore.QTimer(self)
        self._debounce.setInterval(300)
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._refresh_validation_and_preview)

        self._build_ui()
        self._connect_controller()
        self.setStyleSheet(_STYLESHEET)
        self._on_validation(False, "Choose a root and project name.", "")

    # -- construction ---------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble the three zones, action bar, status bar and log panel."""
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 12)
        outer.setSpacing(12)

        outer.addWidget(self._build_config_group())
        outer.addWidget(self._build_preview_group(), 1)
        outer.addWidget(self._build_actions_group())
        outer.addWidget(self._build_log_panel())
        outer.addWidget(self._build_status_bar())

    def _build_config_group(self) -> QtWidgets.QGroupBox:
        """Top zone: root, project name (+live hint), assets, shots."""
        box = QtWidgets.QGroupBox("Project Configuration")
        form = QtWidgets.QGridLayout(box)
        form.setColumnStretch(1, 1)
        form.setVerticalSpacing(9)
        form.setHorizontalSpacing(10)

        # Root + browse (drag & drop enabled)
        form.addWidget(self._label("Root Directory"), 0, 0)
        self._root_edit = DropLineEdit()
        self._root_edit.setPlaceholderText("Drag a folder here or browse...")
        self._root_edit.textChanged.connect(self._queue_refresh)
        browse = QtWidgets.QPushButton("Browse")
        browse.clicked.connect(self._on_browse)
        root_row = QtWidgets.QHBoxLayout()
        root_row.setSpacing(6)
        root_row.addWidget(self._root_edit, 1)
        root_row.addWidget(browse)
        form.addLayout(root_row, 0, 1)

        # Project name + live sanitised hint
        form.addWidget(self._label("Project Name"), 1, 0)
        self._name_edit = QtWidgets.QLineEdit()
        self._name_edit.setPlaceholderText("projectName (required)")
        self._name_edit.textChanged.connect(self._on_name_changed)
        form.addWidget(self._name_edit, 1, 1)
        self._name_hint = QtWidgets.QLabel("")
        self._name_hint.setObjectName("hintLabel")
        form.addWidget(self._name_hint, 2, 1)

        # Assets
        form.addWidget(self._label("Assets"), 3, 0)
        self._assets_edit = QtWidgets.QLineEdit()
        self._assets_edit.setPlaceholderText("hero, prop_a, env   (optional, comma-separated)")
        self._assets_edit.textChanged.connect(self._queue_refresh)
        form.addWidget(self._assets_edit, 3, 1)

        # Shots
        form.addWidget(self._label("Shots"), 4, 0)
        self._shots_edit = QtWidgets.QLineEdit()
        self._shots_edit.setPlaceholderText("sh0010, sh0020   (optional, comma-separated)")
        self._shots_edit.textChanged.connect(self._queue_refresh)
        form.addWidget(self._shots_edit, 4, 1)
        return box

    def _build_preview_group(self) -> QtWidgets.QGroupBox:
        """Middle zone: folder-tree preview of what will be created."""
        box = QtWidgets.QGroupBox("Preview")
        v = QtWidgets.QVBoxLayout(box)
        self._tree = QtWidgets.QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setAlternatingRowColors(True)
        self._tree.setUniformRowHeights(True)
        v.addWidget(self._tree)
        self._preview_count = QtWidgets.QLabel("Enter a project name to preview the structure.")
        self._preview_count.setObjectName("hintLabel")
        v.addWidget(self._preview_count)
        return box

    def _build_actions_group(self) -> QtWidgets.QGroupBox:
        """Bottom zone: options + Dry-run / Create."""
        box = QtWidgets.QGroupBox("Actions & Options")
        v = QtWidgets.QVBoxLayout(box)

        opts = QtWidgets.QHBoxLayout()
        self._setjob_cb = QtWidgets.QCheckBox("Set $JOB on create")
        self._setjob_cb.setChecked(True)
        self._structure_cb = QtWidgets.QCheckBox("Create default folder structure")
        self._structure_cb.setChecked(True)
        self._structure_cb.setToolTip("houdini, geo, tex, usd, render, comp, ref ...")
        self._structure_cb.toggled.connect(self._queue_refresh)
        opts.addWidget(self._setjob_cb)
        opts.addWidget(self._structure_cb)
        opts.addStretch(1)
        v.addLayout(opts)

        btns = QtWidgets.QHBoxLayout()
        preview_btn = QtWidgets.QPushButton("Preview")
        preview_btn.clicked.connect(self._refresh_validation_and_preview)
        self._dryrun_btn = QtWidgets.QPushButton("Dry-run")
        self._dryrun_btn.setObjectName("dryRunBtn")
        self._dryrun_btn.clicked.connect(lambda: self._do_create(dry_run=True))
        self._create_btn = QtWidgets.QPushButton("Create Project")
        self._create_btn.setObjectName("createBtn")
        self._create_btn.clicked.connect(lambda: self._do_create(dry_run=False))
        btns.addWidget(preview_btn)
        btns.addStretch(1)
        btns.addWidget(self._dryrun_btn)
        btns.addWidget(self._create_btn)
        v.addLayout(btns)
        return box

    def _build_log_panel(self) -> QtWidgets.QWidget:
        """Collapsible log area (hidden by default)."""
        wrap = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        self._log_toggle = QtWidgets.QPushButton("Show Log")
        self._log_toggle.setCheckable(True)
        self._log_toggle.toggled.connect(self._on_toggle_log)
        v.addWidget(self._log_toggle, 0, QtCore.Qt.AlignLeft)
        self._log = QtWidgets.QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setFixedHeight(120)
        self._log.setVisible(False)
        v.addWidget(self._log)
        return wrap

    def _build_status_bar(self) -> QtWidgets.QFrame:
        """Bottom status bar: a colored dot + message."""
        bar = QtWidgets.QFrame()
        bar.setObjectName("statusBar")
        h = QtWidgets.QHBoxLayout(bar)
        h.setContentsMargins(10, 6, 10, 6)
        self._status_dot = QtWidgets.QLabel("●")
        self._status_text = QtWidgets.QLabel("Ready.")
        h.addWidget(self._status_dot)
        h.addWidget(self._status_text, 1)
        self._set_status("Ready.", "info")
        return bar

    @staticmethod
    def _label(text: str) -> QtWidgets.QLabel:
        """A right-aligned field label."""
        lbl = QtWidgets.QLabel(text)
        lbl.setObjectName("fieldLabel")
        lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        return lbl

    # -- controller wiring ----------------------------------------------

    def _connect_controller(self) -> None:
        """Connect controller signals to view slots."""
        c = self._controller
        c.statusChanged.connect(self._set_status)
        c.logMessage.connect(self._append_log)
        c.validationChanged.connect(self._on_validation)
        c.previewReady.connect(self._render_preview)

    # -- input handlers -------------------------------------------------

    def _on_browse(self) -> None:
        """Open a directory chooser for the root field."""
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose project root", self._root_edit.text() or "")
        if path:
            self._root_edit.setText(path)

    def _on_name_changed(self, text: str) -> None:
        """Show the live sanitised-name hint, then queue a refresh."""
        safe = self._controller.suggest_name(text)
        if safe and safe != text.strip():
            self._name_hint.setText("→ folder: " + safe)
        else:
            self._name_hint.setText("")
        self._queue_refresh()

    def _queue_refresh(self, *args) -> None:
        """Restart the debounce timer (validation + live preview)."""
        self._debounce.start()

    def _refresh_validation_and_preview(self) -> None:
        """Validate inputs and, when valid, refresh the preview tree."""
        root = self._root_edit.text()
        name = self._name_edit.text()
        self._controller.validate(root, name)
        if root.strip() and self._controller.suggest_name(name):
            self._controller.preview(
                root, name, self._assets_edit.text(), self._shots_edit.text(),
                self._structure_cb.isChecked())

    def _do_create(self, dry_run: bool) -> None:
        """Run a dry-run or a real create via the controller."""
        self._controller.create(
            self._root_edit.text(), self._name_edit.text(),
            self._assets_edit.text(), self._shots_edit.text(),
            default_structure=self._structure_cb.isChecked(),
            dry_run=dry_run, set_job=self._setjob_cb.isChecked())

    def _on_toggle_log(self, shown: bool) -> None:
        """Show/hide the log panel."""
        self._log.setVisible(shown)
        self._log_toggle.setText("Hide Log" if shown else "Show Log")

    # -- controller slots -----------------------------------------------

    def _on_validation(self, can_create: bool, message: str, level: str) -> None:
        """Enable/disable actions and surface a validation hint."""
        self._can_create = can_create
        self._create_btn.setEnabled(can_create)
        self._dryrun_btn.setEnabled(can_create)
        color = _VALID_COLORS.get(level, _VALID_COLORS[""])
        self._preview_count.setStyleSheet("color: " + color + ";")
        if message:
            self._preview_count.setText(message)

    def _render_preview(self, plan) -> None:
        """Render *plan*'s directories as a folder tree (plan is duck-typed)."""
        self._tree.clear()
        root_item = QtWidgets.QTreeWidgetItem([plan.project])
        root_item.setIcon(0, self._dir_icon())
        self._tree.addTopLevelItem(root_item)
        base = plan.project_root.rstrip("/")
        nodes = {base: root_item}
        for d in plan.directories:
            d = d.rstrip("/")
            if d == base:
                continue
            rel = d[len(base) + 1:] if d.startswith(base + "/") else d
            parent = root_item
            acc = base
            for part in rel.split("/"):
                acc = acc + "/" + part
                child = nodes.get(acc)
                if child is None:
                    child = QtWidgets.QTreeWidgetItem([part])
                    child.setIcon(0, self._dir_icon())
                    parent.addChild(child)
                    nodes[acc] = child
                parent = child
        root_item.setExpanded(True)
        for i in range(root_item.childCount()):
            root_item.child(i).setExpanded(True)
        self._preview_count.setStyleSheet("color: " + _VALID_COLORS[""] + ";")
        self._preview_count.setText(plan.summary())

    def _set_status(self, message: str, level: str = "info") -> None:
        """Update the status bar dot color and message."""
        color = _STATUS_COLORS.get(level, _STATUS_COLORS["info"])
        self._status_dot.setStyleSheet("color: " + color + "; font-size: 13px;")
        self._status_text.setText(message)

    def _append_log(self, line: str) -> None:
        """Append a line to the log and auto-reveal the panel."""
        self._log.appendPlainText(line)
        if not self._log.isVisible():
            self._log_toggle.setChecked(True)

    def _dir_icon(self) -> QtGui.QIcon:
        """A folder icon that works across PySide bindings."""
        style = self.style()
        sp = getattr(QtWidgets.QStyle, "SP_DirIcon", None)
        if sp is None:  # PySide6 enum nesting
            sp = QtWidgets.QStyle.StandardPixmap.SP_DirIcon
        return style.standardIcon(sp)


# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------

def launch(parent: Optional[object] = None) -> "ProjectManagerUI":
    """Create, parent, show and return the Project Manager window.

    Parents to Houdini's main window (so it floats above Houdini and is cleaned
    up with the session) and sets ``WA_DeleteOnClose`` to avoid leaking the
    widget.  The caller (``launch.py`` / package ``launch``) keeps a reference
    so Python's garbage collector doesn't reap the window immediately.

    Args:
        parent: Optional explicit Qt parent; defaults to Houdini's main window.

    Returns:
        The shown :class:`ProjectManagerUI`.
    """
    if parent is None:
        parent = _houdini_main_window()
    widget = ProjectManagerUI(parent)
    widget.setWindowFlags(QtCore.Qt.Window)
    widget.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
    widget.show()
    widget.raise_()
    return widget


def _houdini_main_window() -> Optional[object]:
    """Return Houdini's main Qt window, or ``None`` outside Houdini."""
    try:
        import hou  # noqa: PLC0415
        return hou.qt.mainWindow()
    except Exception:  # noqa: BLE001
        return None
