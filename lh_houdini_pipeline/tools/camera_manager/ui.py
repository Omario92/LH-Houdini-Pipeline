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

from typing import Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.camera_manager import core as _core
from lh_houdini_pipeline.tools.camera_manager import service as _service

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
        create_btn.clicked.connect(self._on_create)
        layout.addWidget(create_btn)

        layout.addWidget(QtWidgets.QLabel("Existing cameras:"))
        self._list = QtWidgets.QListWidget()
        layout.addWidget(self._list, 1)

        self._status = QtWidgets.QLabel("Ready.")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

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
            self._list.addItem(
                info.path + "   f=" + str(round(info.focal_length, 1)) + "mm" + res
            )
        self._set_status(str(len(cams)) + " camera(s) in "
                         + self._current_context().value)

    def _set_status(self, message: str, error: bool = False) -> None:
        """Update the status label (red on error)."""
        self._status.setStyleSheet("color: #cc5555;" if error else "")
        self._status.setText(message)


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
