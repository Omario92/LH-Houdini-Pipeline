"""
lh_houdini_pipeline.tools.asset_ingest.ui
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Compact batch-ingestion window (PySide6/PySide2).

Drop geometry files/folders onto the window (or use Add Files / Add Folder) and
the tool resolves each into an editable row: derived asset name, source file,
and detected texture folder.  Click **Ingest** to build one USD component per
row under ``/stage``, with live progress and per-row status.

The window itself is a drop target -- the same ingestion that powers the OS
drag-drop handler, exposed as an explicit, reviewable UI for batch jobs.
"""

from __future__ import annotations

from typing import List, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.ui import style as _style
from lh_houdini_pipeline.tools.asset_ingest import core as _core
from lh_houdini_pipeline.tools.asset_ingest import service as _svc

_log = get_logger(__name__)

try:  # pragma: no cover
    from PySide6 import QtCore, QtGui, QtWidgets  # type: ignore
except ImportError:  # pragma: no cover
    from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore

_COL_NAME, _COL_GEO, _COL_TEX, _COL_STATUS = range(4)


class AssetIngestUI(QtWidgets.QWidget):
    """Drag-and-drop batch ingestion of geometry files into USD components."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("assetIngestRoot")
        self.setWindowTitle("Asset Ingestion")
        self.resize(820, 520)
        self.setStyleSheet(_style.STYLE)
        self.setAcceptDrops(True)  # window-level OS drop target

        self._items: List[_core.IngestItem] = []

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)
        outer.addWidget(self._build_toolbar())
        outer.addWidget(self._build_table(), 1)
        outer.addWidget(self._build_actions())

        self._status = QtWidgets.QLabel("Drop FBX/OBJ/ABC/USD here, or use Add Files.")
        self._status.setObjectName("hintLabel")
        outer.addWidget(self._status)

    # -- construction ---------------------------------------------------
    def _build_toolbar(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(bar)
        h.setContentsMargins(0, 0, 0, 0)
        add_files = QtWidgets.QPushButton("Add Files...")
        add_files.clicked.connect(self._on_add_files)
        add_folder = QtWidgets.QPushButton("Add Folder...")
        add_folder.clicked.connect(self._on_add_folder)
        clear = QtWidgets.QPushButton("Clear")
        clear.clicked.connect(self._clear)
        h.addWidget(add_files)
        h.addWidget(add_folder)
        h.addWidget(clear)
        h.addStretch(1)
        h.addWidget(QtWidgets.QLabel("Output dir:"))
        self._out_edit = QtWidgets.QLineEdit()
        self._out_edit.setPlaceholderText("(optional) write each .usd here")
        browse = QtWidgets.QPushButton("...")
        browse.setMaximumWidth(32)
        browse.clicked.connect(self._on_browse_out)
        h.addWidget(self._out_edit, 1)
        h.addWidget(browse)
        return bar

    def _build_table(self) -> QtWidgets.QWidget:
        self._table = QtWidgets.QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Asset Name", "Geometry", "Textures", "Status"])
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        hdr = self._table.horizontalHeader()
        hdr.setStretchLastSection(True)
        hdr.setSectionResizeMode(_COL_NAME, QtWidgets.QHeaderView.ResizeToContents)
        # only the Asset Name column is editable
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked
                                    | QtWidgets.QAbstractItemView.SelectedClicked)
        return self._table

    def _build_actions(self) -> QtWidgets.QWidget:
        row = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        self._recursive_cb = QtWidgets.QCheckBox("Recurse texture subfolders")
        self._progress = QtWidgets.QProgressBar()
        self._progress.setVisible(False)
        self._ingest_btn = QtWidgets.QPushButton("Ingest")
        self._ingest_btn.setObjectName("primaryBtn")
        self._ingest_btn.clicked.connect(self._on_ingest)
        h.addWidget(self._recursive_cb)
        h.addWidget(self._progress, 1)
        h.addWidget(self._ingest_btn)
        return row

    # -- drag & drop (window-level) -------------------------------------
    def dragEnterEvent(self, event: "QtGui.QDragEnterEvent") -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: "QtGui.QDropEvent") -> None:  # noqa: N802
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile()]
        if paths:
            self._add_paths(paths)
            event.acceptProposedAction()

    # -- input ----------------------------------------------------------
    def _on_add_files(self) -> None:
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Add geometry files", "",
            "Geometry (*.fbx *.obj *.abc *.usd *.usda *.usdc *.bgeo *.bgeo.sc *.ply *.stl)",
        )
        if files:
            self._add_paths(files)

    def _on_add_folder(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Add a folder of assets")
        if folder:
            self._add_paths([folder])

    def _on_browse_out(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Output directory")
        if folder:
            self._out_edit.setText(folder)

    def _add_paths(self, paths: List[str]) -> None:
        new_items = _core.plan_ingest(paths)
        if not new_items:
            self._set_status("No geometry files found in the dropped items.", "info")
            return
        existing = {it.geo_path for it in self._items}
        for it in new_items:
            if it.geo_path not in existing:
                self._items.append(it)
        self._rebuild_table()
        self._set_status(str(len(self._items)) + " asset(s) queued.", "done")

    def _clear(self) -> None:
        self._items = []
        self._table.setRowCount(0)
        self._set_status("Cleared.", "info")

    # -- table ----------------------------------------------------------
    def _rebuild_table(self) -> None:
        self._table.setRowCount(len(self._items))
        for r, it in enumerate(self._items):
            name = QtWidgets.QTableWidgetItem(it.asset_name)
            name.setFlags(name.flags() | QtCore.Qt.ItemIsEditable)
            geo = QtWidgets.QTableWidgetItem(it.geo_path)
            geo.setFlags(geo.flags() & ~QtCore.Qt.ItemIsEditable)
            tex = QtWidgets.QTableWidgetItem(it.tex_folder or "(none)")
            tex.setFlags(tex.flags() & ~QtCore.Qt.ItemIsEditable)
            status = QtWidgets.QTableWidgetItem("queued")
            status.setFlags(status.flags() & ~QtCore.Qt.ItemIsEditable)
            self._table.setItem(r, _COL_NAME, name)
            self._table.setItem(r, _COL_GEO, geo)
            self._table.setItem(r, _COL_TEX, tex)
            self._table.setItem(r, _COL_STATUS, status)

    def _items_from_table(self) -> List[_core.IngestItem]:
        """Re-read the (possibly edited) asset names back into IngestItems."""
        out: List[_core.IngestItem] = []
        for r, it in enumerate(self._items):
            cell = self._table.item(r, _COL_NAME)
            name = cell.text().strip() if cell else it.asset_name
            name = _core.derive_asset_name(name + ".obj")  # sanitise the edit
            out.append(_core.IngestItem(geo_path=it.geo_path, asset_name=name,
                                        tex_folder=it.tex_folder))
        return out

    # -- ingest ---------------------------------------------------------
    def _on_ingest(self) -> None:
        items = self._items_from_table()
        if not items:
            self._set_status("Nothing to ingest.", "info")
            return
        out_dir = self._out_edit.text().strip() or None
        self._progress.setVisible(True)
        self._progress.setRange(0, len(items))
        self._progress.setValue(0)
        self._ingest_btn.setEnabled(False)

        def _progress(i: int, total: int, name: str) -> None:
            self._progress.setValue(i)
            row = i - 1
            if 0 <= row < self._table.rowCount():
                self._table.item(row, _COL_STATUS).setText("building...")
            QtWidgets.QApplication.processEvents()  # keep UI responsive (main thread)

        # Node ops must run on the main thread (matches the other tools), so we
        # call the service directly and pump events for progress feedback.
        summary = _svc.ingest_items(
            items, parent_path="/stage", output_dir=out_dir,
            recursive=self._recursive_cb.isChecked(), on_progress=_progress,
        )
        self._apply_results(summary)
        self._progress.setVisible(False)
        self._ingest_btn.setEnabled(True)

    def _apply_results(self, summary: "_svc.IngestSummary") -> None:
        by_name = {r.asset_name: r for r in summary.results}
        for r in range(self._table.rowCount()):
            cell = self._table.item(r, _COL_NAME)
            res = by_name.get(cell.text().strip()) if cell else None
            st = self._table.item(r, _COL_STATUS)
            if res is None:
                continue
            if res.ok:
                st.setText("OK")
                st.setBackground(QtGui.QColor("#1e3a1e"))
            else:
                st.setText("FAILED")
                st.setBackground(QtGui.QColor("#3a1e1e"))
                st.setToolTip(res.error or "")
        ok, bad = len(summary.succeeded), len(summary.failed)
        self._set_status("Ingest complete: " + str(ok) + " ok, " + str(bad) + " failed.",
                         "error" if bad else "done")

    # -- status ---------------------------------------------------------
    def _set_status(self, text: str, level: str = "info") -> None:
        color = _style.STATUS_COLORS.get(level, _style.TEXT_DIM)
        self._status.setText(text)
        self._status.setStyleSheet("color: " + color + ";")


def launch() -> "AssetIngestUI":
    """Create, show, and return the Asset Ingestion window."""
    parent = None
    try:
        import hou  # noqa: PLC0415
        parent = hou.qt.mainWindow()
    except Exception:  # noqa: BLE001
        parent = None
    win = AssetIngestUI(parent)
    win.setWindowFlag(QtCore.Qt.Window, True)
    win.show()
    return win
