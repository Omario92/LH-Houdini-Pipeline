"""
lh_houdini_pipeline.tools.houdini_ai_assistant.ui.approval
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Modal approval dialog to preview and permit scene modifications proposed by the AI.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from lh_houdini_pipeline.ui import style as _style

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets


class ActionApprovalDialog(QtWidgets.QDialog):
    """Modal dialog displaying proposed node manipulations for artist review."""

    def __init__(
        self,
        action_name: str,
        arguments: Dict[str, Any],
        parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.action_name = action_name
        self.arguments = arguments
        self.setWindowTitle("AI Action Approval Required")
        self.setMinimumSize(500, 350)
        self.setModal(True)
        # Houdini + alt-tab hardening: a plain modal QDialog can lose activation
        # when the artist switches apps and comes back, ending up behind another
        # window and unclickable. ApplicationModal + StaysOnTop + raise/activate
        # on show keeps the approval prompt foremost and interactive.
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowFlags(
            self.windowFlags() | QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint
        )

        self._build_ui()
        _style.apply(self)

    def showEvent(self, event) -> None:  # noqa: N802
        """Force the dialog foremost + active so its buttons always take clicks."""
        super().showEvent(event)
        self.raise_()
        self.activateWindow()

    def focusInEvent(self, event) -> None:  # noqa: N802
        super().focusInEvent(event)
        self.raise_()

    def _build_ui(self) -> None:
        """Construct visual elements including title, details text box, and buttons."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Title/Description
        header_label = QtWidgets.QLabel("The AI Assistant has proposed a modifying scene action:")
        header_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #ff9000;")
        layout.addWidget(header_label)

        # Diff / Detail Area
        self._preview_edit = QtWidgets.QPlainTextEdit()
        self._preview_edit.setReadOnly(True)
        self._preview_edit.setStyleSheet(_style.LOG_STYLE)
        
        # Populate Preview Text
        preview_text = self._generate_preview_text()
        self._preview_edit.setPlainText(preview_text)
        layout.addWidget(self._preview_edit, 1)

        # Warning / Safety Reminder
        warning_lbl = QtWidgets.QLabel(
            "⚠️ Warning: Execution will run on Houdini's main UI thread. "
            "Please verify the action is safe."
        )
        warning_lbl.setStyleSheet("color: #e0a33c; font-style: italic; font-size: 11px;")
        layout.addWidget(warning_lbl)

        # Bottom Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self._approve_btn = QtWidgets.QPushButton("Approve & Execute")
        self._approve_btn.setObjectName("primaryBtn")
        self._approve_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self._approve_btn)

        self._reject_btn = QtWidgets.QPushButton("Reject")
        self._reject_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._reject_btn)

        layout.addLayout(btn_layout)

    def _generate_preview_text(self) -> str:
        """Parse arguments and build a clean visual representation of the tool execution."""
        lines = []
        lines.append(f"Proposed Tool Call: {self.action_name.upper()}")
        lines.append("=" * 60)

        if self.action_name == "create_node":
            parent = self.arguments.get("parent_path", "/")
            ntype = self.arguments.get("node_type", "null")
            name = self.arguments.get("node_name", "(default name)")
            lines.append("[+] ACTION: CREATE NODE")
            lines.append(f"    - Parent Path : {parent}")
            lines.append(f"    - Node Type   : {ntype}")
            lines.append(f"    - Node Name   : {name}")

        elif self.action_name == "set_parm":
            path = self.arguments.get("node_path", "/")
            parms = self.arguments.get("parm_values", {})
            lines.append("[*] ACTION: SET PARAMETERS")
            lines.append(f"    - Target Node: {path}")
            lines.append("    - Parameters to Set:")
            for k, v in parms.items():
                lines.append(f"      - `{k}` -> {v}")

        elif self.action_name == "run_python_snippet":
            code = self.arguments.get("code", "")
            lines.append("[!] ACTION: RUN PYTHON CODE SNIPPET")
            lines.append("-" * 60)
            lines.append(code)
            lines.append("-" * 60)

        elif self.action_name == "layout_network":
            parent = self.arguments.get("parent_path", "/")
            lines.append("[*] ACTION: LAYOUT NETWORK")
            lines.append(f"    - Target Path: {parent}")

        elif self.action_name == "generate_hda_scaffold":
            parent = self.arguments.get("parent_path", "/")
            ntype = self.arguments.get("node_type", "subnet")
            name = self.arguments.get("hda_name", "my_hda")
            lines.append("[+] ACTION: GENERATE HDA SCAFFOLD NETWORK")
            lines.append(f"    - Parent Path : {parent}")
            lines.append(f"    - Node Type   : {ntype}")
            lines.append(f"    - Name        : {name}")

        else:
            # Generic representation
            lines.append("Arguments:")
            try:
                lines.append(json.dumps(self.arguments, indent=4))
            except Exception:
                lines.append(str(self.arguments))

        return "\n".join(lines)


# -- Launch Helper ----------------------------------------------------------

def request_approval(action_name: str, arguments: Dict[str, Any], parent: Optional[QtWidgets.QWidget] = None) -> bool:
    """Convenience helper to show the ActionApprovalDialog modally.

    Returns:
        True if the user approved the action, False otherwise.
    """
    if parent is None:
        try:
            import hou  # noqa: PLC0415
            parent = hou.qt.mainWindow()
        except Exception:  # noqa: BLE001
            parent = None

    dialog = ActionApprovalDialog(action_name, arguments, parent)
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
    result = dialog.exec()
    # PySide6/2 QDialog returns Accepted (1) or Rejected (0)
    # Re-evaluate enum safely
    accepted_val = getattr(QtWidgets.QDialog, "Accepted", 1)
    if not isinstance(accepted_val, int): # PySide6 enum nesting
        accepted_val = QtWidgets.QDialog.DialogCode.Accepted
    return result == accepted_val
