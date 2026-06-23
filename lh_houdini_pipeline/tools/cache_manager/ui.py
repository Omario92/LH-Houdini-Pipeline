"""
lh_houdini_pipeline.tools.cache_manager.ui
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PySide6/PySide2 front end for the Scene Cache Manager.

UX principles (matching the rest of the pipeline tools):

* **Dry-run first** -- "Scan" only reads; "Delete Selected" is the single
  destructive action and always asks for confirmation showing bytes reclaimed.
* **Colour = health** -- rows tint by status (gap/stale/empty) so the eye
  finds problems instantly.
* **Threaded delete** -- filesystem deletion runs in a worker so a slow network
  drive never freezes the UI; progress is reported live.
* Double-click or right-click a row to reveal the cache folder in the OS.

All ``hou`` work (scene discovery) is funnelled through the service and only
runs when the user clicks Scan, so the module imports cleanly for tests.
"""

from __future__ import annotations

from typing import List, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.ui import style as _style
from lh_houdini_pipeline.file.cache_utils import CacheSequence
from lh_houdini_pipeline.tools.cache_manager import core as _core
from lh_houdini_pipeline.tools.cache_manager import service as _svc

_log = get_logger(__name__)

try:  # pragma: no cover
    from PySide6 import QtCore, QtGui, QtWidgets  # type: ignore
except ImportError:  # pragma: no cover
    from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore


# Column indices.
_COL_NAME, _COL_RANGE, _COL_FILES, _COL_SIZE, _COL_STATUS, _COL_DIR = range(6)

#: Status -> background tint (subtle, readable on the dark theme).
_STATUS_TINT = {
    _core.CacheStatus.OK: None,
    _core.CacheStatus.INCOMPLETE: "#5a4a1e",   # amber-ish: gaps
    _core.CacheStatus.STALE: "#4a3030",        # red-ish: stale
    _core.CacheStatus.EMPTY: "#3a3a3a",        # grey: empty
}


# ---------------------------------------------------------------------------
# Delete worker (filesystem-only -> safe off the main thread)
# ---------------------------------------------------------------------------

class _DeleteWorker(QtCore.QObject):
    """Runs ``service.delete_paths`` off-thread, emitting progress + result."""

    progress = QtCore.Signal(int, int)   # done, total
    finished = QtCore.Signal(object)     # DeleteResult

    def __init__(self, paths: List[str], use_trash: bool) -> None:
        super().__init__()
        self._paths = paths
        self._use_trash = use_trash

    @QtCore.Slot()
    def run(self) -> None:
        # Delete one-by-one so we can report progress; reuse service per-file
        # safety semantics by batching size 1.
        agg = _svc.DeleteResult(used_trash=self._use_trash)
        total = len(self._paths)
        for i, p in enumerate(self._paths, start=1):
            res = _svc.delete_paths([p], use_trash=self._use_trash)
            agg.deleted.extend(res.deleted)
            agg.failed.extend(res.failed)
            agg.used_trash = res.used_trash
            self.progress.emit(i, total)
        self.finished.emit(agg)


# ---------------------------------------------------------------------------
# Main widget
# ---------------------------------------------------------------------------

