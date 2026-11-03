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

    @property
    def read_only(self) -> bool:
        """Whether the tool only inspects state and never modifies scene or disk.

        Approval gating is FAIL-CLOSED: the default is ``False``, so every tool
        (including new or delegated ones) needs artist approval unless it
        explicitly opts in as read-only by overriding this property.

        Returns:
            ``True`` only for tools that are safe to run without approval.
        """
        return False

    @abstractmethod
    def execute(self, arguments: Dict[str, Any]) -> Any:
        """Execute the tool logic with the provided arguments.

        Args:
            arguments: Dictionary containing parameters mapped to schema.

        Returns:
            The execution result (typically a string or serializable structure).
        """
        pass


def requires_approval(tool: AITool) -> bool:
    """Return whether *tool* must be approved by the artist before running.

    Single source of truth shared by the chat panel and the MCP TCP server, so
    both entry points gate the same set of tools.

    Args:
        tool: The tool about to be executed.

    Returns:
        ``True`` unless the tool declares itself read-only.
    """
    return not bool(getattr(tool, "read_only", False))
