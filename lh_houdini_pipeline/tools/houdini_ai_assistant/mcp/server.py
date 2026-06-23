"""
lh_houdini_pipeline.tools.houdini_ai_assistant.mcp.server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Server logic for hosting a lightweight MCP server from inside Houdini.
"""

from __future__ import annotations

import json
import socket
import threading
import uuid
from typing import Any, Dict, List, Optional, Callable

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.houdini_ai_assistant.tools import get_default_tools
from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.base import AITool

_log = get_logger(__name__)

try:
    from PySide6 import QtCore
except ImportError:
    from PySide2 import QtCore


class McpTcpServer(QtCore.QObject):
    """A socket-based TCP server hosting MCP tools.

    Runs connection handling in background threads and marshals HOM operations
    to the main thread safely.
    """

    status_changed = QtCore.Signal(str)
    client_connected = QtCore.Signal(str)
    
    # Internal signal to request main-thread execution
    # args: request_id, tool_name, arguments
    request_execution = QtCore.Signal(str, str, dict)

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self._server_socket: Optional[socket.socket] = None
        self._is_running = False
        self._tools: List[AITool] = get_default_tools()
        self._thread: Optional[threading.Thread] = None
        self._connections: List[socket.socket] = []
        
        # Dictionary to store pending execution results
        # request_id -> {"event": threading.Event, "result": None, "approved": True}
        self._pending_executions: Dict[str, Dict[str, Any]] = {}
        
        # Callback to execute tool on the main thread (alternative to signals, e.g. for unit tests)
        self.approval_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None
        
        # Toggle thread dispatching (True when hosted in panel, False in unit tests)
        self.use_thread_dispatch = False
        
        # Connect internal signal to main thread dispatcher
        self.request_execution.connect(self._dispatch_to_main_thread)

    def start(self, host: str = "127.0.0.1", port: int = 14848) -> bool:
        """Start listening for incoming TCP connections in a background thread."""
        if self._is_running:
            self.stop()

        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((host, port))
            self._server_socket.listen(5)
        except Exception as e:
            _log.error(f"Failed to bind MCP server to {host}:{port} - {e}")
            self.status_changed.emit(f"Error: {e}")
            return False

        self._is_running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

        _log.info(f"MCP TCP Server listening on {host}:{port}")
        self.status_changed.emit(f"Running on port {port}")
        return True

    def stop(self) -> None:
        """Stop the server and close all client connections."""
        self._is_running = False
        
        if self._server_socket:
            try:
                # Force close the socket to wake up accept()
                self._server_socket.close()
            except Exception:
                pass
            self._server_socket = None

        for conn in list(self._connections):
            try:
                conn.close()
            except Exception:
                pass
        self._connections.clear()
        
        # Wake up any pending wait events
        for pending in self._pending_executions.values():
            pending["event"].set()
        self._pending_executions.clear()

        _log.info("MCP TCP Server stopped.")
        self.status_changed.emit("Stopped")

    def is_running(self) -> bool:
        return self._is_running

    def _accept_loop(self) -> None:
        """Background thread loop accepting client connections."""
        while self._is_running:
            try:
                if not self._server_socket:
                    break
                conn, addr = self._server_socket.accept()
                if not self._is_running:
                    conn.close()
                    break
                
                self._connections.append(conn)
                client_addr = f"{addr[0]}:{addr[1]}"
                _log.info(f"Client connected to MCP TCP Server: {client_addr}")
                self.client_connected.emit(client_addr)
                
                # Spawn connection handler thread
                t = threading.Thread(target=self._handle_client, args=(conn,), daemon=True)
                t.start()
            except Exception:
                break

    def _handle_client(self, conn: socket.socket) -> None:
        """Handle individual client session in a separate thread."""
        buffer = ""
        conn.settimeout(None) # Infinite wait for clients
        
        try:
            while self._is_running:
                data = conn.recv(4096)
                if not data:
                    break
                
                buffer += data.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, rest = buffer.split("\n", 1)
                    buffer = rest
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        request = json.loads(line)
                        self._handle_request(conn, request)
                    except json.JSONDecodeError as e:
                        self._send_error(conn, None, -32700, f"Parse error: {e}")
                    except Exception as e:
                        self._send_error(conn, None, -32603, f"Internal error: {e}")
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
            if conn in self._connections:
                self._connections.remove(conn)
            _log.info("Client disconnected from MCP TCP Server.")

    def _handle_request(self, conn: socket.socket, request: Dict[str, Any]) -> None:
        """Route JSON-RPC requests."""
        if not isinstance(request, dict):
            self._send_error(conn, None, -32600, "Invalid Request: expected object")
            return

        method = request.get("method")
        req_id = request.get("id")

        if not method:
            return

        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "LH-Houdini-AI-Server", "version": "1.0.0"}
            }
            self._send_response(conn, req_id, result)
        elif method == "tools/list":
            mcp_tools = []
            for tool in self._tools:
                mcp_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.schema
                })
            self._send_response(conn, req_id, {"tools": mcp_tools})
        elif method == "tools/call":
            self._handle_tools_call(conn, req_id, request.get("params", {}))
        else:
            self._send_error(conn, req_id, -32601, f"Method not found: '{method}'")

    def _handle_tools_call(self, conn: socket.socket, req_id: Any, params: Dict[str, Any]) -> None:
        """Execute a tool. Safeguards execution by switching to main thread if required."""
        name = params.get("name")
        arguments = params.get("arguments", {})

        if not name:
            self._send_error(conn, req_id, -32602, "Invalid params: 'name' is required")
            return

        tool = next((t for t in self._tools if t.name == name), None)
        if not tool:
            self._send_error(conn, req_id, -32601, f"Tool not found: '{name}'")
            return

        is_modifying = name in ("create_node", "set_parm", "run_python_snippet", "generate_hda_scaffold")
        approved = True

        # Check approval callbacks or main-thread dispatching
        if is_modifying:
            if self.use_thread_dispatch:
                # Synchronize execution with the main thread using threading.Event
                req_uid = str(uuid.uuid4())
                event = threading.Event()
                self._pending_executions[req_uid] = {
                    "event": event,
                    "approved": True,
                    "result": None
                }
                
                # Emit signal to run on main thread (connection must be Qt.QueuedConnection or default if cross-thread)
                self.request_execution.emit(req_uid, name, arguments)
                
                # Wait for main thread to notify us
                event.wait()
                
                pending = self._pending_executions.pop(req_uid, None)
                if pending:
                    approved = pending["approved"]
                    if not approved:
                        result = {
                            "content": [{"type": "text", "text": f"Tool execution for '{name}' was rejected."}],
                            "isError": True
                        }
                        self._send_response(conn, req_id, result)
                        return
                    
                    if pending["result"] is not None:
                        # Already executed on main thread
                        self._send_response(conn, req_id, pending["result"])
                        return
            else:
                # Direct callback for synchronous environments (e.g. unit tests)
                if self.approval_callback:
                    try:
                        approved = self.approval_callback(name, arguments)
                    except Exception as e:
                        _log.error(f"Approval callback failed: {e}")
                        approved = False

                if not approved:
                    result = {
                        "content": [{"type": "text", "text": f"Tool execution for '{name}' was rejected."}],
                        "isError": True
                    }
                    self._send_response(conn, req_id, result)
                    return

        # Execute read-only tools or modifying tools (if approved and not already executed)
        try:
            execution_result = tool.execute(arguments)
            text_out = json.dumps(execution_result, indent=2)
            is_err = not execution_result.get("success", True)
            result = {
                "content": [{"type": "text", "text": text_out}],
                "isError": is_err
            }
            self._send_response(conn, req_id, result)
        except Exception as e:
            result = {
                "content": [{"type": "text", "text": f"Execution error: {e}"}],
                "isError": True
            }
            self._send_response(conn, req_id, result)

    def _dispatch_to_main_thread(self, req_id: str, name: str, arguments: Dict[str, Any]) -> None:
        """Main thread slot that handles approval gating and tool execution.

        Automatically triggered by request_execution signal.
        """
        pending = self._pending_executions.get(req_id)
        if not pending:
            return

        approved = True
        if self.approval_callback:
            try:
                approved = self.approval_callback(name, arguments)
            except Exception as e:
                _log.error(f"Approval callback failed: {e}")
                approved = False

        pending["approved"] = approved
        if approved:
            # Run tool on main thread!
            tool = next((t for t in self._tools if t.name == name), None)
            if tool:
                try:
                    res = tool.execute(arguments)
                    text_out = json.dumps(res, indent=2)
                    pending["result"] = {
                        "content": [{"type": "text", "text": text_out}],
                        "isError": not res.get("success", True)
                    }
                except Exception as e:
                    pending["result"] = {
                        "content": [{"type": "text", "text": f"Execution error: {e}"}],
                        "isError": True
                    }
        
        # Wake up client thread
        pending["event"].set()

    def _send_response(self, conn: socket.socket, req_id: Any, result: Dict[str, Any]) -> None:
        response = {"jsonrpc": "2.0", "result": result, "id": req_id}
        self._write_line(conn, response)

    def _send_error(self, conn: socket.socket, req_id: Any, code: int, message: str) -> None:
        response = {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": req_id}
        self._write_line(conn, response)

    def _write_line(self, conn: socket.socket, payload: Dict[str, Any]) -> None:
        try:
            line = json.dumps(payload) + "\n"
            conn.sendall(line.encode("utf-8"))
        except Exception as e:
            _log.error(f"Failed to write to socket: {e}")
