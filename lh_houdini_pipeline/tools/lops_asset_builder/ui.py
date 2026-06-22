"""
lh_houdini_pipeline.tools.lops_asset_builder.ui
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PySide UI for the LOPs component-asset builder -- a thin view over ``core``
(pure planning) and ``service`` (hou build / save).

Threading note
--------------
Creating LOP nodes touches ``hou`` and therefore MUST run on Houdini's main
thread -- node creation is not thread-safe.  So *Build* runs synchronously but
reports staged progress (geometry -> materials -> assign -> output) so the UI
stays informative.  The genuinely slow, IO-bound step (*Save*) is offloaded
through Houdini's own background execution (``executebackground``), which is
the safe non-blocking mechanism -- mirroring how the TexToMtlx tool threads
the ``imaketx`` subprocess rather than any ``hou`` calls.
"""

from __future__ import annotations

from typing import Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.lops_asset_builder import core as _core
from lh_houdini_pipeline.tools.lops_asset_builder import service as _service

_log = get_logger(__name__)

try:  # pragma: no cover - binding choice is environment-specific
    from PySide2 import QtCore, QtWidgets  # type: ignore
    _QT = "PySide2"
except ImportError:  # pragma: no cover
    from PySide6 import QtCore, QtWidgets  # type: ignore
    _QT = "PySide6"


class LopsAssetBuilderWidget(QtWidgets.QWidget):
    """Asset name + geometry + textures -> a USD component asset in /stage."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("LOPs Asset Builder  (MVP)")
        self._result = None     # AssetBuildResult after a build
        self._buttons = []
        self._build_ui()

    # -- construction ---------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble the form, action buttons, progress bar and status label."""
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self._name_edit = QtWidgets.QLineEdit()
        self._name_edit.setPlaceholderText("AssetName")
        form.addRow("Asset name:", self._name_edit)

        self._geo_edit, geo_row = self._path_row("Geometry file...")
        form.addRow("Geometry:", geo_row)

        self._tex_edit, tex_row = self._path_row("Texture folder (optional)...")
        form.addRow("Textures:", tex_row)

        self._out_edit, out_row = self._path_row("Output folder (optional)...")
        form.addRow("Output dir:", out_row)

        layout.addLayout(form)

        # Action buttons
        btn_row = QtWidgets.QHBoxLayout()
        build_btn = QtWidgets.QPushButton("Build Asset")
        build_btn.clicked.connect(self._on_build)
        self._save_btn = QtWidgets.QPushButton("Save USD (background)")
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(build_btn)
        btn_row.addWidget(self._save_btn)
        self._buttons += [build_btn, self._save_btn]
        layout.addLayout(btn_row)

        # Progress + status
        self._progress = QtWidgets.QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)
        self._status = QtWidgets.QLabel("Ready.")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        self.resize(480, 240)

    def _path_row(self, placeholder: str):
        """Return ``(line_edit, container_widget)`` for a path + Browse pair."""
        container = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        edit = QtWidgets.QLineEdit()
        edit.setPlaceholderText(placeholder)
        browse = QtWidgets.QPushButton("...")
        browse.setFixedWidth(30)
        is_file = "file" in placeholder.lower()
        browse.clicked.connect(lambda: self._browse(edit, is_file))
        row.addWidget(edit, 1)
        row.addWidget(browse)
        return edit, container

    # -- handlers -------------------------------------------------------

    def _browse(self, edit, is_file: bool) -> None:
        """Fill *edit* from a file or directory chooser."""
        if is_file:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Choose geometry", edit.text() or ""
            )
        else:
            path = QtWidgets.QFileDialog.getExistingDirectory(
                self, "Choose folder", edit.text() or ""
            )
        if path:
            edit.setText(path)

    def _on_build(self) -> None:
        """Plan + build the asset on the main thread with staged progress."""
        name = self._name_edit.text().strip()
        if not name:
            self._set_status("Enter an asset name.", error=True)
            return
        geo = self._geo_edit.text().strip() or None
        tex = self._tex_edit.text().strip() or None
        out = self._out_edit.text().strip() or None

        try:
            plan = _core.plan_asset(name, geo_path=geo, tex_folder=tex, output_dir=out)
        except Exception as exc:  # noqa: BLE001
            self._set_status("Plan failed: " + str(exc), error=True)
            return

        self._progress.setMaximum(4)
        self._progress.setValue(0)
        self._progress.setVisible(True)
        self._set_buttons_enabled(False)
        try:
            self._result = _service.build_asset(plan, on_stage=self._on_stage)
        except Exception as exc:  # noqa: BLE001
            self._progress.setVisible(False)
            self._set_buttons_enabled(True)
            self._set_status("Build failed: " + str(exc), error=True)
            _log.exception("Asset build failed")
            return

        self._progress.setVisible(False)
        self._set_buttons_enabled(True)
        self._save_btn.setEnabled(self._result.output != "")
        mats = ", ".join(self._result.materials_built) or "no materials"
        self._set_status(
            "Built '" + self._result.asset_name + "' (" + mats + ") at "
            + self._result.output
        )

    def _on_stage(self, step: int, total: int, label: str) -> None:
        """Progress callback from ``build_asset`` (runs on the main thread)."""
        self._progress.setValue(step)
        self._set_status("Building " + label + " (" + str(step) + "/" + str(total) + ")...")
        QtWidgets.QApplication.processEvents()

    def _on_save(self) -> None:
        """Trigger a non-blocking background save of the built asset."""
        if self._result is None:
            self._set_status("Build an asset first.", error=True)
            return
        try:
            started = _service.save_asset_background(self._result)
        except Exception as exc:  # noqa: BLE001
            self._set_status("Save failed: " + str(exc), error=True)
            _log.exception("Asset save failed")
            return
        if started:
            self._set_status("Saving USD in the background -- check the output folder.")
        else:
            self._set_status("Could not start save (no output node).", error=True)

    # -- helpers --------------------------------------------------------

    def _set_buttons_enabled(self, enabled: bool) -> None:
        """Enable/disable action buttons while a build runs."""
        for btn in self._buttons:
            btn.setEnabled(enabled)

    def _set_status(self, message: str, error: bool = False) -> None:
        """Update the status label (red on error)."""
        self._status.setStyleSheet("color: #cc5555;" if error else "")
        self._status.setText(message)


def launch(parent: Optional[object] = None) -> "LopsAssetBuilderWidget":
    """Create, show, and return a :class:`LopsAssetBuilderWidget`."""
    if parent is None:
        parent = _houdini_main_window()
    widget = LopsAssetBuilderWidget(parent)
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
