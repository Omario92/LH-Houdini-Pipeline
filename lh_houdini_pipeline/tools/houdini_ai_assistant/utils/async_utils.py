"""
lh_houdini_pipeline.tools.houdini_ai_assistant.utils.async_utils
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Qt Thread workers to call LLM APIs asynchronously.
Prevents Houdini's main application thread from locking up during network requests.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.houdini_ai_assistant.core.client import LLMClient

_log = get_logger(__name__)

try:
    from PySide6 import QtCore
    _QT_SIGNAL = QtCore.Signal
except ImportError:
    from PySide2 import QtCore
    _QT_SIGNAL = QtCore.Signal  # PySide2 also uses QtCore.Signal


class LLMWorker(QtCore.QThread):
    """QThread worker that calls an LLM client in the background and emits signals."""

    # Define signals compatible with both PySide6 and PySide2
    started_signal = _QT_SIGNAL()
    token_received = _QT_SIGNAL(str)
    finished = _QT_SIGNAL(str)
    error = _QT_SIGNAL(str)

    def __init__(
        self,
        client: LLMClient,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        stream: bool = True,
        parent: Optional[QtCore.QObject] = None
    ) -> None:
        super().__init__(parent)
        self.client = client
        self.messages = messages
        self.system_prompt = system_prompt
        self.stream = stream
        self._is_cancelled = False

    def cancel(self) -> None:
        """Request the worker to stop processing early."""
        self._is_cancelled = True
        self.requestInterruption()

    def run(self) -> None:
        """Execute the LLM query on the background thread."""
        self.started_signal.emit()
        try:
            if self.stream:
                full_text: List[str] = []
                for chunk in self.client.chat_stream(self.messages, self.system_prompt):
                    if self._is_cancelled or self.isInterruptionRequested():
                        _log.info("LLMWorker request was interrupted/cancelled.")
                        break
                    
                    if chunk:
                        full_text.append(chunk)
                        self.token_received.emit(chunk)
                
                self.finished.emit("".join(full_text))
            else:
                response = self.client.chat(self.messages, self.system_prompt)
                if not (self._is_cancelled or self.isInterruptionRequested()):
                    self.finished.emit(response)
        except Exception as e:
            _log.error(f"LLMWorker background error: {e}")
            self.error.emit(str(e))
