"""
lh_houdini_pipeline.tools.houdini_ai_assistant.ui.panel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Main PySide6 dockable panel UI for the Houdini AI Assistant.
Integrates with the assistant core orchestrator and routes events.
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional, Any, List

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.houdini_ai_assistant.config import AssistantConfigManager
from lh_houdini_pipeline.tools.houdini_ai_assistant.core.assistant import AIAssistant
from lh_houdini_pipeline.tools.houdini_ai_assistant.prompts.manager import PromptManager
from lh_houdini_pipeline.tools.houdini_ai_assistant.ui.chat import ChatHistoryView
from lh_houdini_pipeline.tools.houdini_ai_assistant.utils.async_utils import LLMWorker
from lh_houdini_pipeline.ui import style as _style

_log = get_logger(__name__)

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    _QT = "PySide6"
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets
    _QT = "PySide2"


class AIAssistantPanel(QtWidgets.QMainWindow):
    """The main Houdini AI Assistant panel interface."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("toolRoot")
        self.setWindowTitle("Houdini AI Assistant")
        self.setMinimumSize(450, 600)

        # Initialize configurations, prompt manager, and assistant core
        self.config_manager = AssistantConfigManager()
        self.prompt_manager = PromptManager()
        self.assistant = AIAssistant(self.config_manager)
        
        self._current_worker: Optional[LLMWorker] = None
        self._current_streaming_text = ""

        self._build_ui()
        self._load_config_to_ui()
        _style.apply(self)
        self._set_status("Ready", "info")

        # Selection polling timer (Houdini only)
        self._selection_timer = QtCore.QTimer(self)
        self._selection_timer.setInterval(1000)
        self._selection_timer.timeout.connect(self._on_selection_tick)
        self._selection_timer.start()

    def _build_ui(self) -> None:
        """Construct the top settings, tab container, input area, and status bar."""
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 1. Top Panel Configuration Zone
        layout.addLayout(self._build_top_config())

        # 2. Main Tabs (Chat / Settings / MCP)
        self._tabs = QtWidgets.QTabWidget()
        layout.addWidget(self._tabs, 1)

        # Tab A: Chat
        self._chat_tab = QtWidgets.QWidget()
        self._build_chat_tab()
        self._tabs.addTab(self._chat_tab, "Chat")

        # Tab B: Prompt Templates
        self._prompts_tab = QtWidgets.QWidget()
        self._build_prompts_tab()
        self._tabs.addTab(self._prompts_tab, "System Prompts")

        # Tab C: MCP
        self._mcp_tab = QtWidgets.QWidget()
        self._build_mcp_tab()
        self._tabs.addTab(self._mcp_tab, "MCP")

        # 3. Input & Action Panel
        layout.addLayout(self._build_input_zone())

        # 4. Status Bar
        layout.addWidget(self._build_status_bar())

    def _build_top_config(self) -> QtWidgets.QLayout:
        """Top settings zone: provider, model & mode dropdowns."""
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(6)

        # Provider Selection
        row.addWidget(QtWidgets.QLabel("Provider:"))
        self._provider_combo = QtWidgets.QComboBox()
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        row.addWidget(self._provider_combo, 1)

        # Model Selection
        row.addWidget(QtWidgets.QLabel("Model:"))
        self._model_combo = QtWidgets.QComboBox()
        self._model_combo.currentIndexChanged.connect(self._on_model_changed)
        row.addWidget(self._model_combo, 2)

        # Mode Selection
        row.addWidget(QtWidgets.QLabel("Mode:"))
        self._mode_combo = QtWidgets.QComboBox()
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        row.addWidget(self._mode_combo, 2)

        return row

    def _build_chat_tab(self) -> None:
        """Construct the main chat view inside the Chat Tab."""
        layout = QtWidgets.QVBoxLayout(self._chat_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        self._chat_history = ChatHistoryView(self)
        layout.addWidget(self._chat_history)

    def _build_prompts_tab(self) -> None:
        """Construct the prompt configuration tab."""
        layout = QtWidgets.QVBoxLayout(self._prompts_tab)
        layout.setContentsMargins(6, 6, 6, 6)

        layout.addWidget(QtWidgets.QLabel("System Instruction Prompt:"))
        self._system_prompt_edit = QtWidgets.QPlainTextEdit()
        self._system_prompt_edit.setPlainText(self.assistant.system_prompt or "")
        self._system_prompt_edit.textChanged.connect(self._on_system_prompt_changed)
        layout.addWidget(self._system_prompt_edit, 1)

    def _build_mcp_tab(self) -> None:
        """Construct the MCP configuration tab."""
        layout = QtWidgets.QVBoxLayout(self._mcp_tab)
        layout.setContentsMargins(8, 8, 8, 8)

        # Checkbox toggle
        self._mcp_cb = QtWidgets.QCheckBox("Delegate to External MCP Claude (Client Mode)")
        self._mcp_cb.stateChanged.connect(self._on_mcp_toggle)
        layout.addWidget(self._mcp_cb)

        # Server URL config
        form = QtWidgets.QFormLayout()
        form.setSpacing(6)
        self._mcp_url_edit = QtWidgets.QLineEdit()
        self._mcp_url_edit.textChanged.connect(self._on_mcp_url_changed)
        form.addRow("MCP Server URL:", self._mcp_url_edit)
        layout.addLayout(form)
        layout.addStretch()

    def _build_input_zone(self) -> QtWidgets.QLayout:
        """Construct the bottom text entry area, context checkboxes, and buttons."""
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(6)

        # Context options row
        options_row = QtWidgets.QHBoxLayout()
        options_row.setSpacing(10)
        
        self._share_context_cb = QtWidgets.QCheckBox("Share Scene Context")
        self._share_context_cb.setChecked(True)
        
        self._share_viewport_cb = QtWidgets.QCheckBox("Include Viewport Screenshot")
        self._share_viewport_cb.setChecked(False)
        
        self._context_chip = QtWidgets.QLabel("No Selection")
        self._context_chip.setStyleSheet(
            "color: #9aa0a6; background: #232323; padding: 2px 6px; "
            "border: 1px solid #3a3a3a; border-radius: 4px; font-weight: bold;"
        )
        
        options_row.addWidget(self._share_context_cb)
        options_row.addWidget(self._share_viewport_cb)
        options_row.addStretch()
        options_row.addWidget(self._context_chip)
        layout.addLayout(options_row)

        # Input row
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(6)

        self._input_edit = QtWidgets.QLineEdit()
        self._input_edit.setPlaceholderText("Ask the assistant or issue a command...")
        self._input_edit.returnPressed.connect(self._on_send)
        row.addWidget(self._input_edit, 1)

        self._send_btn = QtWidgets.QPushButton("Send")
        self._send_btn.setObjectName("primaryBtn")
        self._send_btn.clicked.connect(self._on_send)
        row.addWidget(self._send_btn)

        self._clear_btn = QtWidgets.QPushButton("Clear")
        self._clear_btn.clicked.connect(self._on_clear)
        row.addWidget(self._clear_btn)

        layout.addLayout(row)
        return layout

    def _build_status_bar(self) -> QtWidgets.QWidget:
        """Construct a lightweight status bar widget matching the style system."""
        bar = QtWidgets.QFrame()
        bar.setObjectName("statusBar")
        h = QtWidgets.QHBoxLayout(bar)
        h.setContentsMargins(8, 4, 8, 4)

        self._status_dot = QtWidgets.QLabel("●")
        self._status_text = QtWidgets.QLabel("Ready")
        
        h.addWidget(self._status_dot)
        h.addWidget(self._status_text, 1)
        return bar

    # -- Configuration loading ----------------------------------------------

    def _load_config_to_ui(self) -> None:
        """Load settings from config manager and populate the UI elements."""
        cfg = self.config_manager.config
        
        # Populate provider dropdown
        self._provider_combo.blockSignals(True)
        self._provider_combo.clear()
        providers = sorted(cfg.get("providers", {}).keys())
        self._provider_combo.addItems(providers)
        
        # Set active provider
        active_provider = self.config_manager.get_active_provider()
        idx = self._provider_combo.findText(active_provider)
        if idx >= 0:
            self._provider_combo.setCurrentIndex(idx)
        self._provider_combo.blockSignals(False)

        # Load models for active provider
        self._update_models_dropdown()

        # Populate modes
        self._mode_combo.blockSignals(True)
        self._mode_combo.clear()
        self._mode_combo.addItems(self.prompt_manager.get_modes())
        idx = self._mode_combo.findText("General")
        if idx >= 0:
            self._mode_combo.setCurrentIndex(idx)
        self._mode_combo.blockSignals(False)

        # Load MCP configs
        self._mcp_cb.setChecked(cfg.get("use_mcp", False))
        self._mcp_url_edit.setText(cfg.get("mcp_server_url", "http://localhost:8000"))

        # Setup initial prompt
        self._on_mode_changed()

    def _update_models_dropdown(self) -> None:
        """Load valid models for current provider into dropdown."""
        self._model_combo.blockSignals(True)
        self._model_combo.clear()
        
        provider = self.config_manager.get_active_provider()
        models = self.config_manager.config.get(f"providers.{provider}.models", [])
        self._model_combo.addItems(models)

        active_model = self.config_manager.get_active_model()
        idx = self._model_combo.findText(active_model)
        if idx >= 0:
            self._model_combo.setCurrentIndex(idx)
        
        self._model_combo.blockSignals(False)

    # -- Callbacks & Slots --------------------------------------------------

    def _on_selection_tick(self) -> None:
        """Updates the selection chip badge with the current node selection count."""
        try:
            import hou
            nodes = hou.selectedNodes()
            count = len(nodes)
            if count == 0:
                self._context_chip.setText("No Selection")
                self._context_chip.setStyleSheet(
                    "color: #9aa0a6; background: #232323; padding: 2px 6px; "
                    "border: 1px solid #3a3a3a; border-radius: 4px; font-weight: bold;"
                )
            else:
                self._context_chip.setText(f"Selected Nodes: {count}")
                self._context_chip.setStyleSheet(
                    "color: #ff9000; font-weight: bold; background: #232323; padding: 2px 6px; "
                    "border: 1px solid #ff9000; border-radius: 4px; font-weight: bold;"
                )
        except Exception:
            self._context_chip.setText("Standalone")
            self._context_chip.setStyleSheet(
                "color: #9aa0a6; background: #232323; padding: 2px 6px; "
                "border: 1px solid #3a3a3a; border-radius: 4px; font-weight: bold;"
            )

    def _on_provider_changed(self) -> None:
        """Fires when the active LLM provider dropdown is changed."""
        new_provider = self._provider_combo.currentText()
        self.config_manager.save({"active_provider": new_provider})
        self._update_models_dropdown()
        self._set_status(f"Switched provider to {new_provider}", "info")

    def _on_model_changed(self) -> None:
        """Fires when the active LLM model dropdown is changed."""
        provider = self.config_manager.get_active_provider()
        new_model = self._model_combo.currentText()
        self.config_manager.save({f"providers.{provider}.active_model": new_model})
        self._set_status(f"Switched model to {new_model}", "info")

    def _on_mode_changed(self) -> None:
        """Fires when the active assistant mode dropdown is changed."""
        mode = self._mode_combo.currentText()
        if not mode:
            return
        prompt = self.prompt_manager.get_prompt(mode)
        
        self._system_prompt_edit.setPlainText(prompt)
        self.assistant.system_prompt = prompt
        
        self._chat_history.clear()
        self._chat_history.append_message("system", f"Active Mode set to **{mode}**.")
        self._set_status(f"Switched mode to {mode}", "info")

    def _on_system_prompt_changed(self) -> None:
        """Sync the system prompt editor with assistant state."""
        self.assistant.system_prompt = self._system_prompt_edit.toPlainText()

    def _on_mcp_toggle(self, state: int) -> None:
        """Sync use_mcp checkbox state with config."""
        self.config_manager.save({"use_mcp": bool(state)})

    def _on_mcp_url_changed(self) -> None:
        """Sync MCP server URL config."""
        self.config_manager.save({"mcp_server_url": self._mcp_url_edit.text()})

    def _on_clear(self) -> None:
        """Clears assistant state and UI log."""
        self.assistant.clear_history()
        self._chat_history.clear()
        self._chat_history.append_message("system", f"History cleared. Active Mode: {self._mode_combo.currentText()}.")
        self._set_status("History cleared", "info")

    def _on_send(self) -> None:
        """Main send triggers; creates background QThread and posts query."""
        user_text = self._input_edit.text().strip()
        if not user_text:
            return

        # Disable input while query is running
        self._set_input_enabled(False)
        self._input_edit.clear()

        # Build formatted prompt content (with context if checked)
        formatted_content = user_text
        image_b64 = None
        
        if self._share_context_cb.isChecked():
            from lh_houdini_pipeline.tools.houdini_ai_assistant.utils.context_inspector import get_full_scene_context
            from lh_houdini_pipeline.tools.houdini_ai_assistant.core.context_formatter import format_scene_context
            
            temp_path = None
            if self._share_viewport_cb.isChecked():
                temp_path = os.path.join(tempfile.gettempdir(), "houdini_ai_viewport.png")
            
            try:
                context_data = get_full_scene_context(temp_path)
                image_b64 = context_data.get("viewport_image_b64")
                context_md = format_scene_context(context_data)
                
                # Prepend the context to the message
                formatted_content = f"{context_md}\n\n[User Question]: {user_text}"
            except Exception as e:
                _log.warning(f"Failed to extract scene context: {e}")

        # Visual update in chat list
        self._chat_history.append_message("user", formatted_content, image_b64=image_b64)

        # Add message to history (with fully formatted context content)
        self.assistant.add_message("user", formatted_content, image_b64=image_b64)

        # Build client and run worker thread
        try:
            client = self.assistant.get_client()
            self._current_streaming_text = ""
            
            # Append empty assistant bubble to receive tokens
            self._chat_history.append_message("assistant", "")
            
            # Start QThread worker
            self._current_worker = LLMWorker(
                client=client,
                messages=self.assistant.history,
                system_prompt=self.assistant.system_prompt,
                stream=True,
                parent=self
            )
            self._current_worker.started_signal.connect(self._on_worker_started)
            self._current_worker.token_received.connect(self._on_token_received)
            self._current_worker.finished.connect(self._on_worker_finished)
            self._current_worker.error.connect(self._on_worker_error)
            
            self._current_worker.start()
        except Exception as e:
            self._on_worker_error(str(e))

    def _set_input_enabled(self, enabled: bool) -> None:
        """Enable or disable text edit/buttons during queries."""
        self._input_edit.setEnabled(enabled)
        self._send_btn.setEnabled(enabled)
        self._provider_combo.setEnabled(enabled)
        self._model_combo.setEnabled(enabled)
        self._mode_combo.setEnabled(enabled)

    def _set_status(self, message: str, level: str = "info") -> None:
        """Update status bar text and color dot."""
        color = _style.STATUS_COLORS.get(level, _style.STATUS_COLORS["info"])
        self._status_dot.setStyleSheet(f"color: {color}; font-size: 13px;")
        self._status_text.setText(message)

    # -- Background Thread Slots ---------------------------------------------

    def _on_worker_started(self) -> None:
        self._set_status("Thinking...", "working")

    def _on_token_received(self, token: str) -> None:
        """Append streaming tokens to the chat display."""
        if token:
            self._current_streaming_text += token
            self._chat_history.update_last_message(self._current_streaming_text)

    def _on_worker_finished(self, full_response: str) -> None:
        """Clean up finished worker thread."""
        self.assistant.add_message("assistant", full_response)
        self._set_input_enabled(True)
        self._set_status("Done", "done")
        self._current_worker = None

    def _on_worker_error(self, err_msg: str) -> None:
        """Surface background errors to the user UI."""
        self._chat_history.append_message("assistant", f"**ERROR**: {err_msg}")
        self._set_input_enabled(True)
        self._set_status("Error", "error")
        self._current_worker = None


# -- Launch Helpers ---------------------------------------------------------

def launch(parent: Optional[object] = None) -> AIAssistantPanel:
    """Show and return the dockable panel window parented to Houdini."""
    if parent is None:
        parent = _houdini_main_window()
    
    widget = AIAssistantPanel(parent)
    widget.setWindowFlags(QtCore.Qt.Window)
    widget.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
    widget.show()
    widget.raise_()
    return widget


def _houdini_main_window() -> Optional[QtWidgets.QWidget]:
    """Helper to return Houdini's main Qt window context."""
    try:
        import hou
        return hou.qt.mainWindow()
    except Exception:
        return None
