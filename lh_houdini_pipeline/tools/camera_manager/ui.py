"""
lh_houdini_pipeline.tools.camera_manager.ui
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PySide UI for the Camera Manager -- a thin view over ``core`` (pure
CameraSpec) and ``service`` (hou create / list).  No business logic here:
handlers build a spec and call the service, then refresh the list / status.
Camera creation is fast and touches ``hou`` nodes, so it runs synchronously
on the main thread.
"""

from __future__ import annotations

from typing import Optional, Tuple

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.camera_manager import core as _core
from lh_houdini_pipeline.tools.camera_manager import service as _service
from lh_houdini_pipeline.ui import style as _style

_log = get_logger(__name__)

try:  # pragma: no cover
    from PySide2 import QtCore, QtWidgets  # type: ignore
    _QT = "PySide2"
except ImportError:  # pragma: no cover
    from PySide6 import QtCore, QtWidgets  # type: ignore
    _QT = "PySide6"


class CameraManagerWidget(QtWidgets.QWidget):
    """Create OBJ/Stage cameras from presets and list existing ones."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Camera Manager  (MVP)")
        self._build_ui()
        self._refresh()

    # -- construction ---------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble the form, create button, camera list and status."""
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self._name_edit = QtWidgets.QLineEdit("cam1")
        form.addRow("Name:", self._name_edit)

        self._context_cb = QtWidgets.QComboBox()
        for ctx in _core.CameraContext:
            self._context_cb.addItem(ctx.value, ctx)
        self._context_cb.currentIndexChanged.connect(self._refresh)
        form.addRow("Context:", self._context_cb)

        self._preset_cb = QtWidgets.QComboBox()
        for preset in _core.ResolutionPreset:
            label = preset.name + "  (" + str(preset.width) + "x" + str(preset.height) + ")"
            self._preset_cb.addItem(label, preset)
        self._preset_cb.setCurrentText(
            "HD1080  (1920x1080)"
        )
        form.addRow("Resolution:", self._preset_cb)

        self._focal_spin = QtWidgets.QDoubleSpinBox()
        self._focal_spin.setRange(1.0, 5000.0)
        self._focal_spin.setValue(50.0)
        self._focal_spin.setSuffix(" mm")
        form.addRow("Focal length:", self._focal_spin)

        self._fstop_spin = QtWidgets.QDoubleSpinBox()
        self._fstop_spin.setRange(0.5, 64.0)
        self._fstop_spin.setValue(5.6)
        form.addRow("f-stop:", self._fstop_spin)

        layout.addLayout(form)

        create_btn = QtWidgets.QPushButton("Create Camera")
        create_btn.setObjectName("primaryBtn")
        create_btn.clicked.connect(self._on_create)
        layout.addWidget(create_btn)

        layout.addWidget(QtWidgets.QLabel("Existing cameras:"))
        self._list = QtWidgets.QListWidget()
        self._list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        layout.addWidget(self._list, 1)

        ops_row = QtWidgets.QHBoxLayout()
        self._delete_btn = QtWidgets.QPushButton("Delete Selected")
        self._delete_btn.clicked.connect(self._on_delete)
        self._sync_btn = QtWidgets.QPushButton("Sync Playbar")
        self._sync_btn.clicked.connect(self._on_sync)
        self._merge_btn = QtWidgets.QPushButton("Merge All (OBJ)")
        self._merge_btn.clicked.connect(self._on_merge)
        self._turntable_btn = QtWidgets.QPushButton("Turntable (USD)")
        self._turntable_btn.setToolTip("Create a 360 turntable camera in /stage.")
        self._turntable_btn.clicked.connect(self._on_turntable)
        self._export_btn = QtWidgets.QPushButton("Export Selected...")
        self._export_btn.setToolTip("Export the selected camera to USD, Alembic, or Nuke format.")
        self._export_btn.clicked.connect(self._on_export)
        self._variants_btn = QtWidgets.QPushButton("Add Variants...")
        self._variants_btn.setToolTip("Add focal length or angle VariantSets to a selected LOP camera.")
        self._variants_btn.clicked.connect(self._on_variants)
        ops_row.addWidget(self._delete_btn)
        ops_row.addWidget(self._sync_btn)
        ops_row.addWidget(self._merge_btn)
        ops_row.addWidget(self._turntable_btn)
        ops_row.addWidget(self._export_btn)
        ops_row.addWidget(self._variants_btn)
        layout.addLayout(ops_row)

        self._status = QtWidgets.QLabel("Ready.")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        _style.apply(self)
        self.resize(440, 420)

    # -- handlers -------------------------------------------------------

    def _current_context(self):
        return self._context_cb.currentData()

    def _on_create(self) -> None:
        """Build a CameraSpec from the form and create the camera."""
        name = self._name_edit.text().strip() or "cam1"
        preset = self._preset_cb.currentData()
        spec = _core.spec_from_preset(
            name, preset,
            focal_length=self._focal_spin.value(),
            fstop=self._fstop_spin.value(),
        )
        try:
            path = _service.create_camera(spec, self._current_context(), force=False)
        except Exception as exc:  # noqa: BLE001
            self._set_status("Create failed: " + str(exc), error=True)
            _log.exception("Camera create failed")
            return
        if path:
            self._set_status("Created camera: " + path)
            self._refresh()
        else:
            self._set_status("Camera creation failed (see log).", error=True)

    def _refresh(self) -> None:
        """Reload the list of cameras for the current context."""
        self._list.clear()
        try:
            cams = _service.list_cameras(self._current_context())
        except Exception as exc:  # noqa: BLE001
            self._set_status("List failed: " + str(exc), error=True)
            return
        for info in cams:
            res = ("  " + str(info.resolution[0]) + "x" + str(info.resolution[1])
                   if info.resolution else "")
            item = QtWidgets.QListWidgetItem(
                info.path + "   f=" + str(round(info.focal_length, 1)) + "mm" + res
            )
            item.setData(QtCore.Qt.UserRole, info.path)
            self._list.addItem(item)
        self._set_status(str(len(cams)) + " camera(s) in "
                         + self._current_context().value)

    def _selected_paths(self):
        """Return camera paths for the selected list rows."""
        return [it.data(QtCore.Qt.UserRole) for it in self._list.selectedItems()]

    def _on_delete(self) -> None:
        """Delete the selected cameras."""
        paths = self._selected_paths()
        if not paths:
            self._set_status("Select camera(s) to delete.", error=True)
            return
        deleted = sum(1 for p in paths if _service.delete_camera(p))
        self._refresh()
        self._set_status("Deleted " + str(deleted) + "/" + str(len(paths)) + " camera(s).")

    def _on_sync(self) -> None:
        """Sync the playbar to the first selected camera's animation range."""
        paths = self._selected_paths()
        if not paths:
            self._set_status("Select a camera to sync playbar from.", error=True)
            return
        try:
            start, end = _service.sync_playback_range(paths[0])
        except Exception as exc:  # noqa: BLE001
            self._set_status("Sync failed: " + str(exc), error=True)
            return
        self._set_status("Playbar -> " + str(start) + "-" + str(end) + " (" + paths[0] + ")")

    def _on_merge(self) -> None:
        """Merge all OBJ cameras sequentially into one camera."""
        if self._current_context() is not _core.CameraContext.OBJ:
            self._set_status("Merge works on OBJ cameras only.", error=True)
            return
        cams = [i.path for i in _service.list_cameras(_core.CameraContext.OBJ)]
        if len(cams) < 2:
            self._set_status("Need at least 2 OBJ cameras to merge.", error=True)
            return
        try:
            path = _service.merge_cameras(cams)
        except Exception as exc:  # noqa: BLE001
            self._set_status("Merge failed: " + str(exc), error=True)
            _log.exception("merge failed")
            return
        if path:
            self._refresh()
            self._set_status("Merged " + str(len(cams)) + " cameras -> " + path)
        else:
            self._set_status("Merge failed (see log).", error=True)

    def _on_turntable(self) -> None:
        """Create a USD turntable camera in /stage from the form's focal/fstop."""
        spec = _core.TurntableSpec(focal_length=self._focal_spin.value())
        target = None
        # if a /stage camera/prim source is selected in this list, frame to it
        sel = self._selected_paths()
        if sel and sel[0].startswith("/stage"):
            target = sel[0]
        try:
            path = _service.create_turntable(spec, target_path=target)
        except Exception as exc:  # noqa: BLE001
            self._set_status("Turntable failed: " + str(exc), error=True)
            _log.exception("turntable failed")
            return
        if path:
            # switch context to STAGE so the new camera shows in the list
            idx = self._context_cb.findData(_core.CameraContext.STAGE)
            if idx >= 0:
                self._context_cb.setCurrentIndex(idx)
            self._refresh()
            self._set_status("Created turntable: " + path)
        else:
            self._set_status("Turntable creation failed (see log).", error=True)

    def _on_export(self) -> None:
        """Open the export dialog and export the selected camera."""
        paths = self._selected_paths()
        if not paths:
            self._set_status("Select a camera to export.", error=True)
            return
        
        camera_path = paths[0]
        
        # Determine default start/end frame from playback range
        try:
            import hou  # noqa: PLC0415
            start = int(hou.playbar.frameRange()[0])
            end = int(hou.playbar.frameRange()[1])
            rng = _service.camera_frame_range(camera_path)
            if rng:
                start, end = rng
        except Exception:  # noqa: BLE001
            start, end = 1001, 1050

        dialog = CameraExportDialog(camera_path, (start, end), self)
        exec_func = getattr(dialog, "exec", None) or getattr(dialog, "exec_")
        if exec_func() == QtWidgets.QDialog.Accepted:
            cfg = dialog.get_config()
            if not cfg["formats"]:
                self._set_status("No formats selected for export.", error=True)
                return
            
            try:
                results = _service.export_camera(
                    camera_path=camera_path,
                    output_dir=cfg["output_dir"],
                    file_name_base=cfg["file_name_base"],
                    formats=cfg["formats"],
                    start_frame=cfg["start_frame"],
                    end_frame=cfg["end_frame"],
                )
                if results:
                    self._set_status("Exported: " + ", ".join(results.keys()))
                else:
                    self._set_status("Export failed (see log).", error=True)
            except Exception as exc:  # noqa: BLE001
                self._set_status("Export failed: " + str(exc), error=True)
                _log.exception("Camera export failed")

    def _on_variants(self) -> None:
        """Create camera VariantSets on the selected LOP camera."""
        paths = self._selected_paths()
        if not paths:
            self._set_status("Select a stage camera to add variants to.", error=True)
            return
        
        camera_path = paths[0]
        if not camera_path.startswith("/stage"):
            self._set_status("Variants require a STAGE (USD) camera node.", error=True)
            return
            
        dialog = CameraVariantsDialog(camera_path, self)
        exec_func = getattr(dialog, "exec", None) or getattr(dialog, "exec_")
        if exec_func() == QtWidgets.QDialog.Accepted:
            vset_name, variants = dialog.get_variants()
            if not variants:
                self._set_status("No variants selected.", error=True)
                return
            
            try:
                ok = _service.create_camera_variants(camera_path, vset_name, variants)
                if ok:
                    self._set_status("Added VariantSet '" + vset_name + "' to " + camera_path)
                else:
                    self._set_status("Failed to create variants (see log).", error=True)
            except Exception as exc:  # noqa: BLE001
                self._set_status("Failed: " + str(exc), error=True)
                _log.exception("Camera variants creation failed")

    def _set_status(self, message: str, error: bool = False) -> None:
        """Update the status label (red on error)."""
        self._status.setStyleSheet("color: #cc5555;" if error else "")
        self._status.setText(message)


