"""
lh_houdini_pipeline.tools.tex_to_mtlx.ui
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PySide UI for TexToMtlx -- a thin view over ``core`` (scan/plan) and
``service`` (hou build).

The widget holds **no business logic**: every button handler delegates to the
pure ``core`` functions or the hou-side ``service`` functions and only updates
the status label / list.  Qt is imported with a PySide2 -> PySide6 fallback so
the module loads on either Houdini Qt binding.

Import is guarded: outside Houdini (no PySide installed) importing this module
will raise ``ImportError`` -- callers should catch that (the test suite does).
"""

from __future__ import annotations

from typing import List, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.tex_to_mtlx import core as _core
from lh_houdini_pipeline.tools.tex_to_mtlx import service as _service
from lh_houdini_pipeline.ui import style as _style

_log = get_logger(__name__)

# -- Qt binding (PySide2 first, then PySide6) -------------------------------
try:  # pragma: no cover - binding choice is environment-specific
    from PySide2 import QtCore, QtWidgets  # type: ignore
    _QT = "PySide2"
except ImportError:  # pragma: no cover
    from PySide6 import QtCore, QtWidgets  # type: ignore
    _QT = "PySide6"


class _TxWorker(QtCore.QObject):
    """Runs the imaketx batch off the UI thread, reporting progress via signals.

    Lives in the main thread but its :meth:`run` executes inside a worker
    thread; the Qt signals are delivered back to main-thread slots (queued),
    so widget updates stay on the UI thread.
    """

    progress = QtCore.Signal(int, int, str)   # done, total, source name
    finished = QtCore.Signal(int, int)         # ok_count, total
    failed = QtCore.Signal(str)

    def __init__(self, infos, out_dir, dry_run):
        super().__init__()
        self._infos = list(infos)
        self._out_dir = out_dir
        self._dry_run = dry_run

    def run(self) -> None:
        """Convert all textures, emitting progress after each file."""
        try:
            def _cb(done, total, res):
                self.progress.emit(done, total, res.spec.source.name)
            results = _service.convert_textures_to_tx(
                self._infos, out_dir=self._out_dir,
                dry_run=self._dry_run, on_each=_cb,
            )
            ok = sum(1 for r in results if r.success)
            self.finished.emit(ok, len(results))
        except Exception as exc:  # noqa: BLE001
            _log.exception("tx worker failed")
            self.failed.emit(str(exc))


