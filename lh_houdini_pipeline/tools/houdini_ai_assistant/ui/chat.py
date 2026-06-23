"""
lh_houdini_pipeline.tools.houdini_ai_assistant.ui.chat
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Interactive chat widgets including message bubbles, Markdown browser windows,
code extraction, and scroll container viewports.
"""

from __future__ import annotations

import re
from typing import Optional, Any, List

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.ui import style as _style

_log = get_logger(__name__)

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets


class ChatBubbleWidget(QtWidgets.QFrame):
    """Custom widget representing a single user or assistant message bubble."""

    def __init__(
        self,
        role: str,
        text: str,
        image_b64: Optional[str] = None,
        parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.role = role
        self.raw_text = text
        self.image_b64 = image_b64

        self._build_bubble()
        self.set_text(text)

    def _build_bubble(self) -> None:
        """Lay out headers, text browser, and copy buttons."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Style & Alignment based on role
        if self.role == "user":
            self.setObjectName("userBubble")
            self.setStyleSheet(
                f"QFrame#userBubble {{ background-color: #2d3f56; border: 1px solid {_style.ACTION}; border-radius: 8px; }}"
            )
            # Layout margins: indent from left to push right
            layout.setContentsMargins(60, 8, 10, 8)
        else:
            self.setObjectName("assistantBubble")
            self.setStyleSheet(
                f"QFrame#assistantBubble {{ background-color: {_style.BG_INPUT}; border: 1px solid #3c3c3c; border-radius: 8px; }}"
            )
            # Layout margins: indent from right to push left
            layout.setContentsMargins(10, 8, 60, 8)

        # Header Row (Sender role and badges)
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(6)

        sender_label = QtWidgets.QLabel("ARTIST" if self.role == "user" else "ASSISTANT")
        sender_label.setStyleSheet(f"font-weight: bold; color: {_style.ACCENT}; font-size: 10px; letter-spacing: 0.5px;")
        header_layout.addWidget(sender_label)

        # Optional Badge Indicators
        if self.role == "user":
            if "[User Question]" in self.raw_text or "HOUDINI SCENE CONTEXT OVERVIEW" in self.raw_text:
                context_badge = QtWidgets.QLabel("Scene Context")
                context_badge.setStyleSheet(
                    f"color: {_style.ACCENT}; background: {_style.BG_LOG}; border: 1px solid {_style.ACCENT}; "
                    "border-radius: 3px; font-size: 9px; padding: 1px 4px;"
                )
                header_layout.addWidget(context_badge)
            if self.image_b64:
                img_badge = QtWidgets.QLabel("Viewport Screenshot")
                img_badge.setStyleSheet(
                    f"color: {_style.ACTION}; background: {_style.BG_LOG}; border: 1px solid {_style.ACTION}; "
                    "border-radius: 3px; font-size: 9px; padding: 1px 4px;"
                )
                header_layout.addWidget(img_badge)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Markdown Text Browser Content (resizes to document)
        self._browser = QtWidgets.QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setFrameStyle(QtWidgets.QFrame.Shape.NoFrame)
        self._browser.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._browser.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Inherit styling
        self._browser.setStyleSheet(
            f"background: transparent; border: none; font-size: 11px; color: {_style.TEXT};"
        )
        self._browser.document().contentsChanged.connect(self._adjust_browser_height)
        layout.addWidget(self._browser)

        # Copy Action Button Row (Assistant only)
        if self.role != "user":
            self._actions_row = QtWidgets.QHBoxLayout()
            self._actions_row.setSpacing(6)
            self._actions_row.addStretch()

            self._copy_btn = QtWidgets.QPushButton("Copy Response")
            self._copy_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton))
            self._copy_btn.setStyleSheet("font-size: 9px; padding: 3px 8px; height: 18px;")
            self._copy_btn.clicked.connect(self._on_copy_full)
            self._actions_row.addWidget(self._copy_btn)

            self._copy_code_btn = QtWidgets.QPushButton("Copy Code")
            self._copy_code_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon))
            self._copy_code_btn.setStyleSheet(f"font-size: 9px; padding: 3px 8px; height: 18px; color: {_style.ACCENT};")
            self._copy_code_btn.clicked.connect(self._on_copy_code)
            self._copy_code_btn.setVisible(False)
            self._actions_row.addWidget(self._copy_code_btn)

            layout.addLayout(self._actions_row)

    def set_text(self, text: str) -> None:
        """Update the bubble text, parse markdown, and toggle action buttons."""
        self.raw_text = text
        
        # In user messages, strip the long scene context prefix so it doesn't clutter chat logs
        display_text = text
        if self.role == "user" and "[User Question]:" in text:
            # Show only user question
            parts = text.split("[User Question]:", 1)
            display_text = parts[1].strip()

        # Set rich Markdown natively in PySide6
        self._browser.setMarkdown(display_text)
        self._adjust_browser_height()

        # If assistant, show Copy Code if triple backticks are present
        if self.role != "user":
            has_code = "```" in text
            self._copy_code_btn.setVisible(has_code)

    def _adjust_browser_height(self) -> None:
        """Adjust QTextBrowser height to match its text layout size exactly (prevents inner scroll)."""
        self._browser.document().adjustSize()
        height = int(self._browser.document().size().height()) + 12
        self._browser.setFixedHeight(max(24, height))

    def _on_copy_full(self) -> None:
        """Copy the entire raw text to the clipboard."""
        QtWidgets.QApplication.clipboard().setText(self.raw_text)

    def _on_copy_code(self) -> None:
        """Extract and copy only the code blocks within the response."""
        # Find all blocks between ```...```
        blocks = re.findall(r"```(?:\w+)?\n(.*?)\n```", self.raw_text, re.DOTALL)
        if blocks:
            code = "\n\n".join(blocks).strip()
            QtWidgets.QApplication.clipboard().setText(code)


class ChatHistoryView(QtWidgets.QScrollArea):
    """Scroll container displaying message bubbles sequentially."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameStyle(QtWidgets.QFrame.Shape.NoFrame)
        self.setStyleSheet(f"background-color: {_style.BG_LOG};")

        # Scrollbar adjustments
        self.verticalScrollBar().setStyleSheet(
            f"QScrollBar:vertical {{ width: 8px; background: {_style.BG_LOG}; }}"
            f"QScrollBar::handle:vertical {{ background: #3a3a3a; border-radius: 4px; }}"
            f"QScrollBar::handle:vertical:hover {{ background: {_style.ACCENT}; }}"
        )

        # Setup inner container
        self._container = QtWidgets.QWidget()
        self._container.setObjectName("chatContainer")
        self._container.setStyleSheet(f"QWidget#chatContainer {{ background-color: {_style.BG_LOG}; }}")
        self.setWidget(self._container)

        self._layout = QtWidgets.QVBoxLayout(self._container)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(12)
        
        # Bottom spacer to push bubbles up
        self._layout.addStretch(1)

        self._bubbles: List[ChatBubbleWidget] = []

    def append_message(self, role: str, text: str, image_b64: Optional[str] = None) -> ChatBubbleWidget:
        """Instantiate a ChatBubbleWidget and append to the bottom of layout."""
        bubble = ChatBubbleWidget(role, text, image_b64, self)
        
        # Insert before stretch
        self._layout.insertWidget(self._layout.count() - 1, bubble)
        self._bubbles.append(bubble)
        
        self.scroll_to_bottom()
        return bubble

    def update_last_message(self, text: str) -> None:
        """Update the text of the most recent message (used for streaming)."""
        if self._bubbles:
            # Find the last message that is from assistant
            for bubble in reversed(self._bubbles):
                if bubble.role == "assistant":
                    bubble.set_text(text)
                    self.scroll_to_bottom()
                    break

    def clear(self) -> None:
        """Clear all message bubble widgets from layout."""
        for bubble in self._bubbles:
            self._layout.removeWidget(bubble)
            bubble.deleteLater()
        self._bubbles.clear()

    def scroll_to_bottom(self) -> None:
        """Safely scroll to maximum vertical offset (with small delay for layout calculations)."""
        QtCore.QTimer.singleShot(30, self._do_scroll)

    def _do_scroll(self) -> None:
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
