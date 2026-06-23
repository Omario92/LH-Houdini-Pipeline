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


def _test_hda_scaffold_tool_parameters() -> None:
    from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.node_tools import GenerateHdaScaffoldTool
    
    # Create mock hou module
    mock_hou = MagicMock()
    mock_hou.stringParmType.FileReference = "FileReference"
    mock_hou.scriptLanguage.Python = "Python"
    
    # Setup mocks for constructors
    mock_hou.FloatParmTemplate = MagicMock()
    mock_hou.IntParmTemplate = MagicMock()
    mock_hou.StringParmTemplate = MagicMock()
    mock_hou.ToggleParmTemplate = MagicMock()
    mock_hou.ButtonParmTemplate = MagicMock()
    
    tool = GenerateHdaScaffoldTool()
    
    # We patch sys.modules so when the tool imports hou, it gets our mock
    with patch.dict(sys.modules, {"hou": mock_hou}):
        # Test float parameter template creation
        float_data = {
            "name": "my_float",
            "label": "My Float",
            "type": "float",
            "default": "1.5",
            "min_range": 0.0,
            "max_range": 10.0,
            "help_text": "A float parm",
            "callback_script": "hou.phm().on_change()"
        }
        
        mock_float_template = MagicMock()
        mock_hou.FloatParmTemplate.return_value = mock_float_template
        
        res = tool._create_parm_template(float_data)
        assert res is mock_float_template
        
        # Verify FloatParmTemplate constructor arguments
        mock_hou.FloatParmTemplate.assert_called_once_with(
            "my_float", "My Float", 1, default_value=(1.5,), help="A float parm"
        )
        mock_float_template.setRange.assert_called_once_with(0.0, 10.0)
        mock_float_template.setCallbackScript.assert_called_once_with("hou.phm().on_change()")
        mock_float_template.setCallbackScriptLanguage.assert_called_once_with("Python")
        
        # Test toggle parameter template creation
        toggle_data = {
            "name": "my_toggle",
            "label": "My Toggle",
            "type": "toggle",
            "default": "true"
        }
        
        mock_toggle_template = MagicMock()
        mock_hou.ToggleParmTemplate.return_value = mock_toggle_template
        
        res_toggle = tool._create_parm_template(toggle_data)
        assert res_toggle is mock_toggle_template
        
        mock_hou.ToggleParmTemplate.assert_called_once_with(
            "my_toggle", "My Toggle", default_value=True, help=""
        )
        
        # Test button parameter template creation
        button_data = {
            "name": "my_button",
            "label": "My Button",
            "type": "button",
            "help_text": "Click me"
        }
        
        mock_button_template = MagicMock()
        mock_hou.ButtonParmTemplate.return_value = mock_button_template
        
        res_button = tool._create_parm_template(button_data)
        assert res_button is mock_button_template
        mock_hou.ButtonParmTemplate.assert_called_once_with(
            "my_button", "My Button", help="Click me"
        )

check("GenerateHdaScaffoldTool parameter templates", _test_hda_scaffold_tool_parameters)


