# Houdini AI Assistant

A scene-aware, agentic, and thread-safe AI assistant parented natively to Houdini's PySide application. It inspects active contexts, executes main-thread Houdini Object Model (HOM) operations safely behind modal approval gates, supports specialist mode instruction sets, and delegates tasks using socket-based Model Context Protocol (MCP) clients/servers.

---

## Features

1. **Scene Context Inspector**:
   - Inspects the active network path, selected nodes, parameter wiring, warning states, node types, attributes, and expressions.
   - Converts the raw Houdini state into a token-efficient Markdown prompt payload.
   - Captures viewport snapshots and encodes them into Base64 format for multimodal vision LLMs.

2. **Gated Action Approval Dialog**:
   - Compiles JSON tool calls proposed by the LLM.
   - Intercepts and displays all modifying tools (`create_node`, `set_parm`, `run_python_snippet`, `generate_hda_scaffold`, `project_manager_create_project`, `camera_manager_create_turntable`) in a modal review dialog.
   - Visualizes diff changes (e.g. proposed Python scripts or folder path creations) for user verification before execution.
   - Capped at a maximum loop depth of 5 steps to prevent runaway recursive executions.

3. **Programmatic HDA Architect**:
   - Autogenerates subnets, compiles Houdini Digital Assets (HDAs), injects custom parameter templates (Float, Int, String, Toggle, Button, File), and configures custom `PythonModule` code and `OnCreated` scripts.

4. **Model Context Protocol (MCP) Integration**:
   - **Internal TCP Server**: Hosts a lightweight, multi-threaded TCP socket-based JSON-RPC 2.0 server. Allows external C-suite agents to query context and request HOM operations. Incoming socket requests are dispatched via Qt signals and execution is blocked until approved by the artist.
   - **External Client Delegation**: Connects to other TCP (`tcp://127.0.0.1:14848`) or HTTP (`http://localhost:8000`) MCP servers, dynamically loading external tools as native operations in the assistant.

5. **Integrated Pipeline Bindings**:
   - Wraps Project Manager operations (`project_manager_create_project`) to scaffold directory structures and set `$JOB`.
   - Wraps Camera Manager operations (`camera_manager_create_turntable`) to keyframe USD turntable camera orbits in Solaris.

---

## Specialist Prompt Modes

The assistant supports six dedicated system prompt instruction sets:
* **General**: Default helpful pipeline assistant.
* **HDA Architect**: Specialized in generating HDA parameter schemas and callback wiring.
* **Debugger**: Inspects node errors, warnings, and network hierarchies to propose solutions.
* **VEX/Python Expert**: Deeply versed in writing optimized VEX snippets and safe Python HOM scripts.
* **Solaris/USD**: Focused on LOP graphs, USD stage configurations, composition arcs, and variant sets.
* **MaterialX**: Expert in building MaterialX shading networks and texture mappings.

---

## Installation

### 1. Register Package Path
Ensure this repository root directory is on your `PYTHONPATH`. Add the following to your `houdini.env` file:
```env
PYTHONPATH = "E:/OneDrive/Documents/Claude/Projects/LH Houdini Pipeline;&"
```

### 2. Shelf Button Integration
You can install the pipeline shelf by copying `scripts/lh_pipeline.shelf` into your Houdini preferences folder (`$HOUDINI_USER_PREF_DIR/toolbar/`), or right-clicking the shelf dock and adding the member tool `lh_ai_assistant` running the following python launcher script:
```python
from lh_houdini_pipeline.tools.houdini_ai_assistant import launch
launch()
```

---

## Configuration Settings

The tool configures settings under `~/.lh_pipeline/ai_assistant.json`. Main configuration groups:
```json
{
  "active_provider": "Anthropic",
  "providers": {
    "Anthropic": {
      "api_key": "YOUR_API_KEY",
      "active_model": "claude-3-5-sonnet-latest",
      "models": ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"]
    },
    "OpenAI": {
      "api_key": "YOUR_API_KEY",
      "active_model": "gpt-4o",
      "models": ["gpt-4o", "gpt-4o-mini"]
    }
  },
  "use_mcp": false,
  "mcp_server_url": "tcp://127.0.0.1:14848",
  "use_mcp_server": false,
  "mcp_server_port": 14848
}
```

---

## MCP TCP Socket Protocol (JSON-RPC 2.0)

Both client and server support newline-delimited JSON packets over TCP sockets to bypass stdio redirection limits.

### 1. Handshake (initialize)
```json
{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05"}, "id": 1}
```
**Response**:
```json
{"jsonrpc": "2.0", "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "LH-Houdini-AI-Server"}}, "id": 1}
```

### 2. List Tools (tools/list)
```json
{"jsonrpc": "2.0", "method": "tools/list", "id": 2}
```
**Response**:
```json
{"jsonrpc": "2.0", "result": {"tools": [{"name": "create_node", "description": "Create a node...", "inputSchema": {}}]}, "id": 2}
```

### 3. Call Tool (tools/call)
```json
{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "create_node", "arguments": {"parent_path": "/obj", "node_type": "null", "node_name": "my_null"}}, "id": 3}
```
**Response (Success)**:
```json
{"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": "{\n  \"success\": true,\n  \"node_path\": \"/obj/my_null\"\n}"}], "isError": false}, "id": 3}
```