class CameraExportDialog(QtWidgets.QDialog):
    """Dialog to configure and trigger camera export."""

    def __init__(self, camera_path: str, default_range: Tuple[int, int], parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Export Camera")
        self.camera_path = camera_path

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        # Filename base
        cam_name = camera_path.split("/")[-1]
        self._name_edit = QtWidgets.QLineEdit(cam_name)
        form.addRow("Filename Base:", self._name_edit)

        # Output Directory
        self._dir_edit = QtWidgets.QLineEdit()
        import os  # noqa: PLC0415
        try:
            import hou  # noqa: PLC0415
            job = hou.getenv("JOB")
            if job:
                self._dir_edit.setText(os.path.join(job, "export", "camera").replace("\\", "/"))
            else:
                self._dir_edit.setText(os.path.join(os.path.expanduser("~"), "Desktop").replace("\\", "/"))
        except Exception:  # noqa: BLE001
            self._dir_edit.setText(os.path.expanduser("~").replace("\\", "/"))

        dir_row = QtWidgets.QHBoxLayout()
        dir_row.addWidget(self._dir_edit)
        self._browse_btn = QtWidgets.QPushButton("Browse...")
        self._browse_btn.clicked.connect(self._on_browse)
        dir_row.addWidget(self._browse_btn)
        form.addRow("Output Directory:", dir_row)

        # Formats
        format_layout = QtWidgets.QHBoxLayout()
        self._usd_cb = QtWidgets.QCheckBox("USD (.usd)")
        self._usd_cb.setChecked(True)
        self._abc_cb = QtWidgets.QCheckBox("Alembic (.abc)")
        self._abc_cb.setChecked(True)
        self._nk_cb = QtWidgets.QCheckBox("Nuke (.nk)")
        self._nk_cb.setChecked(True)
        format_layout.addWidget(self._usd_cb)
        format_layout.addWidget(self._abc_cb)
        format_layout.addWidget(self._nk_cb)
        form.addRow("Formats:", format_layout)

        # Frame Range
        self._start_spin = QtWidgets.QSpinBox()
        self._start_spin.setRange(-999999, 999999)
        self._start_spin.setValue(int(default_range[0]))
        self._end_spin = QtWidgets.QSpinBox()
        self._end_spin.setRange(-999999, 999999)
        self._end_spin.setValue(int(default_range[1]))
        
        range_layout = QtWidgets.QHBoxLayout()
        range_layout.addWidget(QtWidgets.QLabel("Start:"))
        range_layout.addWidget(self._start_spin)
        range_layout.addWidget(QtWidgets.QLabel("End:"))
        range_layout.addWidget(self._end_spin)
        form.addRow("Frame Range:", range_layout)

        layout.addLayout(form)

        # Buttons
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        _style.apply(self)
        self.resize(450, 200)

    def _on_browse(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self._dir_edit.text()
        )
        if path:
            self._dir_edit.setText(path.replace("\\", "/"))

    def get_config(self) -> dict:
        formats = []
        if self._usd_cb.isChecked():
            formats.append("usd")
        if self._abc_cb.isChecked():
            formats.append("alembic")
        if self._nk_cb.isChecked():
            formats.append("nuke")

        return {
            "output_dir": self._dir_edit.text().strip(),
            "file_name_base": self._name_edit.text().strip() or "exported_cam",
            "formats": formats,
            "start_frame": self._start_spin.value(),
            "end_frame": self._end_spin.value(),
        }


class CameraVariantsDialog(QtWidgets.QDialog):
    """Dialog to configure camera VariantSet."""
    
    def __init__(self, camera_path: str, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Camera Variants")
        self.camera_path = camera_path
        
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        
        self._vset_type = QtWidgets.QComboBox()
        self._vset_type.addItem("Lens (Focal Lengths)", "lens")
        self._vset_type.addItem("Angle (Transforms)", "angle")
        self._vset_type.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("VariantSet Type:", self._vset_type)
        
        self._vset_name = QtWidgets.QLineEdit("lens")
        form.addRow("VariantSet Name:", self._vset_name)
        
        self._lens_group = QtWidgets.QWidget()
        lens_layout = QtWidgets.QVBoxLayout(self._lens_group)
        lens_layout.setContentsMargins(0, 0, 0, 0)
        self._wide_cb = QtWidgets.QCheckBox("Wide (24mm)")
        self._wide_cb.setChecked(True)
        self._medium_cb = QtWidgets.QCheckBox("Medium (50mm)")
        self._medium_cb.setChecked(True)
        self._tight_cb = QtWidgets.QCheckBox("Tight (85mm)")
        self._tight_cb.setChecked(True)
        lens_layout.addWidget(self._wide_cb)
        lens_layout.addWidget(self._medium_cb)
        lens_layout.addWidget(self._tight_cb)
        form.addRow("Select Lenses:", self._lens_group)
        
        self._angle_group = QtWidgets.QWidget()
        angle_layout = QtWidgets.QVBoxLayout(self._angle_group)
        angle_layout.setContentsMargins(0, 0, 0, 0)
        self._front_cb = QtWidgets.QCheckBox("Front (tx=0, tz=10, ry=0)")
        self._front_cb.setChecked(True)
        self._side_cb = QtWidgets.QCheckBox("Side (tx=10, tz=0, ry=90)")
        self._side_cb.setChecked(True)
        self._three_quarter_cb = QtWidgets.QCheckBox("3/4 View (tx=7.07, tz=7.07, ry=45)")
        self._three_quarter_cb.setChecked(True)
        self._top_cb = QtWidgets.QCheckBox("Top View (ty=10, rx=-90)")
        self._top_cb.setChecked(True)
        angle_layout.addWidget(self._front_cb)
        angle_layout.addWidget(self._side_cb)
        angle_layout.addWidget(self._three_quarter_cb)
        angle_layout.addWidget(self._top_cb)
        form.addRow("Select Angles:", self._angle_group)
        
        self._angle_group.setVisible(False)
        layout.addLayout(form)
        
        # Buttons
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        _style.apply(self)
        self.resize(380, 250)
        
    def _on_type_changed(self) -> None:
        is_lens = self._vset_type.currentData() == "lens"
        self._vset_name.setText("lens" if is_lens else "angle")
        self._lens_group.setVisible(is_lens)
        self._angle_group.setVisible(not is_lens)
        
    def get_variants(self) -> Tuple[str, list]:
        vset_name = self._vset_name.text().strip() or "variants"
        vtype = self._vset_type.currentData()
        variants = []
        
        if vtype == "lens":
            if self._wide_cb.isChecked():
                variants.append(_core.CameraVariantSpec("wide_24mm", 24.0))
            if self._medium_cb.isChecked():
                variants.append(_core.CameraVariantSpec("medium_50mm", 50.0))
            if self._tight_cb.isChecked():
                variants.append(_core.CameraVariantSpec("tight_85mm", 85.0))
        else:
            # Angles
            if self._front_cb.isChecked():
                variants.append(_core.CameraVariantSpec("front", 50.0, tx=0.0, ty=0.0, tz=10.0, rx=0.0, ry=0.0, rz=0.0))
            if self._side_cb.isChecked():
                variants.append(_core.CameraVariantSpec("side", 50.0, tx=10.0, ty=0.0, tz=0.0, rx=0.0, ry=90.0, rz=0.0))
            if self._three_quarter_cb.isChecked():
                variants.append(_core.CameraVariantSpec("three_quarter", 50.0, tx=7.07, ty=0.0, tz=7.07, rx=0.0, ry=45.0, rz=0.0))
            if self._top_cb.isChecked():
                variants.append(_core.CameraVariantSpec("top", 50.0, tx=0.0, ty=10.0, tz=0.0, rx=-90.0, ry=0.0, rz=0.0))
                
        return vset_name, variants


def launch(parent: Optional[object] = None) -> "CameraManagerWidget":
    """Create, show, and return a :class:`CameraManagerWidget`."""
    if parent is None:
        parent = _houdini_main_window()
    widget = CameraManagerWidget(parent)
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