@patch("lh_houdini_pipeline.houdini.hda.create_hda_from_subnet")
@patch("lh_houdini_pipeline.houdini.hda.set_hda_python_module")
@patch("lh_houdini_pipeline.houdini.hda.set_hda_event_script")
@patch("lh_houdini_pipeline.houdini.hda.set_hda_parm_template_group")
@patch("lh_houdini_pipeline.houdini.hda.save_and_reload_hda")
def _test_hda_scaffold_tool_execute(
    mock_save_reload: MagicMock,
    mock_set_parm_group: MagicMock,
    mock_set_event: MagicMock,
    mock_set_py_module: MagicMock,
    mock_create_hda: MagicMock,
) -> None:
    from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.node_tools import GenerateHdaScaffoldTool
    
    mock_hou = MagicMock()
    mock_hou.getenv.return_value = "E:/temp_hip"
    
    mock_subnet = MagicMock()
    mock_subnet.path.return_value = "/obj/sop_mountain_generator"
    mock_subnet.name.return_value = "sop_mountain_generator"
    
    mock_parent = MagicMock()
    mock_parent.createNode.return_value = mock_subnet
    mock_hou.node.return_value = mock_parent
    
    mock_definition = MagicMock()
    mock_create_hda.return_value = mock_definition
    
    tool = GenerateHdaScaffoldTool()
    
    args = {
        "parent_path": "/obj",
        "node_type": "subnet",
        "hda_name": "sop_mountain_generator",
        "hda_label": "SOP Mountain Generator",
        "python_module": "print('hello')",
        "on_created": "print('created')",
        "parameters": [
            {"name": "height", "type": "float", "default": "2.0"}
        ]
    }
    
    with patch.dict(sys.modules, {"hou": mock_hou}):
        res = tool.execute(args)
        
        # Verify success
        assert res["success"] is True, f"Failed execution: {res}"
        assert res["node_path"] == "/obj/sop_mountain_generator"
        
        # Verify calls
        mock_hou.node.assert_called_once_with("/obj")
        mock_parent.createNode.assert_called_once_with("subnet", "sop_mountain_generator")
        
        expected_hda_path = os.path.normpath("E:/temp_hip/otls/sop_mountain_generator.hda")
        actual_hda_path = os.path.normpath(mock_create_hda.call_args[0][1])
        assert actual_hda_path == expected_hda_path
        
        mock_create_hda.assert_called_once()
        mock_set_py_module.assert_called_once_with(mock_definition, "print('hello')")
        mock_set_event.assert_called_once_with(mock_definition, "OnCreated", "print('created')")
        mock_set_parm_group.assert_called_once()
        mock_save_reload.assert_called_once_with(mock_definition, mock_subnet)

check("GenerateHdaScaffoldTool execute", _test_hda_scaffold_tool_execute)


def _test_mcp_integration() -> None:
    from lh_houdini_pipeline.tools.houdini_ai_assistant.mcp.server import McpTcpServer
    from lh_houdini_pipeline.tools.houdini_ai_assistant.mcp.client import McpClient, DelegatedMcpTool
    from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.base import AITool
    
    class DummyTool(AITool):
        @property
        def name(self) -> str:
            return "dummy_tool"
        @property
        def description(self) -> str:
            return "A dummy tool for testing."
        @property
        def schema(self) -> dict:
            return {"type": "object", "properties": {"val": {"type": "string"}}}
        def execute(self, arguments: dict) -> dict:
            return {"success": True, "output": arguments.get("val", "hello")}
            
    # 1. Start Server
    server = McpTcpServer()
    server._tools = [DummyTool()]
    
    # Port 14849 to avoid collision
    ok = server.start(port=14849)
    assert ok is True, "Failed to start McpTcpServer"
    assert server.is_running() is True
    
    # 2. Connect Client
    client = McpClient("tcp://127.0.0.1:14849")
    connected = client.connect()
    assert connected is True, "McpClient failed to connect to McpTcpServer"
    
    # 3. Check tools list
    tools = client.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "dummy_tool"
    assert tools[0]["inputSchema"]["type"] == "object"
    
    # 4. Call tool
    res = client.call_tool("dummy_tool", {"val": "test-data"})
    assert res.get("success") is True
    assert res.get("output") == "test-data"
    
    # 5. Test tool approval callback
    approval_called = []
    def approval_cb(name: str, args: dict) -> bool:
        approval_called.append((name, args))
        return False # Reject
        
    server.approval_callback = approval_cb
    
    # Add a mock modifying tool
    class MockCreateNode(AITool):
        @property
        def name(self) -> str:
            return "create_node"
        @property
        def description(self) -> str:
            return "Mock create node"
        @property
        def schema(self) -> dict:
            return {"type": "object"}
        def execute(self, arguments: dict) -> dict:
            return {"success": True}
            
    server._tools.append(MockCreateNode())
    client.connect() # Re-connect to list new tool
    
    res_reject = client.call_tool("create_node", {"parent": "/obj"})
    assert len(approval_called) == 1
    assert approval_called[0][0] == "create_node"
    assert approval_called[0][1] == {"parent": "/obj"}
    assert "rejected" in res_reject.get("message", "").lower()
    
    # 6. Stop Server
    server.stop()
    assert server.is_running() is False

