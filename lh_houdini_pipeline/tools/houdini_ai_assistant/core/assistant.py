"""
lh_houdini_pipeline.tools.houdini_ai_assistant.core.assistant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Orchestrator class for the Houdini AI Assistant.
Manages chat session history, active modes (system prompts), and client factory invocation.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.houdini_ai_assistant.config import AssistantConfigManager
from lh_houdini_pipeline.tools.houdini_ai_assistant.core.client import LLMClient, create_client
from lh_houdini_pipeline.tools.houdini_ai_assistant.tools import get_default_tools
from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.base import AITool

_log = get_logger(__name__)


class AIAssistant:
    """Session manager that coordinates history, configurations, and LLM requests."""

    def __init__(self, config_manager: Optional[AssistantConfigManager] = None) -> None:
        self.config_manager = config_manager or AssistantConfigManager()
        self.history: List[Dict[str, str]] = []
        self.system_prompt: Optional[str] = "You are a helpful Technical Artist assistant in Houdini."
        self.tools: List[AITool] = get_default_tools()

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

    def add_assistant_tool_calls(self, text: str, tool_calls: List[Dict[str, Any]]) -> None:
        """Record an assistant turn that requested native tool calls.

        *tool_calls* is a list of ``{"id", "name", "arguments"}`` dicts (kept
        JSON-serialisable for history persistence + provider re-serialisation).
        """
        self.history.append({"role": "assistant", "content": text or "", "tool_calls": tool_calls})

    def add_tool_result(self, tool_call_id: str, name: str, content: str) -> None:
        """Record the result of a native tool call, linked by *tool_call_id*."""
        self.history.append({"role": "tool", "tool_call_id": tool_call_id,
                             "name": name, "content": content})

    def get_compiled_system_prompt(self) -> str:
        """Merge base system prompt instructions with registered tool schemas."""
        base = self.system_prompt or "You are a helpful Technical Artist assistant in Houdini."
        if not self.tools:
            return base

        tool_lines = []
        tool_lines.append("\n\n=== AGENTIC TOOL EXECUTION RULES ===")
        tool_lines.append("You have access to the following tools to inspect or modify the Houdini scene:")
        
        for t in self.tools:
            tool_lines.append(f"- Name: `{t.name}`")
            tool_lines.append(f"  Description: {t.description}")
            tool_lines.append(f"  Schema: {json.dumps(t.schema)}")
        
        tool_lines.append("\nTo call a tool, output a JSON block in markdown formatting at the end of your response:")
        tool_lines.append("```json")
        tool_lines.append("{")
        tool_lines.append('    "action": "tool_name",')
        tool_lines.append('    "arguments": {')
        tool_lines.append('        "param_name": "param_value"')
        tool_lines.append("    }")
        tool_lines.append("}")
        tool_lines.append("```")
        tool_lines.append("IMPORTANT Rules:")
        tool_lines.append("1. Never propose a tool action unless it is requested or necessary.")
        tool_lines.append("2. Output ONLY ONE json block at the end of your message if you want to execute a tool.")
        tool_lines.append("3. Once the tool executes, you will receive a new message with the output [TOOL RESULT]. Use that result to write your final response.")
        
        return base + "\n" + "\n".join(tool_lines)

    def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """Search text for a tool-call JSON block and return it if valid.

        Matches code blocks: ```json ... ``` or ```tool ... ```
        """
        # Find JSON blocks
        match = re.search(r"```(?:json|tool)?\s*(\{\s*\"action\".*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
        if not match:
            # Fallback check for raw JSON mapping if brackets match
            match = re.search(r"(\{\s*\"action\"\s*:\s*\"[^\"]+\"\s*,\s*\"arguments\".*?\})", text, re.DOTALL)
            
        if match:
            try:
                data = json.loads(match.group(1).strip())
                if isinstance(data, dict) and "action" in data and "arguments" in data:
                    return data
            except Exception as e:
                _log.debug(f"Failed to parse potential tool JSON: {e}")
        return None

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
