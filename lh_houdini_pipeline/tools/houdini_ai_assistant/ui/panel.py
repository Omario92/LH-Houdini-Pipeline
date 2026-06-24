"""
lh_houdini_pipeline.tools.houdini_ai_assistant.ui.panel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Main PySide6 dockable panel UI for the Houdini AI Assistant.
Integrates with the assistant core orchestrator, routes events,
handles approval gates, and runs the agent loop.
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict, List, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.houdini_ai_assistant.config import AssistantConfigManager
from lh_houdini_pipeline.tools.houdini_ai_assistant.core.assistant import AIAssistant
from lh_houdini_pipeline.tools.houdini_ai_assistant.prompts.manager import PromptManager
from lh_houdini_pipeline.tools.houdini_ai_assistant.ui.approval import request_approval
from lh_houdini_pipeline.tools.houdini_ai_assistant.ui.chat import ChatHistoryView
from lh_houdini_pipeline.tools.houdini_ai_assistant.utils.async_utils import LLMWorker
from lh_houdini_pipeline.tools.houdini_ai_assistant.mcp.server import McpTcpServer
from lh_houdini_pipeline.tools.houdini_ai_assistant.mcp.client import McpClient, DelegatedMcpTool
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
        
        # Initialize internal MCP TCP Server
        self._mcp_server = McpTcpServer(self)
        self._mcp_server.use_thread_dispatch = True
        self._mcp_server.status_changed.connect(self._on_mcp_server_status_changed)
        self._mcp_server.approval_callback = self._on_mcp_server_approval
        
        self._current_worker: Optional[LLMWorker] = None
        self._current_streaming_text = ""
        self._agent_steps = 0  # Tool loop safety counter
        self._stopped = False  # set True when the artist hits Stop
        self._last_tool_sig = None  # detect a model repeating the same action

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
        layout.addLayout(self._build_api_key_row())

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

    def _build_api_key_row(self) -> QtWidgets.QLayout:
        """API key entry for the active provider (masked, saved locally)."""
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(QtWidgets.QLabel("API Key:"))

        self._api_key_edit = QtWidgets.QLineEdit()
        self._api_key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self._api_key_edit.setPlaceholderText("Paste the provider API key, or set its environment variable")
        self._api_key_edit.returnPressed.connect(self._on_save_api_key)
        row.addWidget(self._api_key_edit, 1)

        self._show_key_cb = QtWidgets.QCheckBox("Show")
        self._show_key_cb.toggled.connect(self._on_toggle_key_visibility)
        row.addWidget(self._show_key_cb)

        self._save_key_btn = QtWidgets.QPushButton("Save Key")
        self._save_key_btn.clicked.connect(self._on_save_api_key)
        row.addWidget(self._save_key_btn)
        return row

    def _on_toggle_key_visibility(self, show: bool) -> None:
        mode = QtWidgets.QLineEdit.Normal if show else QtWidgets.QLineEdit.Password
        self._api_key_edit.setEchoMode(mode)

    def _load_api_key_field(self) -> None:
        """Show the stored key for the active provider (or hint at its env var)."""
        provider = self.config_manager.get_active_provider()
        p_cfg = self.config_manager.config.get(f"providers.{provider}", {}) or {}
        stored = p_cfg.get("api_key", "")
        env_var = p_cfg.get("api_key_env", "")

        self._api_key_edit.blockSignals(True)
        self._api_key_edit.setText(stored)
        self._api_key_edit.blockSignals(False)

        if not stored and env_var and os.environ.get(env_var):
            self._api_key_edit.setPlaceholderText(f"(using ${env_var} from environment)")
        elif env_var:
            self._api_key_edit.setPlaceholderText(f"Paste key for {provider}, or set ${env_var}")
        else:
            self._api_key_edit.setPlaceholderText(f"Paste API key for {provider}")

    def _on_save_api_key(self) -> None:
        """Persist the entered key under the active provider (nested write)."""
        provider = self.config_manager.get_active_provider()
        key = self._api_key_edit.text().strip()
        # Nested dict so the deep-merge targets providers.<provider>.api_key
        # without clobbering sibling fields (and so get() can read it back).
        self.config_manager.save({"providers": {provider: {"api_key": key}}})
        masked = "set" if key else "cleared"
        self._set_status(f"API key {masked} for {provider}", "done")

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
        """Construct the MCP configuration tab with client and server controls."""
        layout = QtWidgets.QVBoxLayout(self._mcp_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Group 1: MCP Client settings
        client_group = QtWidgets.QGroupBox("MCP Client Settings (Tool Delegation)")
        client_layout = QtWidgets.QVBoxLayout(client_group)
        client_layout.setSpacing(8)

        self._mcp_cb = QtWidgets.QCheckBox("Enable Client Delegation")
        self._mcp_cb.stateChanged.connect(self._on_mcp_toggle)
        client_layout.addWidget(self._mcp_cb)

        form_client = QtWidgets.QFormLayout()
        form_client.setSpacing(6)
        self._mcp_url_edit = QtWidgets.QLineEdit()
        self._mcp_url_edit.setPlaceholderText("tcp://127.0.0.1:14848 or http://localhost:8000")
        self._mcp_url_edit.textChanged.connect(self._on_mcp_url_changed)
        form_client.addRow("External Server URL:", self._mcp_url_edit)
        client_layout.addLayout(form_client)

        self._mcp_connect_btn = QtWidgets.QPushButton("Connect & Load External Tools")
        self._mcp_connect_btn.clicked.connect(self.update_mcp_tools)
        client_layout.addWidget(self._mcp_connect_btn)

        layout.addWidget(client_group)

        # Group 2: Host Internal MCP TCP Server
        server_group = QtWidgets.QGroupBox("Host Internal Houdini MCP TCP Server")
        server_layout = QtWidgets.QVBoxLayout(server_group)
        server_layout.setSpacing(8)

        self._mcp_server_cb = QtWidgets.QCheckBox("Start MCP TCP Server")
        self._mcp_server_cb.stateChanged.connect(self._on_mcp_server_toggle)
        server_layout.addWidget(self._mcp_server_cb)

        form_server = QtWidgets.QFormLayout()
        form_server.setSpacing(6)
        self._mcp_port_edit = QtWidgets.QLineEdit()
        self._mcp_port_edit.setText("14848")
        self._mcp_port_edit.textChanged.connect(self._on_mcp_port_changed)
        form_server.addRow("TCP Listen Port:", self._mcp_port_edit)
        
        self._mcp_server_status_lbl = QtWidgets.QLabel("Status: Stopped")
        self._mcp_server_status_lbl.setStyleSheet("color: #9aa0a6; font-style: italic;")
        form_server.addRow("Server Status:", self._mcp_server_status_lbl)
        server_layout.addLayout(form_server)

        layout.addWidget(server_group)
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

        self._native_tools_cb = QtWidgets.QCheckBox("Native tools")
        self._native_tools_cb.setChecked(True)
        self._native_tools_cb.setToolTip(
            "Use the provider's native function-calling API (recommended).\n"
            "Uncheck to fall back to the legacy JSON-in-text tool protocol."
        )
        self._native_tools_cb.toggled.connect(self._on_native_tools_toggled)

        self._max_steps_spin = QtWidgets.QSpinBox()
        self._max_steps_spin.setRange(1, 50)
        self._max_steps_spin.setValue(12)
        self._max_steps_spin.setToolTip(
            "Max consecutive tool calls the agent may chain before stopping.\n"
            "Raise this for multi-step builds; lower it to keep the model on a leash."
        )
        self._max_steps_spin.valueChanged.connect(self._on_max_steps_changed)

        self._context_chip = QtWidgets.QLabel("No Selection")
        self._context_chip.setStyleSheet(
            "color: #9aa0a6; background: #232323; padding: 2px 6px; "
            "border: 1px solid #3a3a3a; border-radius: 4px; font-weight: bold;"
        )
        
        options_row.addWidget(self._share_context_cb)
        options_row.addWidget(self._share_viewport_cb)
        options_row.addWidget(self._native_tools_cb)
        options_row.addWidget(QtWidgets.QLabel("Max tool steps:"))
        options_row.addWidget(self._max_steps_spin)
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

        self._stop_btn = QtWidgets.QPushButton("Stop")
        self._stop_btn.setObjectName("warnBtn")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop)
        row.addWidget(self._stop_btn)

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
        self._mcp_url_edit.setText(cfg.get("mcp_server_url", "tcp://127.0.0.1:14848"))
        self._mcp_port_edit.setText(str(cfg.get("mcp_server_port", 14848)))
        self._mcp_server_cb.setChecked(cfg.get("use_mcp_server", False))

        # Setup initial prompt
        self._on_mode_changed()

        # Native function-calling toggle
        self._native_tools_cb.blockSignals(True)
        self._native_tools_cb.setChecked(bool(self.config_manager.config.get("native_tools", True)))
        self._native_tools_cb.blockSignals(False)

        # Agent step cap
        self._max_steps_spin.blockSignals(True)
        self._max_steps_spin.setValue(int(self.config_manager.config.get("max_agent_steps", 12)))
        self._max_steps_spin.blockSignals(False)

        # Show the active provider's API key
        self._load_api_key_field()

        # Initialize MCP client tools if active
        if self._mcp_cb.isChecked():
            self.update_mcp_tools()

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
                    f"color: {_style.TEXT_DIM}; background: {_style.BG_INPUT}; padding: 2px 6px; "
                    "border: 1px solid #3a3a3a; border-radius: 4px; font-weight: bold;"
                )
            else:
                self._context_chip.setText(f"Selected Nodes: {count}")
                self._context_chip.setStyleSheet(
                    f"color: {_style.ACCENT}; font-weight: bold; background: {_style.BG_INPUT}; padding: 2px 6px; "
                    f"border: 1px solid {_style.ACCENT}; border-radius: 4px; font-weight: bold;"
                )
        except Exception:
            self._context_chip.setText("Standalone")
            self._context_chip.setStyleSheet(
                f"color: {_style.TEXT_DIM}; background: {_style.BG_INPUT}; padding: 2px 6px; "
                "border: 1px solid #3a3a3a; border-radius: 4px; font-weight: bold;"
            )

    def _on_provider_changed(self) -> None:
        """Fires when the active LLM provider dropdown is changed."""
        new_provider = self._provider_combo.currentText()
        self.config_manager.save({"active_provider": new_provider})
        self._update_models_dropdown()
        self._load_api_key_field()
        self._set_status(f"Switched provider to {new_provider}", "info")

    def _on_model_changed(self) -> None:
        """Fires when the active LLM model dropdown is changed."""
        provider = self.config_manager.get_active_provider()
        new_model = self._model_combo.currentText()
        # Nested write so the dotted path persists and reads back via get().
        self.config_manager.save({"providers": {provider: {"active_model": new_model}}})
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

    def _on_max_steps_changed(self, value: int) -> None:
        """Persist the agent step cap."""
        self.config_manager.save({"max_agent_steps": int(value)})

    def _on_native_tools_toggled(self, on: bool) -> None:
        """Persist the native function-calling preference."""
        self.config_manager.save({"native_tools": bool(on)})

    def _on_system_prompt_changed(self) -> None:
        """Sync the system prompt editor with assistant state."""
        self.assistant.system_prompt = self._system_prompt_edit.toPlainText()

    def _on_mcp_toggle(self, state: int) -> None:
        """Sync use_mcp checkbox state with config and reload tools."""
        self.config_manager.save({"use_mcp": bool(state)})
        self.update_mcp_tools()

    def _on_mcp_url_changed(self) -> None:
        """Sync MCP server URL config."""
        self.config_manager.save({"mcp_server_url": self._mcp_url_edit.text()})

    def _on_mcp_server_toggle(self, state: int) -> None:
        """Start or stop the internal TCP server based on checkbox state."""
        self.config_manager.save({"use_mcp_server": bool(state)})
        if state:
            try:
                port = int(self._mcp_port_edit.text().strip())
            except ValueError:
                port = 14848
                self._mcp_port_edit.setText(str(port))
            
            self._mcp_server.start(port=port)
        else:
            self._mcp_server.stop()

    def _on_mcp_port_changed(self) -> None:
        """Save new port string to config."""
        try:
            port = int(self._mcp_port_edit.text().strip())
            self.config_manager.save({"mcp_server_port": port})
        except ValueError:
            pass

    def _on_mcp_server_status_changed(self, status: str) -> None:
        """Update server status display."""
        self._mcp_server_status_lbl.setText(f"Status: {status}")
        if "Running" in status:
            self._mcp_server_status_lbl.setStyleSheet(f"color: {_style.OK}; font-weight: bold;")
        elif "Error" in status:
            self._mcp_server_status_lbl.setStyleSheet(f"color: {_style.ERROR}; font-weight: bold;")
        else:
            self._mcp_server_status_lbl.setStyleSheet(f"color: {_style.TEXT_DIM}; font-style: italic;")

    def _on_mcp_server_approval(self, action: str, arguments: Dict[str, Any]) -> bool:
        """Main thread callback to gate modifying actions from external socket requests."""
        self._chat_history.append_message(
            "system", f"ℹ️ External TCP Client requested tool **{action}**."
        )
        approved = request_approval(action, arguments, parent=self)
        if approved:
            self._chat_history.append_message("system", f"Artist approved external tool **{action}**.")
        else:
            self._chat_history.append_message("system", f"Artist rejected external tool **{action}**.")
        return approved

    def update_mcp_tools(self) -> None:
        """Query the external MCP server and register delegated tools if client mode is active."""
        # 1. Reset to standard default tools
        from lh_houdini_pipeline.tools.houdini_ai_assistant.tools import get_default_tools
        self.assistant.tools = get_default_tools()

        if not self._mcp_cb.isChecked():
            self._mcp_connect_btn.setEnabled(False)
            self._set_status("MCP Client disabled", "info")
            return

        self._mcp_connect_btn.setEnabled(True)
        url = self._mcp_url_edit.text().strip()
        if not url:
            self._set_status("MCP Client URL empty", "warn")
            return

        self._set_status("Connecting to MCP...", "working")
        
        # Connect to client dynamically
        client = McpClient(url)
        if client.connect():
            ext_tools = client.list_tools()
            loaded_count = 0
            for tool_data in ext_tools:
                name = tool_data.get("name")
                if not name:
                    continue
                # Avoid shadowing built-in tools of same name
                if any(t.name == name for t in self.assistant.tools):
                    continue
                
                wrapped_tool = DelegatedMcpTool(
                    name=name,
                    description=tool_data.get("description", ""),
                    schema=tool_data.get("inputSchema", {}),
                    client=client
                )
                self.assistant.tools.append(wrapped_tool)
                loaded_count += 1
            
            self._chat_history.append_message(
                "system", f"Connected to external MCP server. Loaded {loaded_count} delegated tools."
            )
            self._set_status("MCP Connected", "done")
        else:
            self._chat_history.append_message(
                "system", f"⚠️ Warning: Failed to connect to external MCP server at '{url}'."
            )
            self._set_status("MCP Connection Error", "error")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Clean up background TCP servers on exit to avoid orphaned ports."""
        if hasattr(self, "_mcp_server"):
            self._mcp_server.stop()
        super().closeEvent(event)

    def _on_clear(self) -> None:
        """Clears assistant state and UI log."""
        self.assistant.clear_history()
        self._chat_history.clear()
        self._chat_history.append_message("system", f"History cleared. Active Mode: {self._mode_combo.currentText()}.")
        self._set_status("History cleared", "info")

    def _on_send(self) -> None:
        """Main send triggers; compiles context and starts the agent steps."""
        user_text = self._input_edit.text().strip()
        if not user_text:
            return

        self._input_edit.clear()
        self._agent_steps = 0  # Reset tool loops
        self._stopped = False
        self._last_tool_sig = None

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

        # Add message to history (with fully formatted context content)
        self.assistant.add_message("user", formatted_content, image_b64=image_b64)

        # Visual update in chat list (we append user_text, not the massive context payload)
        self._chat_history.append_message("user", user_text, image_b64=image_b64)

        # Trigger background processing step
        self._run_assistant_step()

    def _run_assistant_step(self) -> None:
        """Query the LLM client with active message history asynchronously."""
        if self._stopped:
            return
        # Loop safety guard (configurable; raise 'Max tool steps' for big builds)
        limit = max(1, int(self._max_steps_spin.value()))
        if self._agent_steps >= limit:
            self._chat_history.append_message(
                "system",
                f"⚠️ Safety halt: reached the max of {limit} consecutive tool calls. "
                "Type 'continue' to keep going, or raise 'Max tool steps' for longer "
                "multi-step builds."
            )
            self._set_running(False)
            self._set_status("Halted", "warn")
            return

        self._agent_steps += 1
        self._set_running(True)

        use_native = (self._native_tools_cb.isChecked() and bool(self.assistant.tools))

        try:
            client = self.assistant.get_client()
            self._current_streaming_text = ""

            if use_native:
                # Native function-calling: structured, non-streaming turn.
                self._current_worker = LLMWorker(
                    client=client,
                    messages=self.assistant.history,
                    system_prompt=self.assistant.system_prompt,
                    stream=False,
                    parent=self,
                    tools=self.assistant.tools,
                    agentic=True,
                )
                self._current_worker.started_signal.connect(self._on_worker_started)
                self._current_worker.agent_finished.connect(self._on_agent_finished)
                self._current_worker.error.connect(self._on_worker_error)
                self._current_worker.agent_finished.connect(self._current_worker.deleteLater)
                self._current_worker.error.connect(self._current_worker.deleteLater)
                self._current_worker.start()
                return

            # Legacy streaming + JSON-in-text protocol (fallback).
            self._chat_history.append_message("assistant", "")
            compiled_system_prompt = self.assistant.get_compiled_system_prompt()
            self._current_worker = LLMWorker(
                client=client,
                messages=self.assistant.history,
                system_prompt=compiled_system_prompt,
                stream=True,
                parent=self
            )
            self._current_worker.started_signal.connect(self._on_worker_started)
            self._current_worker.token_received.connect(self._on_token_received)
            self._current_worker.finished.connect(self._on_worker_finished)
            self._current_worker.error.connect(self._on_worker_error)
            self._current_worker.finished.connect(self._current_worker.deleteLater)
            self._current_worker.error.connect(self._current_worker.deleteLater)
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

    def _set_running(self, running: bool) -> None:
        """Toggle UI between 'request in flight' and 'idle'.

        While running, inputs/Send are disabled and Stop is enabled, so the
        artist can always abort a stuck model and then switch model or resend.
        """
        self._set_input_enabled(not running)
        self._stop_btn.setEnabled(running)

    def _on_stop(self) -> None:
        """Abort the in-flight request and hand control back to the artist."""
        worker = self._current_worker
        if worker is None:
            self._set_running(False)
            return
        self._stopped = True
        self._agent_steps = 999  # guarantee the agent loop will not continue
        try:
            worker.cancel()  # closes the socket -> unblocks a stuck stream
        except Exception as e:  # noqa: BLE001
            _log.debug(f"worker.cancel() failed: {e}")
        if not self._current_streaming_text:
            self._chat_history.update_last_message("_(stopped — no response)_")
        self._current_worker = None
        self._set_running(False)
        self._set_status("Stopped by user", "warn")

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
        """Main thread callback when LLM query is fully completed. Parses tool calls."""
        if self._stopped:
            self._set_running(False)
            self._current_worker = None
            return
        # 1. Commit response to active session history
        self.assistant.add_message("assistant", full_response)
        
        # 2. Check for proposed tool calls
        tool_call = self.assistant.parse_tool_call(full_response)
        
        if tool_call:
            action = tool_call["action"]
            args = tool_call["arguments"]
            
            # Find matching tool
            tool = next((t for t in self.assistant.tools if t.name == action), None)
            
            if tool:
                # Loop guard: if the model proposes the EXACT same call it just
                # made, it is stuck retrying -- stop instead of burning steps.
                sig = (action, json.dumps(args, sort_keys=True, default=str))
                if sig == self._last_tool_sig:
                    self._chat_history.append_message(
                        "system",
                        f"⚠️ Stopped: the model repeated the same '{action}' call. "
                        "Rephrase your request or adjust the parameters."
                    )
                    self._set_running(False)
                    self._set_status("Halted (repeat)", "warn")
                    self._current_worker = None
                    return
                self._last_tool_sig = sig

                # 3. Query User Approval (modal dialog on main thread)
                self._set_status("Awaiting Approval...", "working")
                approved = request_approval(action, args, self)
                
                if approved:
                    self._chat_history.append_message("system", f"Artist approved action **{action}**.")
                    self._set_status("Executing...", "working")
                    
                    try:
                        # 4. Execute tool logic (safe on main thread)
                        res = tool.execute(args)
                        res_str = json.dumps(res, indent=2) if isinstance(res, dict) else str(res)
                        
                        # Add feedback message to history
                        self.assistant.add_message("user", f"[TOOL RESULT]: {res_str}")
                        self._chat_history.append_message("system", f"Tool **{action}** executed successfully.")
                        
                        # 5. Continue loop asynchronously
                        QtCore.QTimer.singleShot(100, self._run_assistant_step)
                        return
                    except Exception as ex:
                        err_msg = f"Failed to execute tool: {ex}"
                        self._chat_history.append_message("system", f"**ERROR**: {err_msg}")
                        self.assistant.add_message("user", f"[TOOL ERROR]: {err_msg}")
                        QtCore.QTimer.singleShot(100, self._run_assistant_step)
                        return
                else:
                    # Rejected by user
                    self._chat_history.append_message("system", f"Artist rejected action **{action}**.")
                    self.assistant.add_message("user", f"[TOOL RESULT]: Action '{action}' was rejected by the artist.")
                    QtCore.QTimer.singleShot(100, self._run_assistant_step)
                    return
            else:
                # Tool not found
                err_msg = f"Tool '{action}' is not registered in this pipeline."
                self._chat_history.append_message("system", f"**ERROR**: {err_msg}")
                self.assistant.add_message("user", f"[TOOL ERROR]: {err_msg}")
                QtCore.QTimer.singleShot(100, self._run_assistant_step)
                return
        
        # No tool calls proposed; loop finishes. Re-enable input fields.
        self._set_running(False)
        self._set_status("Done", "done")
        self._current_worker = None

    # Read-only tools execute without an approval prompt; everything else
    # (scene/disk-modifying or unknown delegated tools) must be approved.
    _READ_ONLY_TOOLS = {"get_scene_context"}

    def _on_agent_finished(self, resp: object) -> None:
        """Native function-calling result: run any tool calls, then loop."""
        if self._stopped:
            self._set_running(False)
            self._current_worker = None
            return

        text = (getattr(resp, "text", "") or "")
        tool_calls = list(getattr(resp, "tool_calls", []) or [])

        # No tool calls -> final answer.
        if not tool_calls:
            self.assistant.add_message("assistant", text)
            self._chat_history.append_message("assistant", text if text.strip() else "_(no content)_")
            self._set_running(False)
            self._set_status("Done", "done")
            self._current_worker = None
            return

        # Record the assistant tool-call turn so the next request has context.
        tc_dicts = [{"id": tc.id, "name": tc.name, "arguments": tc.arguments} for tc in tool_calls]
        self.assistant.add_assistant_tool_calls(text, tc_dicts)
        if text.strip():
            self._chat_history.append_message("assistant", text)

        # Repeat guard (first call signature).
        first = tool_calls[0]
        sig = (first.name, json.dumps(first.arguments, sort_keys=True, default=str))
        if sig == self._last_tool_sig:
            self._chat_history.append_message(
                "system",
                f"⚠️ Stopped: the model repeated the same '{first.name}' call. "
                "Rephrase your request or adjust the parameters."
            )
            self._set_running(False)
            self._set_status("Halted (repeat)", "warn")
            self._current_worker = None
            return
        self._last_tool_sig = sig

        # Execute each requested tool call, gating modifying ones behind approval.
        for tc in tool_calls:
            tool = next((t for t in self.assistant.tools if t.name == tc.name), None)
            if tool is None:
                self.assistant.add_tool_result(tc.id, tc.name, f"ERROR: tool '{tc.name}' is not registered.")
                self._chat_history.append_message("system", f"**ERROR**: tool '{tc.name}' not found.")
                continue

            if tc.name not in self._READ_ONLY_TOOLS:
                self._set_status("Awaiting Approval...", "working")
                if not request_approval(tc.name, tc.arguments, self):
                    self.assistant.add_tool_result(tc.id, tc.name, "Action was rejected by the artist.")
                    self._chat_history.append_message("system", f"Artist rejected action **{tc.name}**.")
                    continue

            self._set_status("Executing...", "working")
            try:
                res = tool.execute(tc.arguments)
                res_str = json.dumps(res, indent=2, default=str) if isinstance(res, dict) else str(res)
                self.assistant.add_tool_result(tc.id, tc.name, res_str)
                self._chat_history.append_message("system", f"Tool **{tc.name}** executed.")
            except Exception as ex:  # noqa: BLE001
                self.assistant.add_tool_result(tc.id, tc.name, f"ERROR: {ex}")
                self._chat_history.append_message("system", f"**ERROR** running {tc.name}: {ex}")

        self._current_worker = None
        # Loop: let the model read the tool results and continue.
        QtCore.QTimer.singleShot(100, self._run_assistant_step)

    def _on_worker_error(self, err_msg: str) -> None:
        """Surface background errors to the user UI."""
        if self._stopped:
            self._set_running(False)
            self._current_worker = None
            return
        self._chat_history.append_message("assistant", f"**ERROR**: {err_msg}")
        self._set_running(False)
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