class CacheManagerUI(QtWidgets.QWidget):
    """Scan, inspect, and safely purge scene caches."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("cacheMgrRoot")
        self.setWindowTitle("Scene Cache Manager")
        self.resize(960, 600)
        self.setStyleSheet(_style.STYLE)

        self._rows: List[_core.CacheReportRow] = []
        self._thread: Optional[QtCore.QThread] = None
        self._worker: Optional[_DeleteWorker] = None

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)
        outer.addWidget(self._build_controls())
        outer.addWidget(self._build_table(), 1)
        outer.addWidget(self._build_actions())
        self._status = QtWidgets.QLabel("Ready. Click Scan Scene to discover caches.")
        self._status.setObjectName("hintLabel")
        outer.addWidget(self._status)

    # -- construction ---------------------------------------------------
    def _build_controls(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox("Scan & Policy")
        grid = QtWidgets.QGridLayout(box)

        scan_btn = QtWidgets.QPushButton("Scan Scene")
        scan_btn.setObjectName("primaryBtn")
        scan_btn.clicked.connect(self._on_scan_scene)
        folder_btn = QtWidgets.QPushButton("Scan Folder...")
        folder_btn.clicked.connect(self._on_scan_folder)

        grid.addWidget(scan_btn, 0, 0)
        grid.addWidget(folder_btn, 0, 1)

        grid.addWidget(QtWidgets.QLabel("Stale after (days):"), 0, 2)
        self._stale_spin = QtWidgets.QSpinBox()
        self._stale_spin.setRange(0, 3650)
        self._stale_spin.setValue(14)
        grid.addWidget(self._stale_spin, 0, 3)

        self._cb_stale = QtWidgets.QCheckBox("Flag stale")
        self._cb_stale.setChecked(True)
        self._cb_incomplete = QtWidgets.QCheckBox("Flag incomplete (gaps)")
        self._cb_empty = QtWidgets.QCheckBox("Flag empty")
        self._cb_empty.setChecked(True)
        grid.addWidget(self._cb_stale, 0, 4)
        grid.addWidget(self._cb_incomplete, 0, 5)
        grid.addWidget(self._cb_empty, 0, 6)
        grid.setColumnStretch(7, 1)
        return box

    def _build_table(self) -> QtWidgets.QWidget:
        self._table = QtWidgets.QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["Sequence", "Frame Range", "Files", "Size", "Status", "Directory"]
        )
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.cellDoubleClicked.connect(self._on_double_click)
        hdr = self._table.horizontalHeader()
        hdr.setStretchLastSection(True)
        hdr.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        return self._table

    def _build_actions(self) -> QtWidgets.QWidget:
        row = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)

        self._select_btn = QtWidgets.QPushButton("Select Candidates")
        self._select_btn.clicked.connect(self._select_candidates)
        self._trash_cb = QtWidgets.QCheckBox("Send to Trash (recoverable)")
        self._trash_cb.setChecked(True)

        self._progress = QtWidgets.QProgressBar()
        self._progress.setVisible(False)

        self._delete_btn = QtWidgets.QPushButton("Delete Selected")
        self._delete_btn.setObjectName("warnBtn")
        self._delete_btn.clicked.connect(self._on_delete)

        h.addWidget(self._select_btn)
        h.addWidget(self._trash_cb)
        h.addWidget(self._progress, 1)
        h.addWidget(self._delete_btn)
        return row

    # -- scanning -------------------------------------------------------
    def _current_policy(self) -> _core.CleanupPolicy:
        return _core.CleanupPolicy(
            stale_days=float(self._stale_spin.value()),
            delete_stale=self._cb_stale.isChecked(),
            delete_incomplete=self._cb_incomplete.isChecked(),
            delete_empty=self._cb_empty.isChecked(),
        )

    def _on_scan_scene(self) -> None:
        try:
            sequences = _svc.scan_scene()
        except Exception as exc:  # noqa: BLE001
            self._set_status("Scan failed: " + str(exc), "error")
            return
        self._populate(sequences)

    def _on_scan_folder(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose cache folder")
        if not folder:
            return
        sequences = _svc.scan_dirs([folder], recursive=True)
        self._populate(sequences)

    def _populate(self, sequences: List[CacheSequence]) -> None:
        plan = _core.plan_cleanup(sequences, self._current_policy())
        self._rows = list(plan.rows)
        self._table.setRowCount(len(self._rows))
        for r, row in enumerate(self._rows):
            self._set_row(r, row)
        total = sum(rr.size_bytes for rr in self._rows)
        from lh_houdini_pipeline.file.cache_utils import human_size
        self._set_status(
            str(len(self._rows)) + " sequence(s), " + human_size(total)
            + " total. " + str(len(plan.candidate_rows))
            + " candidate(s) -> " + plan.reclaimed_label + " reclaimable.",
            "done",
        )
        self._select_candidates()

    def _set_row(self, r: int, row: _core.CacheReportRow) -> None:
        vals = [row.name, row.range_label, str(row.file_count),
                row.size_label, row.status.value, row.directory]
        for c, text in enumerate(vals):
            item = QtWidgets.QTableWidgetItem(text)
            if c == _COL_NAME:
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
            tint = _STATUS_TINT.get(row.status)
            if tint:
                item.setBackground(QtGui.QColor(tint))
            self._table.setItem(r, c, item)

    # -- selection ------------------------------------------------------
    def _select_candidates(self) -> None:
        for r, row in enumerate(self._rows):
            item = self._table.item(r, _COL_NAME)
            if item is not None:
                item.setCheckState(
                    QtCore.Qt.Checked if row.is_candidate else QtCore.Qt.Unchecked
                )

    def _checked_rows(self) -> List[_core.CacheReportRow]:
        out = []
        for r, row in enumerate(self._rows):
            item = self._table.item(r, _COL_NAME)
            if item is not None and item.checkState() == QtCore.Qt.Checked:
                out.append(row)
        return out

    # -- deletion -------------------------------------------------------
    def _on_delete(self) -> None:
        rows = self._checked_rows()
        if not rows:
            self._set_status("Nothing selected.", "info")
            return
        paths = _core.paths_for_sequences([r.sequence for r in rows])
        reclaim = sum(r.size_bytes for r in rows)
        from lh_houdini_pipeline.file.cache_utils import human_size
        verb = "Send to Trash" if self._trash_cb.isChecked() else "PERMANENTLY DELETE"
        msg = (verb + " " + str(len(paths)) + " file(s) across "
               + str(len(rows)) + " sequence(s), freeing "
               + human_size(reclaim) + "?")
        confirm = QtWidgets.QMessageBox.question(
            self, "Confirm cache cleanup", msg,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if confirm != QtWidgets.QMessageBox.Yes:
            return
        self._start_delete(paths)

    def _start_delete(self, paths: List[str]) -> None:
        self._progress.setVisible(True)
        self._progress.setRange(0, len(paths))
        self._progress.setValue(0)
        self._delete_btn.setEnabled(False)

        self._thread = QtCore.QThread(self)
        self._worker = _DeleteWorker(paths, self._trash_cb.isChecked())
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_delete_progress)
        self._worker.finished.connect(self._on_delete_done)
        self._thread.start()

    @QtCore.Slot(int, int)
    def _on_delete_progress(self, done: int, total: int) -> None:
        self._progress.setValue(done)

    @QtCore.Slot(object)
    def _on_delete_done(self, result: "_svc.DeleteResult") -> None:
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
        self._progress.setVisible(False)
        self._delete_btn.setEnabled(True)
        mode = "trashed" if result.used_trash else "deleted"
        status = ("Deletion complete: " + str(result.freed_count) + " "
                  + mode + ", " + str(len(result.failed)) + " failed.")
        self._set_status(status, "error" if result.failed else "done")
        # Re-scan the same selection sources cheaply by clearing removed rows.
        self._refresh_after_delete()

    def _refresh_after_delete(self) -> None:
        # Simplest correct refresh: re-scan currently shown directories.
        dirs = sorted({row.directory for row in self._rows})
        sequences = _svc.scan_dirs(dirs, recursive=False)
        self._populate(sequences)

    # -- folder reveal --------------------------------------------------
    def _on_double_click(self, r: int, _c: int) -> None:
        if 0 <= r < len(self._rows):
            _svc.open_in_explorer(self._rows[r].directory)

    def _on_context_menu(self, pos: "QtCore.QPoint") -> None:
        r = self._table.rowAt(pos.y())
        menu = QtWidgets.QMenu(self)
        act_open = menu.addAction("Open Folder")
        act_sel = menu.addAction("Select Candidates")
        chosen = menu.exec_(self._table.viewport().mapToGlobal(pos))
        if chosen == act_open and 0 <= r < len(self._rows):
            _svc.open_in_explorer(self._rows[r].directory)
        elif chosen == act_sel:
            self._select_candidates()

    # -- status ---------------------------------------------------------
    def _set_status(self, text: str, level: str = "info") -> None:
        color = _style.STATUS_COLORS.get(level, _style.TEXT_DIM)
        self._status.setText(text)
        self._status.setStyleSheet("color: " + color + ";")


# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------

def launch() -> "CacheManagerUI":
    """Create, show, and return the Cache Manager window.

    Parents to Houdini's main window when running inside Houdini so the tool
    docks/stacks correctly; standalone otherwise.
    """
    parent = None
    try:
        import hou  # noqa: PLC0415
        parent = hou.qt.mainWindow()
    except Exception:  # noqa: BLE001 -- outside Houdini
        parent = None
    win = CacheManagerUI(parent)
    win.setWindowFlag(QtCore.Qt.Window, True)
    win.show()
    return win
