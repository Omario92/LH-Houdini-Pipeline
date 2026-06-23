"""
lh_houdini_pipeline.tools.houdini_ai_assistant.core.assistant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Orchestrator class for the Houdini AI Assistant.
Manages chat session history, active modes (system prompts), and client factory invocation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.houdini_ai_assistant.config import AssistantConfigManager
from lh_houdini_pipeline.tools.houdini_ai_assistant.core.client import LLMClient, create_client

_log = get_logger(__name__)


class AIAssistant:
    """Session manager that coordinates history, configurations, and LLM requests."""

    def __init__(self, config_manager: Optional[AssistantConfigManager] = None) -> None:
        self.config_manager = config_manager or AssistantConfigManager()
        self.history: List[Dict[str, str]] = []
        self.system_prompt: Optional[str] = "You are a helpful Technical Artist assistant in Houdini."

    def clear_history(self) -> None:
        """Reset the conversation history."""
        self.history.clear()
        _log.info("Conversation history cleared.")

    def add_message(self, role: str, content: str, image_b64: Optional[str] = None) -> None:
        """Add a message to the active session history."""
        msg = {"role": role, "content": content}
        if image_b64:
            msg["image_b64"] = image_b64
        self.history.append(msg)


    def get_client(self) -> LLMClient:
        """Create and return the active LLMClient instance based on current settings."""
        cfg_mgr = self.config_manager
        provider = cfg_mgr.get_active_provider()
        api_key = cfg_mgr.get_api_key(provider)
        url = cfg_mgr.get_active_url()
        model = cfg_mgr.get_active_model()
        temperature = cfg_mgr.config.get("temperature", 0.2)
        max_tokens = cfg_mgr.config.get("max_tokens", 4096)

        return create_client(
            provider=provider,
            api_key=api_key,
            url=url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
