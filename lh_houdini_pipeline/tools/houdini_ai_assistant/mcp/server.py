"""
lh_houdini_pipeline.tools.houdini_ai_assistant.mcp.server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Server logic for hosting a lightweight MCP server from inside Houdini.

Transports (newline-delimited JSON-RPC 2.0, one message per line/frame):

* **Windows named pipe** (``pipe_name``) -- production path used by
  ``scripts/lh_mcp_stdio.py --pipe``. Clients authenticate through the
  ``multiprocessing.connection`` authkey challenge using the run token.
* **Loopback TCP** -- fallback / panel-to-panel. With ``require_auth`` the
  first line must be ``{"lhAuth": "<token>"}``; the server answers
  ``{"lhAuth": "ok"}`` or closes the connection.

The token is regenerated on every :meth:`McpTcpServer.start` and written to
the credential file (see :mod:`..mcp.auth`), which is removed on stop.
"""

from __future__ import annotations

import json
import os
import socket
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.houdini_ai_assistant.mcp import auth as _auth
from lh_houdini_pipeline.tools.houdini_ai_assistant.tools import get_default_tools
from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.base import AITool, requires_approval

_log = get_logger(__name__)

try:
    from PySide6 import QtCore
except ImportError:
    from PySide2 import QtCore

# ``multiprocessing.connection`` family for the pipe listener. Only Windows
# supports AF_PIPE; tests on POSIX swap this for AF_UNIX to exercise the same
# code path (that does NOT validate real Windows named-pipe behaviour).
_PIPE_FAMILY = "AF_PIPE"

MAX_MESSAGE_BYTES = 4 * 1024 * 1024
"""Upper bound for one framed message (matches the bridge)."""


