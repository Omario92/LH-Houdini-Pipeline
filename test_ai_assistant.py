"""
Unit tests for the Houdini AI Assistant core and client layers.
Run from the project root:

    python test_ai_assistant.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add workspace root to python path
sys.path.insert(0, os.path.dirname(__file__))

from lh_houdini_pipeline.tools.houdini_ai_assistant.config import AssistantConfigManager
from lh_houdini_pipeline.tools.houdini_ai_assistant.core.assistant import AIAssistant
from lh_houdini_pipeline.tools.houdini_ai_assistant.core.client import (
    LLMError,
    create_client,
    AnthropicClient,
    OpenAIClient,
    GeminiClient,
)

PASS = "\033[32mOK\033[0m"
FAIL = "\033[31mFAIL\033[0m"
errors = []


def check(label: str, fn: callable) -> None:
    try:
        fn()
        print("  " + label.ljust(45) + " " + PASS)
    except Exception as e:
        print("  " + label.ljust(45) + " " + FAIL + "  " + str(e))
        errors.append((label, e))


# ---------------------------------------------------------------------------
# Setup & Config Tests
# ---------------------------------------------------------------------------

print("\n=== Config & Assistant Tests ===")

# Create a temporary config dir to avoid dirtying user prefs
import tempfile
import shutil

temp_dir = tempfile.mkdtemp()


def _test_config_manager() -> None:
    cfg_mgr = AssistantConfigManager(config_dir=Path(temp_dir))
    
    # Assert defaults loaded
    assert cfg_mgr.get_active_provider() == "anthropic"
    assert cfg_mgr.get_active_model() == "claude-3-5-sonnet-20241022"
    assert cfg_mgr.get_active_url() == "https://api.anthropic.com/v1/messages"
    
    # Test switching provider
    cfg_mgr.save({"active_provider": "openai"})
    assert cfg_mgr.get_active_provider() == "openai"
    assert cfg_mgr.get_active_model() == "gpt-4o"
    
    # Test api key fallback
    with patch.dict(os.environ, {"OPENAI_API_KEY": "env-secret-key"}):
        key = cfg_mgr.get_api_key("openai")
        assert key == "env-secret-key", f"Expected env-secret-key, got {key}"

check("AssistantConfigManager default and save", _test_config_manager)


def _test_assistant_history() -> None:
    assistant = AIAssistant(AssistantConfigManager(config_dir=Path(temp_dir)))
    assert len(assistant.history) == 0
    
    assistant.add_message("user", "Hello AI")
    assistant.add_message("assistant", "Hello Artist")
    
    assert len(assistant.history) == 2
    assert assistant.history[0]["role"] == "user"
    assert assistant.history[1]["content"] == "Hello Artist"
    
    assistant.clear_history()
    assert len(assistant.history) == 0

check("AIAssistant message history", _test_assistant_history)


# ---------------------------------------------------------------------------
# LLM Client Tests
# ---------------------------------------------------------------------------

print("\n=== LLM Client Tests ===")

def _test_client_factory() -> None:
    # Anthropic
    c = create_client("anthropic", "key", "url", "model")
    assert isinstance(c, AnthropicClient)
    
    # OpenAI
    c = create_client("openai", "key", "url", "model")
    assert isinstance(c, OpenAIClient)
    
    # Gemini
    c = create_client("gemini", "key", "url", "model")
    assert isinstance(c, GeminiClient)

check("create_client factory", _test_client_factory)


@patch("requests.post")
def _test_anthropic_client(mock_post: MagicMock) -> None:
    # Mock normal response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "content": [{"text": "Hello from Claude"}]
    }
    mock_post.return_value = mock_resp

    c = create_client("anthropic", "key-123", "https://api.anthropic.com/v1/messages", "claude-model")
    res = c.chat([{"role": "user", "content": "Hi"}], system_prompt="SysPrompt")
    
    assert res == "Hello from Claude"
    
    # Check what was posted
    posted_headers = mock_post.call_args[1]["headers"]
    posted_body = mock_post.call_args[1]["json"]
    
    assert posted_headers["x-api-key"] == "key-123"
    assert posted_headers["anthropic-version"] == "2023-06-01"
    assert posted_body["model"] == "claude-model"
    assert posted_body["system"] == "SysPrompt"
    assert posted_body["messages"] == [{"role": "user", "content": "Hi"}]

check("AnthropicClient normal chat", _test_anthropic_client)


@patch("requests.post")
def _test_openai_client(mock_post: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello from GPT"
                }
            }
        ]
    }
    mock_post.return_value = mock_resp

    c = create_client("openai", "key-openai", "https://api.openai.com/v1/chat/completions", "gpt-model")
    res = c.chat([{"role": "user", "content": "Hi"}], system_prompt="SysPrompt")
    
    assert res == "Hello from GPT"
    
    posted_headers = mock_post.call_args[1]["headers"]
    posted_body = mock_post.call_args[1]["json"]
    
    assert posted_headers["Authorization"] == "Bearer key-openai"
    assert posted_body["messages"][0] == {"role": "system", "content": "SysPrompt"}
    assert posted_body["messages"][1] == {"role": "user", "content": "Hi"}

check("OpenAIClient normal chat", _test_openai_client)


@patch("requests.post")
def _test_gemini_client(mock_post: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Hello from Gemini"}]
                }
            }
        ]
    }
    mock_post.return_value = mock_resp

    c = create_client("gemini", "key-gemini", "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", "gemini-model")
    res = c.chat([{"role": "user", "content": "Hi"}], system_prompt="SysPrompt")
    
    assert res == "Hello from Gemini"
    
    # Check URL building
    posted_url = mock_post.call_args[0][0]
    assert "gemini-model" in posted_url
    assert "key=key-gemini" in posted_url
    
    posted_body = mock_post.call_args[1]["json"]
    assert posted_body["systemInstruction"]["parts"][0]["text"] == "SysPrompt"
    assert posted_body["contents"][0]["role"] == "user"
    assert posted_body["contents"][0]["parts"][0]["text"] == "Hi"

check("GeminiClient normal chat", _test_gemini_client)


# ---------------------------------------------------------------------------
# LLM Client Streaming Tests
# ---------------------------------------------------------------------------

print("\n=== LLM Client Streaming Tests ===")

@patch("requests.post")
def _test_anthropic_streaming(mock_post: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    
    # Simulate SSE lines
    mock_resp.iter_lines.return_value = [
        b'data: {"type": "message_start"}',
        b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello "}}',
        b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "World"}}',
        b'data: [DONE]'
    ]
    mock_post.return_value = mock_resp

    c = create_client("anthropic", "key", "url", "model")
    chunks = list(c.chat_stream([{"role": "user", "content": "Hi"}]))
    
    assert chunks == ["Hello ", "World"], f"Got {chunks}"

check("AnthropicClient streaming parsing", _test_anthropic_streaming)


@patch("requests.post")
def _test_openai_streaming(mock_post: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_lines.return_value = [
        b'data: {"choices": [{"delta": {"content": "Hello "}}]}',
        b'data: {"choices": [{"delta": {"content": "World"}}]}',
        b'data: [DONE]'
    ]
    mock_post.return_value = mock_resp

    c = create_client("openai", "key", "url", "model")
    chunks = list(c.chat_stream([{"role": "user", "content": "Hi"}]))
    
    assert chunks == ["Hello ", "World"], f"Got {chunks}"

check("OpenAIClient streaming parsing", _test_openai_streaming)


@patch("requests.post")
def _test_gemini_streaming(mock_post: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    # Gemini returns stream chunks as JSON array elements
    mock_resp.iter_lines.return_value = [
        b'[',
        b'  {"candidates": [{"content": {"parts": [{"text": "Hello "}]}}]}',
        b'  ,{"candidates": [{"content": {"parts": [{"text": "World"}]}}]}',
        b']'
    ]
    mock_post.return_value = mock_resp

    c = create_client("gemini", "key", "url", "model")
    chunks = list(c.chat_stream([{"role": "user", "content": "Hi"}]))
    
    assert chunks == ["Hello ", "World"], f"Got {chunks}"

check("GeminiClient streaming parsing", _test_gemini_streaming)


# ---------------------------------------------------------------------------
# Scene Context Formatting Tests
# ---------------------------------------------------------------------------

print("\n=== Scene Context Formatting Tests ===")

from lh_houdini_pipeline.tools.houdini_ai_assistant.core.context_formatter import format_scene_context

def _test_scene_context_formatter() -> None:
    # Test empty selected nodes
    context_data = {
        "desktop": "Build",
        "network_path": "/obj",
        "selected_nodes": []
    }
    res = format_scene_context(context_data)
    assert "HOUDINI SCENE CONTEXT OVERVIEW" in res
    assert "No nodes are currently selected" in res

    # Test selected nodes with connection, expressions and attributes
    node_data = {
        "path": "/obj/geo1",
        "name": "geo1",
        "type": "geo",
        "inputs": [{"index": 0, "input_name": "input1", "connected_to": "/obj/file1"}],
        "outputs": [],
        "errors": "Failed to cook node",
        "warnings": "Low memory",
        "geometry": {
            "points_count": 100,
            "prims_count": 50,
            "attributes": {"point": ["P", "N"]},
            "groups": {"point": ["my_group"]}
        },
        "expressions": [{"name": "tx", "label": "Translate X", "expression": "$F", "value": "1.0"}],
        "modified_parms": {"scale": {"label": "Scale", "value": "2.0"}}
    }
    context_data = {
        "desktop": "Animate",
        "network_path": "/obj",
        "selected_nodes": [node_data]
    }
    res = format_scene_context(context_data)
    assert "Node: `geo1` (Type: `geo`)" in res
    assert "Input 0 (input1) connected to `/obj/file1`" in res
    assert "Failed to cook node" in res
    assert "Translate X" in res
    assert "Scale" in res

check("Scene context formatting Markdown conversion", _test_scene_context_formatter)


# ---------------------------------------------------------------------------
# Prompt Manager Tests
# ---------------------------------------------------------------------------

print("\n=== Prompt Manager Tests ===")

from lh_houdini_pipeline.tools.houdini_ai_assistant.prompts.manager import PromptManager

def _test_prompt_manager() -> None:
    pm = PromptManager()
    modes = pm.get_modes()
    assert "General" in modes
    assert "Debugger" in modes
    assert "HDA Architect" in modes
    
    prompt = pm.get_prompt("Debugger")
    assert "SRE specialist" in prompt or "Debugger" in prompt
    
    prompt_unknown = pm.get_prompt("NonExistentMode")
    assert "Senior Technical Artist" in prompt_unknown
    
    pm.register_prompt("CustomTA", "Custom prompt instructions")
    assert "CustomTA" in pm.get_modes()
    assert pm.get_prompt("CustomTA") == "Custom prompt instructions"

check("PromptManager modes and registry mappings", _test_prompt_manager)


# ---------------------------------------------------------------------------
# Agentic Tools Tests
# ---------------------------------------------------------------------------

print("\n=== Agentic Tools Tests ===")

from lh_houdini_pipeline.tools.houdini_ai_assistant.tools import get_default_tools
from lh_houdini_pipeline.tools.houdini_ai_assistant.core.assistant import AIAssistant

def _test_ai_tools() -> None:
    tools = get_default_tools()
    assert len(tools) >= 6
    
    # Check that each tool has basic properties
    for t in tools:
        assert isinstance(t.name, str) and t.name
        assert isinstance(t.description, str) and t.description
        assert isinstance(t.schema, dict) and t.schema["type"] == "object"

    # Test parser
    assistant = AIAssistant()
    
    # Test valid tool block parsing
    text_with_tool = (
        "Let me create that node for you.\n"
        "```json\n"
        "{\n"
        '    "action": "create_node",\n'
        '    "arguments": {\n'
        '        "parent_path": "/obj",\n'
        '        "node_type": "null",\n'
        '        "node_name": "my_null"\n'
        "    }\n"
        "}\n"
        "```\n"
    )
    call = assistant.parse_tool_call(text_with_tool)
    assert call is not None
    assert call["action"] == "create_node"
    assert call["arguments"]["node_type"] == "null"
    
    # Test invalid json block doesn't crash
    text_invalid = "```json\n{invalid json}\n```"
    call_invalid = assistant.parse_tool_call(text_invalid)
    assert call_invalid is None

check("AI Tool schemas and parse_tool_call parsing", _test_ai_tools)


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

shutil.rmtree(temp_dir)

print("\n=== Test Summary ===")
if errors:
    print(f"{len(errors)} tests failed:")
    for label, exc in errors:
        print(f"  - {label}: {exc}")
    sys.exit(1)
else:
    print("All tests passed successfully.")
    sys.exit(0)
