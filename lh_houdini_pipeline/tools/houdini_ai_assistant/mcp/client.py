"""
lh_houdini_pipeline.tools.houdini_ai_assistant.mcp.client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Client logic for connecting to external Houdini MCP servers.
"""

from __future__ import annotations

import json
import socket
import urllib.parse
from typing import Any, Dict, List, Optional

import requests
from lh_houdini_pipeline.core.logger import get_logger

_log = get_logger(__name__)

from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.base import AITool


class McpClient:
    """A versatile Model Context Protocol client.

    Supports connecting to external MCP servers via TCP sockets or HTTP JSON-RPC.
    Allows the AI Assistant to discover and delegate tool executions.
    """

    def __init__(self, server_url: str) -> None:
        """
        Args:
            server_url: The connection string (e.g. 'tcp://localhost:14848' or 'http://localhost:8000').
        """
        self.server_url = server_url.strip()
        self.tools: List[Dict[str, Any]] = []
        self._is_connected = False
        
        # Parse transport mode
        parsed = urllib.parse.urlparse(self.server_url)
        self.transport = parsed.scheme if parsed.scheme in ("tcp", "http", "https") else "http"
        self.netloc = parsed.netloc or self.server_url

    def connect(self) -> bool:
        """Establish connection with the external MCP server and retrieve tool definitions."""
        try:
            if self.transport == "tcp":
                self._is_connected = self._connect_tcp()
            else:
                self._is_connected = self._connect_http()
            return self._is_connected
        except Exception as e:
            _log.error(f"Failed to connect to MCP server '{self.server_url}': {e}")
            self._is_connected = False
            return False

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return the cached list of tools retrieved from the server."""
        if not self._is_connected:
            self.connect()
        return self.tools

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an external tool and return the execution results.

        Args:
            name: The name of the tool to execute.
            arguments: Input parameters matching the tool's schema.
        """
        if not self._is_connected:
            if not self.connect():
                return {"success": False, "error": "Not connected to MCP server"}

        try:
            if self.transport == "tcp":
                return self._call_tool_tcp(name, arguments)
            else:
                return self._call_tool_http(name, arguments)
        except Exception as e:
            _log.error(f"Failed to call external MCP tool '{name}': {e}")
            return {"success": False, "error": str(e)}

    # -- TCP Socket Transport Implementation ---------------------------------

    def _connect_tcp(self) -> bool:
        """Perform handshake and query tool list over TCP socket."""
        try:
            host, port_str = self.netloc.split(":")
            port = int(port_str)
        except ValueError:
            host = self.netloc
            port = 14848

        try:
            with socket.create_connection((host, port), timeout=5) as s:
                # 1. Send initialize
                init_req = {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "LH-Houdini-AI-Client", "version": "1.0.0"}
                    },
                    "id": 1
                }
                s.sendall((json.dumps(init_req) + "\n").encode("utf-8"))
                
                # Read response
                f = s.makefile("r", encoding="utf-8")
                init_resp_line = f.readline()
                if not init_resp_line:
                    _log.error(f"TCP handshake failed: Empty response from {host}:{port}")
                    return False
                
                try:
                    init_resp = json.loads(init_resp_line)
                except json.JSONDecodeError as e:
                    _log.error(f"Malformed JSON handshake response from TCP server at {host}:{port}: {e}")
                    return False

                if "error" in init_resp:
                    _log.error(f"TCP Handshake error: {init_resp['error']}")
                    return False

                # 2. Query tools/list
                list_req = {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 2
                }
                s.sendall((json.dumps(list_req) + "\n").encode("utf-8"))
                
                list_resp_line = f.readline()
                if not list_resp_line:
                    _log.error(f"TCP list tools failed: Empty response from {host}:{port}")
                    return False
                
                try:
                    list_resp = json.loads(list_resp_line)
                except json.JSONDecodeError as e:
                    _log.error(f"Malformed JSON tools list response from TCP server at {host}:{port}: {e}")
                    return False

                if "error" in list_resp:
                    _log.error(f"TCP list tools returned error: {list_resp['error']}")
                    return False

                self.tools = list_resp.get("result", {}).get("tools", [])
                return True
        except socket.timeout:
            _log.error(f"TCP connection to {host}:{port} timed out (timeout=5s).")
            return False
        except (ConnectionRefusedError, ConnectionResetError) as e:
            _log.error(f"TCP connection to {host}:{port} refused or reset: {e}")
            return False
        except Exception as e:
            _log.error(f"TCP connection failed to {host}:{port}: {e}")
            return False

    def _call_tool_tcp(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool call over TCP socket connection."""
        try:
            host, port_str = self.netloc.split(":")
            port = int(port_str)
        except ValueError:
            host = self.netloc
            port = 14848

        try:
            with socket.create_connection((host, port), timeout=10) as s:
                # Re-initialize for this command transaction
                init_req = {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
                    "id": 1
                }
                s.sendall((json.dumps(init_req) + "\n").encode("utf-8"))
                
                f = s.makefile("r", encoding="utf-8")
                f.readline() # Read initialize response discard

                # Call tool
                call_req = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": name,
                        "arguments": arguments
                    },
                    "id": 2
                }
                s.sendall((json.dumps(call_req) + "\n").encode("utf-8"))
                
                call_resp_line = f.readline()
                if not call_resp_line:
                    return {"success": False, "error": "Empty socket response from server"}
                
                try:
                    resp = json.loads(call_resp_line)
                except json.JSONDecodeError as e:
                    return {"success": False, "error": f"Malformed JSON-RPC payload from server: {e}"}

                if "error" in resp:
                    return {"success": False, "error": resp["error"].get("message", "Unknown JSON-RPC error")}

                # Unpack MCP contents
                result = resp.get("result", {})
                content_list = result.get("content", [])
                is_error = result.get("isError", False)

                text_response = ""
                if content_list:
                    text_response = content_list[0].get("text", "")

                try:
                    # Try parsing as JSON first
                    parsed_res = json.loads(text_response)
                    if isinstance(parsed_res, dict):
                        return parsed_res
                except Exception:
                    pass

                return {"success": not is_error, "message": text_response}
        except socket.timeout:
            return {"success": False, "error": f"TCP command execution to {host}:{port} timed out (timeout=10s)."}
        except ConnectionError as e:
            return {"success": False, "error": f"TCP connection error to {host}:{port}: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error during TCP tool call: {e}"}

    # -- HTTP Transport Implementation ---------------------------------------

    def _connect_http(self) -> bool:
        """Perform handshake and query tool list over HTTP POST endpoints."""
        try:
            # 1. Initialize POST
            init_req = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "LH-Houdini-AI-Client", "version": "1.0.0"}
                },
                "id": 1
            }
            
            try:
                resp = requests.post(self.server_url, json=init_req, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    if "error" in data:
                        _log.error(f"HTTP Handshake error: {data['error']}")
                        return False
            except requests.Timeout:
                _log.error(f"HTTP connection to {self.server_url} timed out during handshake (timeout=5s).")
                return False
            except requests.RequestException as e:
                _log.debug(f"HTTP initialize request failed: {e}. Attempting direct tools/list query.")

            # 2. Query tools/list
            list_req = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 2
            }
            try:
                resp = requests.post(self.server_url, json=list_req, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    self.tools = data.get("result", {}).get("tools", [])
                    return True
                else:
                    _log.error(f"HTTP tools/list failed with status code {resp.status_code}")
                    return False
            except requests.Timeout:
                _log.error(f"HTTP connection to {self.server_url} timed out during tools list query (timeout=5s).")
                return False
            except json.JSONDecodeError as e:
                _log.error(f"Malformed JSON response from HTTP server at {self.server_url}: {e}")
                return False
            except requests.RequestException as e:
                _log.error(f"HTTP request failed: {e}")
                return False
        except Exception as e:
            _log.debug(f"HTTP connection failed to {self.server_url}: {e}")
            return False

    def _call_tool_http(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool call over HTTP POST."""
        call_req = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            },
            "id": 3
        }
        try:
            resp = requests.post(self.server_url, json=call_req, timeout=10)
            if resp.status_code != 200:
                return {"success": False, "error": f"HTTP error status code: {resp.status_code}"}

            try:
                data = resp.json()
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Malformed JSON response from HTTP server: {e}"}

            if "error" in data:
                return {"success": False, "error": data["error"].get("message", "Unknown HTTP JSON-RPC error")}

            result = data.get("result", {})
            content_list = result.get("content", [])
            is_error = result.get("isError", False)

            text_response = ""
            if content_list:
                text_response = content_list[0].get("text", "")

            try:
                parsed_res = json.loads(text_response)
                if isinstance(parsed_res, dict):
                    return parsed_res
            except Exception:
                pass

            return {"success": not is_error, "message": text_response}
        except requests.Timeout:
            return {"success": False, "error": f"HTTP command execution to {self.server_url} timed out (timeout=10s)."}
        except requests.RequestException as e:
            return {"success": False, "error": f"HTTP request failed to {self.server_url}: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error during HTTP tool call: {e}"}


class DelegatedMcpTool(AITool):
    """Dynamic AITool wrapper that delegates execution to an external MCP server."""

    def __init__(self, name: str, description: str, schema: Dict[str, Any], client: McpClient) -> None:
        self._name = name
        self._description = description
        self._schema = schema
        self._client = client

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def schema(self) -> Dict[str, Any]:
        return self._schema

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.call_tool(self._name, arguments)

