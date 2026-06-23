"""
lh_houdini_pipeline.tools.houdini_ai_assistant.tools.base
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Abstract base class and registry for tools exposed to the LLM agent.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class AITool(ABC):
    """Abstract base class for all AI Assistant tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The tool name as recognized by the model's function calling API."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A detailed description explaining what the tool does and when to call it."""
        pass

    @property
    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        """The JSON Schema parameter description for the tool (OpenAPI/MCP compatible)."""
        pass

    @abstractmethod
    def execute(self, arguments: Dict[str, Any]) -> Any:
        """Execute the tool logic with the provided arguments.

        Args:
            arguments: Dictionary containing parameters mapped to schema.

        Returns:
            The execution result (typically a string or serializable structure).
        """
        pass