check("MCP Client/Server TCP integration", _test_mcp_integration)


def _test_pipeline_tools() -> None:
    from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.pipeline_tools import (
        ProjectManagerCreateTool,
        CameraManagerTurntableTool,
    )
    from unittest.mock import MagicMock, patch
    
    # 1. Test ProjectManagerCreateTool
    pm_tool = ProjectManagerCreateTool()
    assert pm_tool.name == "project_manager_create_project"
    assert "root" in pm_tool.schema["required"]
    
    with patch("lh_houdini_pipeline.tools.project_manager.core.plan_project") as mock_plan, \
         patch("lh_houdini_pipeline.tools.project_manager.service.create_project") as mock_create, \
         patch("lh_houdini_pipeline.tools.project_manager.service.set_houdini_job") as mock_job:
         
        mock_plan_inst = MagicMock()
        mock_plan_inst.project = "test_proj"
        mock_plan_inst.project_root = "/some/path/test_proj"
        mock_plan_inst.directories = ("/some/path/test_proj", "/some/path/test_proj/houdini")
        mock_plan.return_value = mock_plan_inst
        
        mock_result = MagicMock()
        mock_result.ok = True
        mock_result.summary.return_value = "2 created"
        mock_create.return_value = mock_result
        mock_job.return_value = True
        
        args = {
            "root": "/some/path",
            "project": "test_proj",
            "assets": ["hero"],
            "shots": ["sh01"]
        }
        res = pm_tool.execute(args)
        assert res["success"] is True
        assert "test_proj" in res["message"]
        assert res["job_set"] is True
        mock_plan.assert_called_once_with("/some/path", "test_proj", assets=["hero"], shots=["sh01"])
        mock_create.assert_called_once_with(mock_plan_inst, dry_run=False)
        mock_job.assert_called_once_with("/some/path/test_proj")

    # 2. Test CameraManagerTurntableTool
    cam_tool = CameraManagerTurntableTool()
    assert cam_tool.name == "camera_manager_create_turntable"
    
    with patch("lh_houdini_pipeline.tools.camera_manager.service.create_turntable") as mock_turntable:
        mock_turntable.return_value = "/stage/orbit_cam"
        args = {
            "name": "orbit_cam",
            "total_frames": 240,
            "center": [0, 1.5, 0],
            "radius": 15.0,
            "target_path": "/stage/geo_mesh"
        }
        res = cam_tool.execute(args)
        assert res["success"] is True
        assert res["node_path"] == "/stage/orbit_cam"
        mock_turntable.assert_called_once()
        
        call_kwargs = mock_turntable.call_args[1]
        assert call_kwargs["center"] == (0.0, 1.5, 0.0)
        assert call_kwargs["radius"] == 15.0
        assert call_kwargs["target_path"] == "/stage/geo_mesh"
        assert call_kwargs["spec"].total_frames == 240

check("AITool ProjectManager and CameraManager bindings", _test_pipeline_tools)


def _test_mcp_client_error_handling() -> None:
    from lh_houdini_pipeline.tools.houdini_ai_assistant.mcp.client import McpClient
    from unittest.mock import patch, MagicMock
    import requests
    
    # 1. Connection Timeout error
    with patch("socket.create_connection", side_effect=TimeoutError("Connection timed out")):
        client = McpClient("tcp://127.0.0.1:9999")
        connected = client.connect()
        assert connected is False
        
    # 2. Malformed JSON-RPC handshake response error
    mock_socket = MagicMock()
    mock_file = MagicMock()
    mock_file.readline.return_value = "not a valid json payload\n"
    mock_socket.makefile.return_value = mock_file
    
    with patch("socket.create_connection", return_value=mock_socket):
        client = McpClient("tcp://127.0.0.1:9999")
        connected = client.connect()
        assert connected is False
        
    # 3. HTTP Timeout on call_tool
    client = McpClient("http://localhost:8000")
    client._is_connected = True
    with patch("requests.post", side_effect=requests.Timeout("HTTP timed out")):
        res = client.call_tool("some_tool", {})
        assert res["success"] is False
        assert "timed out" in res["error"].lower()

check("MCP Client robust error handling", _test_mcp_client_error_handling)


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
