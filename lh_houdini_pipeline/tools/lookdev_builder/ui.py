"""
lh_houdini_pipeline.tools.lookdev_builder.ui
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
One-click Lookdev Builder window (PySide6/PySide2).

Pick a geometry file, tick what you want (lights / turntable), hit **Build
Lookdev**, and the tool assembles asset + 3-point rig + turntable camera in
``/stage`` with live stage-by-stage progress.

Node authoring runs on the main thread (Houdini requirement); progress is
pumped between stages so the window stays responsive.
"""

from __future__ import annotations

from typing import Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.ui import style as _style
from lh_houdini_pipeline.tools.lookdev_builder.core import LookdevConfig
from lh_houdini_pipeline.tools.lookdev_builder import service as _svc

_log = get_logger(__name__)

try:  # pragma: no cover
    from PySide6 import QtCore, QtWidgets  # type: ignore
except ImportError:  # pragma: no cover
    from PySide2 import QtCore, QtWidgets  # type: ignore


class LookdevBuilderUI(QtWidgets.QWidget):
    """Assemble Asset + Light Rig + Turntable in one click."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("lookdevRoot")
        self.setWindowTitle("Lookdev Builder")
        self.resize(640, 420)
        self.setStyleSheet(_style.STYLE)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)
        outer.addWidget(self._build_inputs())
        outer.addWidget(self._build_options())
        outer.addStretch(1)
        outer.addWidget(self._build_actions())
        self._status = QtWidgets.QLabel("Pick a geometry file, then Build Lookdev.")
        self._status.setObjectName("hintLabel")
        outer.addWidget(self._status)

    # -- construction ---------------------------------------------------
    def _build_inputs(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox("Asset")
        grid = QtWidgets.QGridLayout(box)

        grid.addWidget(QtWidgets.QLabel("Geometry:"), 0, 0)
        self._geo_edit = QtWidgets.QLineEdit()
        self._geo_edit.setPlaceholderText("FBX / OBJ / ABC / USD  (blank = default box)")
        geo_browse = QtWidgets.QPushButton("...")
        geo_browse.setMaximumWidth(32)
        geo_browse.clicked.connect(self._on_browse_geo)
        grid.addWidget(self._geo_edit, 0, 1)
        grid.addWidget(geo_browse, 0, 2)

        grid.addWidget(QtWidgets.QLabel("Asset name:"), 1, 0)
        self._name_edit = QtWidgets.QLineEdit()
        self._name_edit.setPlaceholderText("(auto from filename)")
        grid.addWidget(self._name_edit, 1, 1, 1, 2)

        grid.addWidget(QtWidgets.QLabel("Output dir:"), 2, 0)
        self._out_edit = QtWidgets.QLineEdit()
        self._out_edit.setPlaceholderText("(optional) write component .usd here")
        out_browse = QtWidgets.QPushButton("...")
        out_browse.setMaximumWidth(32)
        out_browse.clicked.connect(self._on_browse_out)
        grid.addWidget(self._out_edit, 2, 1)
        grid.addWidget(out_browse, 2, 2)
        return box

    def _build_options(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox("Lookdev")
        grid = QtWidgets.QGridLayout(box)

        self._lights_cb = QtWidgets.QCheckBox("3-point light rig")
        self._lights_cb.setChecked(True)
        self._turntable_cb = QtWidgets.QCheckBox("360 turntable camera")
        self._turntable_cb.setChecked(True)
        self._calib_cb = QtWidgets.QCheckBox("Calibration plates")
        self._calib_cb.setChecked(True)
        grid.addWidget(self._lights_cb, 0, 0)
        grid.addWidget(self._turntable_cb, 0, 1)
        grid.addWidget(self._calib_cb, 0, 2)

        grid.addWidget(QtWidgets.QLabel("Turntable frames:"), 1, 0)
        self._frames_spin = QtWidgets.QSpinBox()
        self._frames_spin.setRange(2, 2000)
        self._frames_spin.setValue(120)
        grid.addWidget(self._frames_spin, 1, 1)

        grid.addWidget(QtWidgets.QLabel("Dome HDRI:"), 2, 0)
        self._dome_edit = QtWidgets.QLineEdit()
        self._dome_edit.setPlaceholderText("(optional) .exr/.hdr for ambient dome")
        dome_browse = QtWidgets.QPushButton("...")
        dome_browse.setMaximumWidth(32)
        dome_browse.clicked.connect(self._on_browse_dome)
        grid.addWidget(self._dome_edit, 2, 1)
        grid.addWidget(dome_browse, 2, 2)
        return box

    def _build_actions(self) -> QtWidgets.QWidget:
        row = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        self._progress = QtWidgets.QProgressBar()
        self._progress.setVisible(False)
        self._build_btn = QtWidgets.QPushButton("Build Lookdev")
        self._build_btn.setObjectName("primaryBtn")
        self._build_btn.clicked.connect(self._on_build)
        h.addWidget(self._progress, 1)
        h.addWidget(self._build_btn)
        return row

    # -- browse ---------------------------------------------------------
    def _on_browse_geo(self) -> None:
        f, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Geometry file", "",
            "Geometry (*.fbx *.obj *.abc *.usd *.usda *.usdc *.bgeo *.bgeo.sc)",
        )
        if f:
            self._geo_edit.setText(f)

    def _on_browse_out(self) -> None:
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Output directory")
        if d:
            self._out_edit.setText(d)

    def _on_browse_dome(self) -> None:
        f, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "HDRI", "", "HDRI (*.exr *.hdr *.rat *.tex)")
        if f:
            self._dome_edit.setText(f)

    # -- build ----------------------------------------------------------
    def _config(self) -> LookdevConfig:
        return LookdevConfig(
            geo_path=self._geo_edit.text().strip() or None,
            asset_name=self._name_edit.text().strip() or None,
            with_lights=self._lights_cb.isChecked(),
            with_turntable=self._turntable_cb.isChecked(),
            with_calibration=self._calib_cb.isChecked(),
            dome_hdri=self._dome_edit.text().strip() or None,
            turntable_frames=self._frames_spin.value(),
            output_dir=self._out_edit.text().strip() or None,
        )

    def _on_build(self) -> None:
        cfg = self._config()
        total = cfg.step_count()
        self._progress.setVisible(True)
        self._progress.setRange(0, total)
        self._progress.setValue(0)
        self._build_btn.setEnabled(False)

        def _progress(step: int, tot: int, label: str) -> None:
            self._progress.setValue(step)
            self._set_status("Building " + label + "... (" + str(step) + "/" + str(tot) + ")",
                             "working")
            QtWidgets.QApplication.processEvents()

        result = _svc.build_lookdev(cfg, on_progress=_progress)
        self._progress.setVisible(False)
        self._build_btn.setEnabled(True)

        if result.ok:
            self._set_status(
                "Built '" + result.asset_name + "': " + str(len(result.light_nodes))
                + " lights" + (", turntable cam" if result.camera_node else "")
                + (", calib plates" if result.calibration_node else "") + ".",
                "done",
            )
        else:
            self._set_status("Completed with errors: " + "; ".join(result.errors), "error")

    # -- status ---------------------------------------------------------
    def _set_status(self, text: str, level: str = "info") -> None:
        color = _style.STATUS_COLORS.get(level, _style.TEXT_DIM)
        self._status.setText(text)
        self._status.setStyleSheet("color: " + color + ";")


def launch() -> "LookdevBuilderUI":
    """Create, show, and return the Lookdev Builder window."""
    parent = None
    try:
        import hou  # noqa: PLC0415
        parent = hou.qt.mainWindow()
    except Exception:  # noqa: BLE001
        parent = None
    win = LookdevBuilderUI(parent)
    win.setWindowFlag(QtCore.Qt.Window, True)
    win.show()
    return win
