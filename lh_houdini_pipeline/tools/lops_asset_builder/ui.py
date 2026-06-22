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
the safe non-blocking mechanism.

For texture conversion, we run ``imaketx`` in a background thread using a QObject
worker with queued signals to keep the UI active.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Optional, Tuple

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.lops_asset_builder import core as _core
from lh_houdini_pipeline.tools.lops_asset_builder import service as _service
from lh_houdini_pipeline.ui import style as _style

_log = get_logger(__name__)

# -- Qt binding (PySide2 first, then PySide6) -------------------------------
try:  # pragma: no cover - binding choice is environment-specific
    from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore
    _QT = "PySide2"
except ImportError:  # pragma: no cover
    from PySide6 import QtCore, QtGui, QtWidgets  # type: ignore
    _QT = "PySide6"


class QTextEditLogger(QtCore.QObject, logging.Handler):
    """Custom logging handler that emits a Qt signal for each log record."""

    log_emitted = QtCore.Signal(str, str)  # message, levelname

    def __init__(self) -> None:
        QtCore.QObject.__init__(self)
        logging.Handler.__init__(self)
        self.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.log_emitted.emit(msg, record.levelname)


class CollapsibleGroupBox(QtWidgets.QWidget):
    """A clean PySide collapsible container widget."""

    def __init__(self, title: str, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toggle_btn = QtWidgets.QPushButton(f"▶  {title}")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(False)
        self.toggle_btn.setStyleSheet(
            "QPushButton {"
            "    text-align: left;"
            "    font-weight: bold;"
            "    border: none;"
            "    background: transparent;"
            "    padding: 6px 2px;"
            "    color: #e0e0e0;"
            "}"
            "QPushButton:hover {"
            "    color: #ff9000;"
            "}"
        )
        self.toggle_btn.toggled.connect(self._on_toggle)
        layout.addWidget(self.toggle_btn)

        self.content = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(15, 4, 5, 8)
        self.content.setVisible(False)
        layout.addWidget(self.content)

    def _on_toggle(self, checked: bool) -> None:
        title = self.toggle_btn.text()[3:]
        if checked:
            self.toggle_btn.setText(f"▼  {title}")
            self.content.setVisible(True)
        else:
            self.toggle_btn.setText(f"▶  {title}")
            self.content.setVisible(False)

    def add_widget(self, widget: QtWidgets.QWidget) -> None:
        self.content_layout.addWidget(widget)

    def add_layout(self, layout: QtWidgets.QLayout) -> None:
        self.content_layout.addLayout(layout)


class _TxWorker(QtCore.QObject):
    """Runs the imaketx batch off the UI thread, reporting progress via signals."""

    progress = QtCore.Signal(int, int, str)   # done, total, source name
    finished = QtCore.Signal(int, int)         # ok_count, total
    failed = QtCore.Signal(str)

    def __init__(self, infos: list, out_dir: Optional[str], dry_run: bool) -> None:
        super().__init__()
        self._infos = list(infos)
        self._out_dir = out_dir
        self._dry_run = dry_run

    def run(self) -> None:
        """Convert all textures, emitting progress after each file."""
        try:
            from lh_houdini_pipeline.tools.tex_to_mtlx import service as _tex_service
            def _cb(done, total, res):
                self.progress.emit(done, total, res.spec.source.name)
            results = _tex_service.convert_textures_to_tx(
                self._infos, out_dir=self._out_dir,
                dry_run=self._dry_run, on_each=_cb,
            )
            ok = sum(1 for r in results if r.success)
            self.finished.emit(ok, len(results))
        except Exception as exc:  # noqa: BLE001
            _log.exception("tx worker failed")
            self.failed.emit(str(exc))


class LopsAssetBuilderWidget(QtWidgets.QWidget):
    """Redesigned component-asset builder UI with Drag & Drop, validation, and logs."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("LOPs Asset Builder")
        self.setAcceptDrops(True)
        
        self._result = None     # AssetBuildResult after a build
        self._buttons = []
        self._tx_worker = None
        self._tx_thread = None

        self._build_ui()
        self._setup_logger()
        self._validate_inputs()

    def _build_ui(self) -> None:
        """Assemble form elements, collapsible options, log area, and main buttons."""
        self._setup_stylesheet()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header Block
        header_layout = QtWidgets.QHBoxLayout()
        title_lbl = QtWidgets.QLabel("LOPs Asset Builder")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff9000;")
        version_lbl = QtWidgets.QLabel("v1.2.0")
        version_lbl.setStyleSheet("font-size: 10px; color: #888888; margin-top: 4px;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(version_lbl)
        layout.addLayout(header_layout)

        # Form fields
        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 4, 0, 4)
        form.setSpacing(6)

        self._name_edit = QtWidgets.QLineEdit()
        self._name_edit.setPlaceholderText("e.g. hero_car")
        self._name_edit.setToolTip("Name of the root primitive and created nodes (sanitized live).")
        self._name_edit.textChanged.connect(self._on_name_changed)
        form.addRow("Asset Name:", self._name_edit)

        self._geo_edit, geo_row = self._path_row("Choose or drop geometry file (.fbx, .obj, .abc, .usd)...", is_file=True)
        form.addRow("Geometry File:", geo_row)

        self._tex_edit, tex_row = self._path_row("Choose or drop texture folder (optional)...", is_file=False)
        form.addRow("Texture Folder:", tex_row)

        self._out_edit, out_row = self._path_row("Choose or drop output USD directory (optional)...", is_file=False)
        form.addRow("Output Directory:", out_row)

        layout.addLayout(form)

        # Collapsible Advanced Options
        self._options_group = CollapsibleGroupBox("Advanced Options", self)
        
        self._sim_proxy_cb = QtWidgets.QCheckBox("Generate Sim Proxy (Convex Hull)")
        self._sim_proxy_cb.setToolTip("Generate a convex hull SOP inside the asset's geometry and bind it to simproxy.")
        self._sim_proxy_cb.setChecked(False)
        
        proxy_quality_layout = QtWidgets.QHBoxLayout()
        proxy_quality_layout.setContentsMargins(0, 0, 0, 0)
        proxy_quality_lbl = QtWidgets.QLabel("Proxy Quality:")
        self._proxy_quality_cb = QtWidgets.QComboBox()
        self._proxy_quality_cb.addItems(["Low", "Medium", "High"])
        self._proxy_quality_cb.setCurrentText("Medium")
        proxy_quality_layout.addWidget(proxy_quality_lbl)
        proxy_quality_layout.addWidget(self._proxy_quality_cb)
        proxy_quality_layout.addStretch()
        
        self._convert_tx_cb = QtWidgets.QCheckBox("Auto convert textures to .tx")
        self._convert_tx_cb.setToolTip("Process texture folder using imaketx in a background thread before building.")
        self._convert_tx_cb.setChecked(True)

        self._options_group.add_widget(self._sim_proxy_cb)
        self._options_group.add_layout(proxy_quality_layout)
        self._options_group.add_widget(self._convert_tx_cb)
        layout.addWidget(self._options_group)

        # Log Area
        log_header = QtWidgets.QHBoxLayout()
        log_header.setContentsMargins(0, 2, 0, 0)
        log_lbl = QtWidgets.QLabel("Console Log:")
        log_lbl.setStyleSheet("font-weight: bold; color: #aaaaaa;")
        clear_log_btn = QtWidgets.QPushButton("Clear Log")
        clear_log_btn.setFixedWidth(70)
        clear_log_btn.setStyleSheet("padding: 2px 4px; font-size: 10px;")
        clear_log_btn.clicked.connect(self._on_clear_log)
        log_header.addWidget(log_lbl)
        log_header.addStretch()
        log_header.addWidget(clear_log_btn)
        layout.addLayout(log_header)

        self._log_text = QtWidgets.QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setStyleSheet(
            "QTextEdit {"
            "    background-color: #1A1A1A;"
            "    color: #DFDFDF;"
            "    font-family: 'Consolas', 'Courier New', monospace;"
            "    font-size: 10px;"
            "    border: 1px solid #3A3A3A;"
            "    border-radius: 3px;"
            "}"
        )
        layout.addWidget(self._log_text, 1)

        # Progress bar
        self._progress = QtWidgets.QProgressBar()
        self._progress.setVisible(False)
        self._progress.setFixedHeight(12)
        layout.addWidget(self._progress)

        # Action Buttons
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(6)
        
        self._build_btn = QtWidgets.QPushButton("Build Asset")
        self._build_btn.setObjectName("primaryBtn")
        self._build_btn.setToolTip("Build LOP network and save USD file synchronously on main thread.")
        self._build_btn.clicked.connect(lambda: self._on_build_triggered(background=False))
        self._build_btn.setStyleSheet("font-weight: bold; height: 24px;")
        
        self._build_bg_btn = QtWidgets.QPushButton("Build in Background")
        self._build_bg_btn.setToolTip("Build LOP network on main thread, but trigger USD file saving in the background thread.")
        self._build_bg_btn.clicked.connect(lambda: self._on_build_triggered(background=True))
        self._build_bg_btn.setStyleSheet("font-weight: bold; height: 24px; color: #ff9000;")
        
        btn_row.addWidget(self._build_btn)
        btn_row.addWidget(self._build_bg_btn)
        self._buttons += [self._build_btn, self._build_bg_btn]
        layout.addLayout(btn_row)

        # Status Bar
        self._status = QtWidgets.QLabel("Ready.")
        self._status.setWordWrap(True)
        self._status.setStyleSheet("color: #888888;")
        layout.addWidget(self._status)

        self.resize(520, 480)

    def _path_row(self, placeholder: str, is_file: bool) -> Tuple[QtWidgets.QLineEdit, QtWidgets.QWidget]:
        """Return ``(line_edit, container_widget)`` for a path + Browse pair."""
        container = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        
        edit = QtWidgets.QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.textChanged.connect(self._validate_inputs)
        
        browse = QtWidgets.QPushButton("...")
        browse.setFixedWidth(30)
        browse.clicked.connect(lambda: self._browse(edit, is_file))
        
        row.addWidget(edit, 1)
        row.addWidget(browse)
        return edit, container

    def _setup_logger(self) -> None:
        """Initialize custom logging handler and bind to pipeline logger."""
        self._logger_handler = QTextEditLogger()
        self._logger_handler.log_emitted.connect(self._on_log_emitted)
        logging.getLogger("lh_houdini_pipeline").addHandler(self._logger_handler)

    def closeEvent(self, event: QtCore.QEvent) -> None:
        """Clean up logging handler when widget closes to prevent leaks."""
        logging.getLogger("lh_houdini_pipeline").removeHandler(self._logger_handler)
        super().closeEvent(event)

    # -- drag and drop --------------------------------------------------

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return

        files = [u.toLocalFile() for u in urls]
        geo_exts = (".fbx", ".obj", ".abc", ".usd", ".usda", ".usdc")
        geo_file = None
        tex_folder = None
        out_dir = None

        # Sort dropped items
        for f in files:
            if os.path.isfile(f) and f.lower().endswith(geo_exts):
                geo_file = f
                break
        
        for f in files:
            if os.path.isdir(f):
                # If both a texture and output directory are dropped, assign respectively
                if not tex_folder:
                    tex_folder = f
                else:
                    out_dir = f
                    break

        # Fallbacks if only a single item was dropped
        if not geo_file and not tex_folder and not out_dir:
            item = files[0]
            if os.path.isfile(item):
                if item.lower().endswith(geo_exts):
                    geo_file = item
                else:
                    self._log_msg(f"Unsupported file format dropped: {os.path.basename(item)}", "WARNING")
            elif os.path.isdir(item):
                tex_folder = item

        # Apply values
        if geo_file:
            clean_geo = os.path.normpath(geo_file).replace("\\", "/")
            self._geo_edit.setText(clean_geo)
            self._log_msg(f"Dropped Geometry File: {clean_geo}", "INFO")
            
            # Auto-populate asset name
            base = os.path.splitext(os.path.basename(geo_file))[0]
            self._name_edit.setText(self._sanitize_name_string(base))

        if tex_folder:
            clean_tex = os.path.normpath(tex_folder).replace("\\", "/")
            self._tex_edit.setText(clean_tex)
            self._log_msg(f"Dropped Texture Folder: {clean_tex}", "INFO")

        if out_dir:
            clean_out = os.path.normpath(out_dir).replace("\\", "/")
            self._out_edit.setText(clean_out)
            self._log_msg(f"Dropped Output Directory: {clean_out}", "INFO")

        self._validate_inputs()

    # -- handlers & slots ------------------------------------------------

    def _on_name_changed(self, text: str) -> None:
        """Sanitize asset name string live as user types."""
        cursor_pos = self._name_edit.cursorPosition()
        sanitized = self._sanitize_name_string(text)
        if sanitized != text:
            # Temporarily block signals to prevent recursive loops
            self._name_edit.blockSignals(True)
            self._name_edit.setText(sanitized)
            self._name_edit.setCursorPosition(min(cursor_pos, len(sanitized)))
            self._name_edit.blockSignals(False)
        self._validate_inputs()

    def _sanitize_name_string(self, text: str) -> str:
        """Sanitize name to match alphanumeric/underscore requirements."""
        out = []
        for ch in text.strip():
            out.append(ch if (ch.isalnum() or ch == "_") else "_")
        safe = "".join(out).strip("_")
        if not safe:
            safe = "asset"
        if safe[0].isdigit():
            safe = "a_" + safe
        return safe

    def _validate_inputs(self, *args) -> None:
        """Realtime input validation to toggle Build buttons."""
        name = self._name_edit.text().strip()
        geo = self._geo_edit.text().strip()

        is_valid = bool(name) and bool(geo) and os.path.isfile(geo)
        
        self._build_btn.setEnabled(is_valid)
        self._build_bg_btn.setEnabled(is_valid)

        if not name:
            self._set_status("Input validation: Enter an Asset Name.")
        elif not geo:
            self._set_status("Input validation: Geometry File path is required.")
        elif not os.path.isfile(geo):
            self._set_status("Input validation: Geometry File path must point to a valid file.", error=True)
        else:
            tex = self._tex_edit.text().strip()
            if tex and not os.path.isdir(tex):
                self._set_status("Input validation Warning: Texture Folder is invalid.", error=True)
            else:
                self._set_status("Ready.")

    def _browse(self, edit: QtWidgets.QLineEdit, is_file: bool) -> None:
        """Chooser dialog."""
        if is_file:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Choose Geometry File", edit.text() or "",
                "USD/Geometry Files (*.fbx *.obj *.abc *.usd *.usda *.usdc)"
            )
        else:
            path = QtWidgets.QFileDialog.getExistingDirectory(
                self, "Choose Directory", edit.text() or ""
            )
        if path:
            edit.setText(path.replace("\\", "/"))
            self._validate_inputs()

    def _on_clear_log(self) -> None:
        self._log_text.clear()

    def _on_log_emitted(self, message: str, level: str) -> None:
        """Write formatted logs directly to the text console."""
        color = "#DFDFDF"
        if level in ("ERROR", "CRITICAL"):
            color = "#ff6b6b"
        elif level == "WARNING":
            color = "#f3a638"
        elif level == "INFO":
            color = "#a2e3a2"

        html = f"<span style='color: {color};'>{message}</span>"
        self._log_text.append(html)

    def _log_msg(self, message: str, level: str = "INFO") -> None:
        """Self logging utility."""
        self._on_log_emitted(message, level)
        if level == "ERROR":
            _log.error(message)
        elif level == "WARNING":
            _log.warning(message)
        else:
            _log.info(message)

    # -- build execution -------------------------------------------------

    def _on_build_triggered(self, background: bool) -> None:
        """Master handler: runs texture conversions then HDA build."""
        name = self._name_edit.text().strip()
        geo = self._geo_edit.text().strip()
        tex = self._tex_edit.text().strip() or None
        out = self._out_edit.text().strip() or None
        
        sim_proxy = self._sim_proxy_cb.isChecked()
        proxy_quality = self._proxy_quality_cb.currentText()
        auto_tx = self._convert_tx_cb.isChecked()

        # Check if texture conversion should run first
        if auto_tx and tex and os.path.isdir(tex):
            self._log_msg("Scanning texture folder for conversion...", "INFO")
            from lh_houdini_pipeline.tools.tex_to_mtlx.core import scan_and_plan
            try:
                scan_res = scan_and_plan(tex)
                if scan_res.infos:
                    self._progress.setMaximum(len(scan_res.infos))
                    self._progress.setValue(0)
                    self._progress.setVisible(True)
                    self._set_buttons_enabled(False)
                    
                    self._log_msg(f"Starting async conversion of {len(scan_res.infos)} texture(s) to .tx...", "INFO")
                    
                    self._tx_worker = _TxWorker(scan_res.infos, out_dir=None, dry_run=False)
                    self._tx_worker.progress.connect(self._on_tx_progress)
                    self._tx_worker.finished.connect(
                        lambda ok, total: self._on_tx_finished(
                            ok, total, name, geo, tex, out, sim_proxy, proxy_quality, background
                        )
                    )
                    self._tx_worker.failed.connect(self._on_tx_failed)
                    
                    self._tx_thread = threading.Thread(target=self._tx_worker.run, daemon=True)
                    self._tx_thread.start()
                    return
                else:
                    self._log_msg("No textures found to convert. Proceeding to build.", "WARNING")
            except Exception as exc:  # noqa: BLE001
                self._log_msg(f"Texture scan failed: {exc}, proceeding directly to build.", "WARNING")

        # Fallthrough directly to HDA build
        try:
            plan = self._make_plan(name, geo, tex, out, sim_proxy, proxy_quality)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Planning failed: {exc}", error=True)
            self._log_msg(f"ERROR: Planning failed: {exc}", "ERROR")
            return
        self._execute_build(plan, background)

    def _on_tx_progress(self, done: int, total: int, name: str) -> None:
        self._progress.setValue(done)
        self._set_status(f"Converting textures: {done}/{total} ({os.path.basename(name)})")

    def _on_tx_finished(
        self,
        ok: int,
        total: int,
        name: str,
        geo: str,
        tex: Optional[str],
        out: Optional[str],
        sim_proxy: bool,
        proxy_quality: str,
        background: bool,
    ) -> None:
        self._progress.setVisible(False)
        self._log_msg(f"Finished texture conversion. {ok}/{total} succeeded.", "INFO")
        try:
            plan = self._make_plan(name, geo, tex, out, sim_proxy, proxy_quality)
        except Exception as exc:  # noqa: BLE001
            self._set_buttons_enabled(True)
            self._set_status(f"Planning failed after texture conversion: {exc}", error=True)
            self._log_msg(f"ERROR: Planning failed after texture conversion: {exc}", "ERROR")
            return
        self._execute_build(plan, background)

    def _on_tx_failed(self, error_msg: str) -> None:
        self._progress.setVisible(False)
        self._set_buttons_enabled(True)
        self._set_status("Texture conversion failed.", error=True)
        self._log_msg(f"ERROR: Texture conversion thread failed: {error_msg}", "ERROR")

    def _execute_build(self, plan: _core.AssetBuildPlan, background: bool) -> None:
        """Run node graph construction on Houdini main thread with progress hooks."""
        self._progress.setMaximum(4)
        self._progress.setValue(0)
        self._progress.setVisible(True)
        self._set_buttons_enabled(False)

        self._log_msg(f"Building LOP Asset: {plan.asset_name} ...", "INFO")
        
        try:
            self._result = _service.build_asset(plan, on_stage=self._on_stage)
        except Exception as exc:  # noqa: BLE001
            self._progress.setVisible(False)
            self._set_buttons_enabled(True)
            self._set_status(f"Build failed: {exc}", error=True)
            self._log_msg(f"ERROR: Build failed: {exc}", "ERROR")
            return

        self._progress.setVisible(False)
        self._set_buttons_enabled(True)

        if self._result and self._result.output:
            mats = ", ".join(self._result.materials_built) or "no materials"
            self._log_msg(f"LOP Node network created successfully. Materials built: {mats}", "INFO")
            
            if background:
                self._log_msg("Saving USD file in background...", "INFO")
                started = _service.save_asset_background(self._result)
                if started:
                    self._set_status("Build succeeded! USD is saving in the background.")
                else:
                    self._set_status("Build succeeded, but background save failed.", error=True)
            else:
                self._log_msg("Saving USD file (blocking main thread)...", "INFO")
                ok = _service.save_asset(self._result)
                if ok:
                    self._set_status(f"Build & Save successful! Output: {plan.output_file or 'Default LOP'}")
                    self._log_msg("USD saved successfully to disk.", "INFO")
                else:
                    self._set_status("Build succeeded, but USD save failed.", error=True)
        else:
            self._set_status("Build failed (empty output results).", error=True)

    def _make_plan(
        self,
        name: str,
        geo: str,
        tex: Optional[str],
        out: Optional[str],
        sim_proxy: bool,
        proxy_quality: str,
    ) -> _core.AssetBuildPlan:
        """Build a fresh asset plan from captured UI inputs."""
        return _core.plan_asset(
            name,
            geo_path=geo,
            tex_folder=tex,
            output_dir=out,
            generate_proxy=sim_proxy,
            proxy_quality=proxy_quality,
        )

    def _on_stage(self, step: int, total: int, label: str) -> None:
        """Main thread callback to update build progress bar."""
        self._progress.setValue(step)
        self._set_status(f"Building LOP network: {label} ({step}/{total})...")
        self._log_msg(f"Stage {step}/{total}: Built {label} nodes.", "INFO")
        QtWidgets.QApplication.processEvents()

    # -- helpers & styling -----------------------------------------------

    def _set_buttons_enabled(self, enabled: bool) -> None:
        for btn in self._buttons:
            btn.setEnabled(enabled)

    def _set_status(self, message: str, error: bool = False) -> None:
        self._status.setStyleSheet("color: #ff6b6b; font-weight: bold;" if error else "color: #aaaaaa;")
        self._status.setText(message)

    def _setup_stylesheet(self) -> None:
        """Apply the shared pipeline dark theme (orange accent + blue action)."""
        self.setStyleSheet(_style.STYLE)


def launch(parent: Optional[object] = None) -> LopsAssetBuilderWidget:
    """Create, show, and return a :class:`LopsAssetBuilderWidget`."""
    if parent is None:
        parent = _houdini_main_window()

    # Avoid duplicate instances
    if parent is not None:
        for child in parent.children():
            if child.objectName() == "LopsAssetBuilderWindow":
                child.close()
                child.deleteLater()

    widget = LopsAssetBuilderWidget(parent)
    widget.setObjectName("LopsAssetBuilderWindow")
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
