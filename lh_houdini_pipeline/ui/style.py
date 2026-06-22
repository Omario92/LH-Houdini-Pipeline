"""
lh_houdini_pipeline.ui.style
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The single source of truth for the pipeline tools' visual style.

Standardised from the LOPs Asset Builder and Project Manager designs:

* **Primary accent** -- Houdini orange ``#ff9000`` (focus rings, hover borders,
  checkboxes, progress) so the tools feel native to Houdini.
* **Primary action** -- blue ``#4a90d9`` for the main commit button
  (``objectName="primaryBtn"``): Create / Build / etc.
* **Caution action** -- amber ``#e0a33c`` for safe/dry-run buttons
  (``objectName="warnBtn"``).

Tools apply the look with one call::

    from lh_houdini_pipeline.ui import style
    style.apply(self)                      # sets the shared stylesheet
    create_btn.setObjectName("primaryBtn") # blue main action
    dryrun_btn.setObjectName("warnBtn")    # amber caution action

A shared :class:`DropLineEdit` (folder drag-and-drop) and a status-bar colour
map are provided so every tool behaves consistently.  PySide6 first, PySide2
fallback -- no ``hou`` import, so this module loads anywhere.
"""

from __future__ import annotations

import os
from typing import Optional

try:  # pragma: no cover
    from PySide6 import QtCore, QtGui, QtWidgets  # type: ignore
    _QT = "PySide6"
except ImportError:  # pragma: no cover
    from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore
    _QT = "PySide2"


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

BG          = "#2b2b2b"   # window background
BG_CARD     = "#323232"   # group-box / card background
BG_INPUT    = "#232323"   # text fields, trees
BG_LOG      = "#1a1a1a"   # console / log background
TEXT        = "#d4d4d4"
TEXT_DIM    = "#9aa0a6"

ACCENT      = "#ff9000"   # Houdini orange -- primary accent
ACTION      = "#4a90d9"   # blue -- primary action button
ACTION_HI   = "#5a9fe0"
WARN        = "#e0a33c"   # amber -- caution / dry-run
OK          = "#5cb85c"
ERROR       = "#d9534f"

#: Status-bar dot colours by level.
STATUS_COLORS = {"info": TEXT_DIM, "working": WARN, "done": OK, "error": ERROR}
#: Inline-validation message colours by level.
HINT_COLORS = {"": "#6f8db5", "warn": WARN, "error": ERROR}


# ---------------------------------------------------------------------------
# Stylesheet
# ---------------------------------------------------------------------------