class _PipeConn:
    """Adapter giving a ``multiprocessing`` Connection a socket-like API.

    Lets the JSON-RPC handlers use ``sendall`` for every transport.
    """

    def __init__(self, conn: Any) -> None:
        """Wrap *conn*.

        Args:
            conn: A ``multiprocessing.connection.Connection``.
        """
        self._conn = conn
        self._lock = threading.Lock()

    def sendall(self, data: bytes) -> None:
        """Send *data* as one message frame.

        Args:
            data: Encoded JSON line.
        """
        with self._lock:
            self._conn.send_bytes(data)

    def recv_message(self) -> bytes:
        """Receive one message frame.

        Returns:
            Raw bytes of the frame.

        Raises:
            EOFError: When the peer closed the pipe.
        """
        return self._conn.recv_bytes(MAX_MESSAGE_BYTES)

    def close(self) -> None:
        """Close the underlying connection."""
        self._conn.close()


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
        self._connections: List[Any] = []

        # Authentication / named pipe state (set by start()).
        self.require_auth = True
        self._token = ""
        self._auth_file: Optional[Path] = None
        self._pipe_name: Optional[str] = None
        self._pipe_listener: Any = None
        self._pipe_thread: Optional[threading.Thread] = None
        
        # Dictionary to store pending execution results
        # request_id -> {"event": threading.Event, "result": None, "approved": True}
        self._pending_executions: Dict[str, Dict[str, Any]] = {}
        
        # Callback to execute tool on the main thread (alternative to signals, e.g. for unit tests)
        self.approval_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None
        
        # Toggle thread dispatching (True when hosted in panel, False in unit tests)
        self.use_thread_dispatch = False
        
        # Connect internal signal to main thread dispatcher
        self.request_execution.connect(self._dispatch_to_main_thread)

    def start(
        self,
        host: str = "127.0.0.1",
        port: int = 14848,
        *,
        pipe_name: Optional[str] = None,
        auth_file: Optional[str] = None,
        require_auth: bool = True,
    ) -> bool:
        """Start listening in background threads.

        Args:
            host: TCP bind address (keep loopback).
            port: TCP port.
            pipe_name: Named-pipe endpoint to listen on as well (Windows),
                e.g. :data:`auth.DEFAULT_PIPE`. ``None`` disables the pipe.
            auth_file: Credential file to write; defaults to
                :func:`auth.default_auth_file`.
            require_auth: When ``True`` (default) every client must present
                the run token. A named pipe always requires it.

        Returns:
            ``True`` if every requested listener started and the credential
            file was written; on failure nothing is left listening.
        """
        if self._is_running:
            self.stop()

        self.require_auth = bool(require_auth)
        self._token = _auth.generate_token()
        self._auth_file = Path(auth_file) if auth_file else _auth.default_auth_file()
        self._pipe_name = pipe_name

        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                # Windows: SO_REUSEADDR would let another process bind the
                # same port and intercept clients; claim it exclusively.
                self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            else:
                self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((host, port))
            self._server_socket.listen(5)
            if pipe_name:
                from multiprocessing.connection import Listener
                self._pipe_listener = Listener(
                    pipe_name, family=_PIPE_FAMILY, authkey=self._token.encode("utf-8")
                )
            if self.require_auth or pipe_name:
                _auth.write_credential(
                    self._auth_file, self._token,
                    pipe=pipe_name, host=host, port=port,
                )
        except Exception as e:
            _log.error(f"Failed to start MCP server ({host}:{port}, pipe={pipe_name}) - {e}")
            self._close_listeners()
            self.status_changed.emit(f"Error: {e}")
            return False

        self._is_running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()
        if self._pipe_listener is not None:
            self._pipe_thread = threading.Thread(target=self._pipe_accept_loop, daemon=True)
            self._pipe_thread.start()

        where = f"port {port}" + (f" + pipe {pipe_name}" if pipe_name else "")
        _log.info(f"MCP Server listening on {host}:{port}"
                  + (f" and {pipe_name}" if pipe_name else "")
                  + (f" (credential: {self._auth_file})" if self.require_auth or pipe_name else ""))
        self.status_changed.emit(f"Running on {where}")
        return True

    @property
    def auth_file(self) -> Optional[Path]:
        """Credential file written by the last :meth:`start` (or ``None``)."""
        return self._auth_file

    def _close_listeners(self) -> None:
        """Close the TCP socket and named-pipe listener (idempotent)."""
        if self._server_socket:
            try:
                # Force close the socket to wake up accept()
                self._server_socket.close()
            except Exception:
                pass
            self._server_socket = None

        listener = self._pipe_listener
        self._pipe_listener = None
        if listener is not None:
            # A pending accept() on a Windows pipe is not woken by close();
            # connect once with the run token so the accept loop can exit.
            if self._pipe_thread is not None and self._pipe_thread.is_alive():
                try:
                    from multiprocessing.connection import Client
                    Client(self._pipe_name, family=_PIPE_FAMILY,
                           authkey=self._token.encode("utf-8")).close()
                except Exception:
                    pass
            try:
                listener.close()
            except Exception:
                pass

    def stop(self) -> None:
        """Stop the server and close all client connections."""
        self._is_running = False
        self._close_listeners()
        if self._token and self._auth_file is not None:
            _auth.remove_credential(self._auth_file, self._token)

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

    def _pipe_accept_loop(self) -> None:
        """Background loop accepting authenticated named-pipe clients."""
        from multiprocessing import AuthenticationError
        while self._is_running:
            listener = self._pipe_listener
            if listener is None:
                break
            try:
                raw = listener.accept()
            except AuthenticationError:
                _log.warning("Rejected named-pipe client: wrong or missing token.")
                continue
            except Exception:
                break
            if not self._is_running:
                try:
                    raw.close()
                except Exception:
                    pass
                break
            conn = _PipeConn(raw)
            self._connections.append(conn)
            _log.info("Client connected to MCP server via named pipe.")
            self.client_connected.emit(str(self._pipe_name))
            t = threading.Thread(target=self._handle_pipe_client, args=(conn,), daemon=True)
            t.start()

    def _handle_pipe_client(self, conn: _PipeConn) -> None:
        """Serve one named-pipe client (already authenticated by authkey)."""
        try:
            while self._is_running:
                try:
                    data = conn.recv_message()
                except (EOFError, OSError):
                    break
                for line in data.decode("utf-8", errors="replace").split("\n"):
                    self._process_line(conn, line)
        finally:
            try:
                conn.close()
            except Exception:
                pass
            if conn in self._connections:
                self._connections.remove(conn)
            _log.info("Named-pipe client disconnected from MCP server.")

    def _process_line(self, conn: Any, line: str) -> None:
        """Decode one JSON-RPC line and route it, replying on errors.

        Args:
            conn: Socket-like connection with ``sendall``.
            line: One raw message line.
        """
        line = line.strip()
        if not line:
            return
        try:
            request = json.loads(line)
            self._handle_request(conn, request)
        except json.JSONDecodeError as e:
            self._send_error(conn, None, -32700, f"Parse error: {e}")
        except Exception as e:
            self._send_error(conn, None, -32603, f"Internal error: {e}")

    def _check_tcp_auth(self, conn: Any, line: str) -> bool:
        """Validate the TCP ``{"lhAuth": token}`` handshake line.

        Args:
            conn: Client socket.
            line: First line received from the client.

        Returns:
            ``True`` if the token matched (and ``ok`` was sent).
        """
        try:
            msg = json.loads(line)
        except ValueError:
            msg = None
        if isinstance(msg, dict) and _auth.tokens_match(self._token, msg.get("lhAuth")):
            self._write_line(conn, {"lhAuth": "ok"})
            return True
        _log.warning("Rejected TCP MCP client: missing or wrong auth token.")
        self._write_line(conn, {"lhAuth": "denied"})
        return False

    def _handle_client(self, conn: socket.socket) -> None:
        """Handle individual client session in a separate thread."""
        buffer = ""
        conn.settimeout(None) # Infinite wait for clients
        authenticated = not self.require_auth

        try:
            while self._is_running:
                data = conn.recv(4096)
                if not data:
                    break
                
                buffer += data.decode("utf-8", errors="replace")
                if len(buffer) > MAX_MESSAGE_BYTES:
                    self._send_error(conn, None, -32600, "Message exceeds size limit.")
                    break
                while "\n" in buffer:
                    line, rest = buffer.split("\n", 1)
                    buffer = rest

                    if not authenticated:
                        if not line.strip():
                            continue
                        if not self._check_tcp_auth(conn, line):
                            return
                        authenticated = True
                        continue

                    self._process_line(conn, line)
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

        # JSON-RPC notifications (no "id": notifications/initialized,
        # notifications/cancelled, ...) must never get a response.
        if "id" not in request:
            return

        if method == "ping":
            self._send_response(conn, req_id, {})
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

        # Fail-closed: anything not explicitly read-only (incl. pipeline tools
        # such as project_manager_create_project) goes through approval and,
        # in the panel, runs on the main thread.
        is_modifying = requires_approval(tool)
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
                
                # Wait for main thread to notify us, but never block forever:
                # if the panel/dispatcher never processes (e.g. closed), time out
                # and reject (fail-closed) rather than hang the client thread.
                notified = event.wait(timeout=300.0)
                
                pending = self._pending_executions.pop(req_uid, None)
                if not notified:
                    self._send_error(conn, req_id, -32603,
                                     f"Tool '{name}' approval timed out (300s).")
                    return
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
                # Direct callback for synchronous environments (e.g. unit tests).
                # FAIL-CLOSED: with no approval mechanism wired, a modifying tool
                # must be rejected -- never silently execute (e.g. run_python_snippet
                # = arbitrary code) just because nobody installed a gate.
                if self.approval_callback:
                    try:
                        approved = self.approval_callback(name, arguments)
                    except Exception as e:
                        _log.error(f"Approval callback failed: {e}")
                        approved = False
                else:
                    _log.warning(
                        f"Rejecting modifying tool '{name}': no approval_callback "
                        "configured (fail-closed)."
                    )
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

        # FAIL-CLOSED: default to rejected unless an approval callback explicitly
        # approves. A missing callback must never green-light a modifying tool.
        approved = False
        if self.approval_callback:
            try:
                approved = self.approval_callback(name, arguments)
            except Exception as e:
                _log.error(f"Approval callback failed: {e}")
                approved = False
        else:
            _log.warning(
                f"Rejecting modifying tool '{name}' on main thread: "
                "no approval_callback configured (fail-closed)."
            )

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