class TexToMtlxWidget(QtWidgets.QWidget):
    """Folder -> scan -> build MaterialX networks, in four clicks.

    The widget is intentionally minimal (MVP scope):
        * a folder picker,
        * a Scan button,
        * a checkable list of discovered materials,
        * Build Selected / Build All,
        * a dry-run toggle and a status label.
    """

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("TexToMtlx  (MVP)")
        self._scan: Optional[_core.ScanResult] = None
        self._buttons = []
        self._tx_worker = None
        self._tx_thread = None
        self._build_ui()

    # -- construction ---------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble all child widgets and connect signals."""
        layout = QtWidgets.QVBoxLayout(self)

        # Folder row
        folder_row = QtWidgets.QHBoxLayout()
        self._folder_edit = QtWidgets.QLineEdit()
        self._folder_edit.setPlaceholderText("Texture folder...")
        browse = QtWidgets.QPushButton("Browse...")
        browse.clicked.connect(self._on_browse)
        self._buttons.append(browse)
        folder_row.addWidget(QtWidgets.QLabel("Folder:"))
        folder_row.addWidget(self._folder_edit, 1)
        folder_row.addWidget(browse)
        layout.addLayout(folder_row)

        # Options row
        opts_row = QtWidgets.QHBoxLayout()
        self._recursive_cb = QtWidgets.QCheckBox("Recursive")
        self._dryrun_cb = QtWidgets.QCheckBox("Dry-run (no nodes)")
        self._force_cb = QtWidgets.QCheckBox("Replace existing")
        scan_btn = QtWidgets.QPushButton("Scan")
        scan_btn.clicked.connect(self._on_scan)
        self._buttons.append(scan_btn)
        opts_row.addWidget(self._recursive_cb)
        opts_row.addWidget(self._dryrun_cb)
        opts_row.addWidget(self._force_cb)
        opts_row.addStretch(1)
        opts_row.addWidget(scan_btn)
        layout.addLayout(opts_row)

        # Material list
        self._list = QtWidgets.QListWidget()
        self._list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        layout.addWidget(self._list, 1)

        # Build row
        build_row = QtWidgets.QHBoxLayout()
        build_sel = QtWidgets.QPushButton("Build Selected")
        build_sel.clicked.connect(self._on_build_selected)
        self._buttons.append(build_sel)
        build_all = QtWidgets.QPushButton("Build All")
        build_all.setObjectName("primaryBtn")
        build_all.clicked.connect(self._on_build_all)
        self._buttons.append(build_all)
        # .tx conversion via SideFX imaketx (brick: materialx.tx).
        tx_btn = QtWidgets.QPushButton("Convert .tx")
        tx_btn.setToolTip("Convert scanned source textures to .rat via imaketx.")
        tx_btn.clicked.connect(self._on_convert_tx)
        self._buttons.append(tx_btn)
        build_row.addWidget(build_sel)
        build_row.addWidget(build_all)
        build_row.addStretch(1)
        build_row.addWidget(tx_btn)
        layout.addLayout(build_row)

        # Progress (hidden until a conversion runs)
        self._progress = QtWidgets.QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Status
        self._status = QtWidgets.QLabel("Ready.")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        _style.apply(self)
        self.resize(460, 420)

    # -- handlers (delegate to core/service, never embed logic) ----------

    def _on_browse(self) -> None:
        """Open a directory chooser and fill the folder field."""
        start = self._folder_edit.text() or ""
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose texture folder", start
        )
        if path:
            self._folder_edit.setText(path)

    def _on_scan(self) -> None:
        """Scan the chosen folder and populate the material list."""
        folder = self._folder_edit.text().strip()
        if not folder:
            self._set_status("Choose a folder first.", error=True)
            return
        try:
            self._scan = _core.scan_and_plan(
                folder, recursive=self._recursive_cb.isChecked()
            )
        except NotADirectoryError as exc:
            self._set_status(str(exc), error=True)
            return
        except Exception as exc:  # noqa: BLE001
            self._set_status("Scan failed: " + str(exc), error=True)
            _log.exception("Scan failed")
            return

        self._list.clear()
        for plan in self._scan.plans:
            chans = ", ".join(c.value for c in plan.channels)
            item = QtWidgets.QListWidgetItem(plan.name + "   [" + chans + "]")
            item.setData(QtCore.Qt.UserRole, plan.name)
            self._list.addItem(item)
        self._set_status(self._scan.summary())

    def _on_build_selected(self) -> None:
        """Build only the materials selected in the list."""
        names = [
            item.data(QtCore.Qt.UserRole)
            for item in self._list.selectedItems()
        ]
        if not names:
            self._set_status("Select one or more materials, or use Build All.", error=True)
            return
        self._build(names)

    def _on_build_all(self) -> None:
        """Build every discovered material."""
        self._build(None)

    def _on_convert_tx(self) -> None:
        """Convert scanned textures to .tx/.rat via imaketx on a worker thread."""
        if self._scan is None or not self._scan.infos:
            self._set_status("Scan a folder first.", error=True)
            return
        if self._tx_thread is not None and self._tx_thread.is_alive():
            self._set_status("A conversion is already running.", error=True)
            return

        infos = self._scan.infos
        self._progress.setMaximum(len(infos))
        self._progress.setValue(0)
        self._progress.setVisible(True)
        self._set_buttons_enabled(False)

        worker = _TxWorker(infos, None, self._dryrun_cb.isChecked())
        worker.progress.connect(self._on_tx_progress, QtCore.Qt.QueuedConnection)
        worker.finished.connect(self._on_tx_finished, QtCore.Qt.QueuedConnection)
        worker.failed.connect(self._on_tx_failed, QtCore.Qt.QueuedConnection)

        import threading
        self._tx_worker = worker  # keep refs so they survive the handler scope
        self._tx_thread = threading.Thread(target=worker.run, daemon=True)
        verb = "Planning" if self._dryrun_cb.isChecked() else "Converting"
        self._set_status(verb + " " + str(len(infos)) + " texture(s)...")
        self._tx_thread.start()

    def _on_tx_progress(self, done: int, total: int, name: str) -> None:
        """Slot: update the progress bar after each converted texture."""
        self._progress.setValue(done)
        self._set_status("imaketx " + str(done) + "/" + str(total) + ": " + name)

    def _on_tx_finished(self, ok: int, total: int) -> None:
        """Slot: re-enable the UI when the batch completes."""
        self._progress.setVisible(False)
        self._set_buttons_enabled(True)
        verb = "Planned" if self._dryrun_cb.isChecked() else "Converted"
        self._set_status(verb + " " + str(ok) + "/" + str(total) + " texture(s) to .tx.")

    def _on_tx_failed(self, message: str) -> None:
        """Slot: report a batch failure and restore the UI."""
        self._progress.setVisible(False)
        self._set_buttons_enabled(True)
        self._set_status("imaketx failed: " + message, error=True)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        """Enable/disable all action buttons (used while a job runs)."""
        for btn in self._buttons:
            btn.setEnabled(enabled)

    # -- shared build path ----------------------------------------------

    def _build(self, names: Optional[List[str]]) -> None:
        """Resolve plans and either dry-run or build them via ``service``."""
        if self._scan is None:
            self._set_status("Scan a folder first.", error=True)
            return
        plans = _core.select_plans(self._scan, names)
        if not plans:
            self._set_status("Nothing to build.", error=True)
            return

        if self._dryrun_cb.isChecked():
            report = _core.format_dry_run(self._scan)
            _log.info("\n" + report)
            self._set_status(
                "Dry-run: " + str(len(plans)) + " material(s) planned (see log)."
            )
            return

        try:
            results = _service.build_plans(plans, force=self._force_cb.isChecked())
        except Exception as exc:  # noqa: BLE001
            self._set_status("Build failed: " + str(exc), error=True)
            _log.exception("Build failed")
            return

        built = sum(1 for r in results if r.created)
        where = results[0].node_path if results else "?"
        self._set_status("Built " + str(built) + " material(s) under " + where + ".")

    def _set_status(self, message: str, error: bool = False) -> None:
        """Update the status label (red on error)."""
        self._status.setStyleSheet("color: #cc5555;" if error else "")
        self._status.setText(message)


def launch(parent: Optional[object] = None) -> "TexToMtlxWidget":
    """Create, show, and return a :class:`TexToMtlxWidget`.

    Parents the window to Houdini's main window when running inside Houdini so
    it floats correctly; falls back to a parentless window otherwise.

    Args:
        parent: Optional explicit Qt parent.

    Returns:
        The shown :class:`TexToMtlxWidget` (kept referenced by the caller).
    """
    if parent is None:
        parent = _houdini_main_window()
    widget = TexToMtlxWidget(parent)
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