STYLE = """
* { font-family: "Segoe UI", "Roboto", Arial, sans-serif; font-size: 12px; color: %(TEXT)s; }
QWidget#pmRoot, QWidget#toolRoot { background: %(BG)s; }
QGroupBox {
    background: %(BG_CARD)s; border: 1px solid #3c3c3c; border-radius: 8px;
    margin-top: 26px; padding: 16px 12px 14px 12px;
}
QGroupBox::title {
    subcontrol-origin: margin; subcontrol-position: top left;
    left: 14px; top: 2px; padding: 0 6px;
    color: %(TEXT_DIM)s; font-weight: 600; text-transform: uppercase;
    letter-spacing: 1px; font-size: 11px;
}
QLabel#fieldLabel { color: #b8b8b8; }
QLabel#hintLabel  { color: #6f8db5; font-style: italic; }
QLabel#titleLabel { color: %(ACCENT)s; font-size: 14px; font-weight: 700; }
QLineEdit, QPlainTextEdit, QTreeWidget, QListWidget, QComboBox, QSpinBox, QDoubleSpinBox {
    background: %(BG_INPUT)s; border: 1px solid #3a3a3a; border-radius: 5px;
    padding: 5px 7px; selection-background-color: %(ACCENT)s; selection-color: #1a1a1a;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid %(ACCENT)s; }
QLineEdit[dropActive="true"] { border: 1px dashed %(ACCENT)s; background: #2f2a20; }
QComboBox::drop-down { border: none; width: 18px; }
QPushButton {
    background: #3a3a3a; border: 1px solid #474747; border-radius: 6px;
    padding: 7px 14px; color: #e0e0e0;
}
QPushButton:hover { background: #444444; border: 1px solid %(ACCENT)s; }
QPushButton:pressed { background: #2e2e2e; }
QPushButton:disabled { background: #2f2f2f; color: #6a6a6a; border-color: #3a3a3a; }
QPushButton#primaryBtn {
    background: %(ACTION)s; border: 1px solid %(ACTION_HI)s; color: #ffffff; font-weight: 600;
}
QPushButton#primaryBtn:hover { background: %(ACTION_HI)s; border: 1px solid %(ACTION_HI)s; }
QPushButton#primaryBtn:disabled { background: #34465a; color: #7e8b99; border-color: #34465a; }
QPushButton#warnBtn { background: #5a4a2c; border: 1px solid #7a6336; color: #f0d6a8; }
QPushButton#warnBtn:hover { background: #6d5836; border: 1px solid %(ACCENT)s; }
QCheckBox { spacing: 7px; }
QCheckBox::indicator { width: 15px; height: 15px; border-radius: 4px;
    border: 1px solid #555; background: %(BG_INPUT)s; }
QCheckBox::indicator:checked { background: %(ACCENT)s; border-color: %(ACCENT)s; }
QProgressBar { border: 1px solid #3d3d3d; border-radius: 4px; text-align: center;
    background: %(BG_LOG)s; color: #ffffff; }
QProgressBar::chunk { background: %(ACCENT)s; border-radius: 3px; }
QTreeWidget, QListWidget { alternate-background-color: #272727; }
QTreeWidget::item, QListWidget::item { padding: 2px 0; }
QScrollBar:vertical { background: %(BG)s; width: 11px; margin: 0; }
QScrollBar::handle:vertical { background: #484848; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: %(ACCENT)s; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QFrame#statusBar { background: %(BG_INPUT)s; border: 1px solid #3a3a3a; border-radius: 5px; }
QToolTip { background: %(BG_LOG)s; color: %(TEXT)s; border: 1px solid %(ACCENT)s; padding: 4px; }
""" % {
    "TEXT": TEXT, "TEXT_DIM": TEXT_DIM, "BG": BG, "BG_CARD": BG_CARD,
    "BG_INPUT": BG_INPUT, "BG_LOG": BG_LOG, "ACCENT": ACCENT,
    "ACTION": ACTION, "ACTION_HI": ACTION_HI,
}

#: Monospace console styling for log views (apply per log widget).
LOG_STYLE = (
    "QTextEdit, QPlainTextEdit {"
    " background: " + BG_LOG + "; color: #dfdfdf;"
    " font-family: 'Consolas','Courier New',monospace; font-size: 11px;"
    " border: 1px solid #3a3a3a; border-radius: 5px; }"
)


def apply(widget: "QtWidgets.QWidget") -> None:
    """Apply the shared pipeline stylesheet to *widget* (and its children)."""
    widget.setStyleSheet(STYLE)


# ---------------------------------------------------------------------------
# Shared drag-and-drop folder/file field
# ---------------------------------------------------------------------------

class DropLineEdit(QtWidgets.QLineEdit):
    """A ``QLineEdit`` that accepts a dropped folder (or file) and self-fills.

    Args:
        accept_files: If ``True`` a dropped *file* is accepted too; otherwise
                      only directories are.
    """

    def __init__(self, accept_files: bool = False,
                 parent: Optional["QtWidgets.QWidget"] = None) -> None:
        super().__init__(parent)
        self._accept_files = accept_files
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: "QtGui.QDragEnterEvent") -> None:  # noqa: N802
        """Accept the drag only if it carries an acceptable local path."""
        if self._first_path(event.mimeData()) is not None:
            self.setProperty("dropActive", True)
            self._restyle()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: "QtCore.QEvent") -> None:  # noqa: N802
        """Clear the drop-hover styling."""
        self.setProperty("dropActive", False)
        self._restyle()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: "QtGui.QDropEvent") -> None:  # noqa: N802
        """Fill the field with the dropped path."""
        path = self._first_path(event.mimeData())
        self.setProperty("dropActive", False)
        self._restyle()
        if path:
            self.setText(path)
            event.acceptProposedAction()

    def _first_path(self, mime: "QtCore.QMimeData") -> Optional[str]:
        """Return the first acceptable dropped local path, or ``None``."""
        if not mime.hasUrls():
            return None
        for url in mime.urls():
            if url.isLocalFile():
                p = url.toLocalFile()
                if os.path.isdir(p) or (self._accept_files and os.path.isfile(p)):
                    return p
        return None

    def _restyle(self) -> None:
        """Re-evaluate the dynamic ``dropActive`` style property."""
        self.style().unpolish(self)
        self.style().polish(self)
