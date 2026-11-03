#!/usr/bin/env python
"""
Concurrent MCP stdio bridge for an active LH Houdini session.

The client owns this lightweight stdio process while Houdini independently
hosts the tool executor over private local IPC.  Windows named pipe is the
production default; authenticated loopback TCP remains a migration fallback.

The bridge is pure standard library and runs on Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
from multiprocessing.connection import Client
from pathlib import Path
from typing import Any, Callable, Dict, Optional


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 14848
DEFAULT_PIPE = r"\\.\pipe\lh-houdini-mcp"
CONNECT_TIMEOUT = 5.0
READ_TIMEOUT = 310.0
MAX_MESSAGE_BYTES = 4 * 1024 * 1024

_STDOUT_LOCK = threading.Lock()


def _log(message: str) -> None:
    """Write diagnostics to stderr, reserving stdout for MCP messages.

    Args:
        message: Text to log.
    """

    sys.stderr.write("[lh-mcp-bridge] " + message + "\n")
    sys.stderr.flush()


def _write_message(payload: Dict[str, Any]) -> None:
    """Emit one newline-delimited JSON-RPC message.

    Args:
        payload: JSON-serialisable message.
    """

    line = json.dumps(payload) + "\n"
    with _STDOUT_LOCK:
        sys.stdout.write(line)
        sys.stdout.flush()


def _error_response(req_id: Any, code: int, message: str) -> Dict[str, Any]:
    """Build a JSON-RPC error response.

    Args:
        req_id: Original string or numeric request ID.
        code: JSON-RPC error code.
        message: Human-readable error.

    Returns:
        A JSON-RPC error response.
    """

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    }


def _normalise_reply(raw_reply: Any, req_id: Any) -> Dict[str, Any]:
    """Coerce a Houdini reply into a schema-valid JSON-RPC response.

    Args:
        raw_reply: Decoded reply from Houdini.
        req_id: Request ID expected by the client.

    Returns:
        A response carrying the expected ID and exactly one result/error.
    """

    if not isinstance(raw_reply, dict):
        return _error_response(
            req_id,
            -32603,
            "Houdini sent a non-object reply: " + repr(raw_reply)[:200],
        )
    if "result" not in raw_reply and "error" not in raw_reply:
        if raw_reply.get("status") == "error" or "message" in raw_reply:
            return _error_response(
                req_id,
                -32001,
                str(raw_reply.get("message") or "Houdini reported an error."),
            )
        return _error_response(
            req_id,
            -32603,
            "Houdini reply had neither 'result' nor 'error': "
            + json.dumps(raw_reply)[:200],
        )
    reply = dict(raw_reply)
    reply["jsonrpc"] = "2.0"
    reply["id"] = req_id
    if "result" in reply and "error" in reply:
        del reply["result"]
    return reply


def _default_auth_file() -> Path:
    """Return the user-local credential file path."""

    override = os.environ.get("LH_MCP_AUTH_FILE")
    if override:
        return Path(override)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "LH-Houdini-Pipeline" / "mcp-auth.json"
    return Path(os.environ.get("TEMP") or ".") / "lh-houdini-mcp-auth.json"


def _request_key(req_id: Any) -> str:
    """Return a stable dictionary key for a JSON-RPC request ID."""

    return json.dumps(req_id, sort_keys=True, separators=(",", ":"))


class _PendingReply:
    """Thread-safe state for one in-flight request."""

    def __init__(self) -> None:
        """Create an unresolved reply."""

        self.event = threading.Event()
        self.reply: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.cancelled = False


class HoudiniBridge:
    """Concurrent request-correlating bridge to Houdini private IPC."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        *,
        pipe_name: Optional[str] = None,
        auth_file: Optional[str] = None,
    ) -> None:
        """Store transport configuration without connecting.

        Args:
            host: Loopback host for TCP fallback.
            port: Loopback port for TCP fallback.
            pipe_name: Windows named-pipe endpoint. When provided, pipe mode
                takes precedence over TCP.
            auth_file: Credential record produced by the Houdini panel.
                ``None`` preserves unauthenticated fake-server unit tests.
        """

        self.host = host
        self.port = int(port)
        self.pipe_name = pipe_name
        self.auth_file = Path(auth_file) if auth_file else None
        self.notification_callback: Optional[
            Callable[[Dict[str, Any]], None]
        ] = None
        self._connection: Any = None
        self._connection_generation = 0
        self._reader_thread: Optional[threading.Thread] = None
        self._socket_buffer = b""
        self._pending: Dict[str, _PendingReply] = {}
        self._state_lock = threading.RLock()
        self._send_lock = threading.Lock()
        self._connect_lock = threading.Lock()
        self._request_threads: set[threading.Thread] = set()

    def connect(self) -> None:
        """Connect and start the response reader.

        Raises:
            OSError: If Houdini or the credential file is unavailable.
            ValueError: If the credential record is malformed.
        """

        with self._connect_lock:
            with self._state_lock:
                if self._connection is not None:
                    return
            credential = self._read_credential()
            token = credential.get("token") if credential else None
            pipe_name = self.pipe_name
            if pipe_name:
                if not token:
                    raise OSError("Named-pipe authentication credential is unavailable.")
                connection = Client(
                    pipe_name,
                    family="AF_PIPE",
                    authkey=str(token).encode("utf-8"),
                )
                label = "named pipe"
            else:
                connection = socket.create_connection(
                    (self.host, self.port),
                    timeout=CONNECT_TIMEOUT,
                )
                if token:
                    self._authenticate_tcp(connection, str(token))
                connection.settimeout(None)
                label = self.host + ":" + str(self.port)

            with self._state_lock:
                self._connection = connection
                self._connection_generation += 1
                generation = self._connection_generation
                self._socket_buffer = b""
            reader = threading.Thread(
                target=self._reader_loop,
                args=(generation,),
                name="lh-mcp-bridge-reader",
                daemon=True,
            )
            self._reader_thread = reader
            reader.start()
            _log("connected to " + label)

    def close(self) -> None:
        """Close the active connection and release pending callers."""

        self._disconnect("Bridge connection closed.", expected_generation=None)

    def request(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Forward one request and wait for its correlated response.

        Args:
            message: JSON-RPC request or notification.

        Returns:
            A response mapping, or ``None`` for notifications.
        """

        req_id = message.get("id")
        if req_id is None:
            self.notify(message)
            return None
        pending = _PendingReply()
        key = _request_key(req_id)
        try:
            self.connect()
        except (OSError, ValueError) as exc:
            return self._offline_error(req_id, exc)

        with self._state_lock:
            if key in self._pending:
                return _error_response(req_id, -32600, "Duplicate in-flight request ID.")
            self._pending[key] = pending
        try:
            self._send(message)
        except (OSError, ConnectionError) as exc:
            with self._state_lock:
                self._pending.pop(key, None)
            self._disconnect(str(exc), expected_generation=None)
            return _error_response(req_id, -32001, "Lost connection to Houdini: " + str(exc))

        if not pending.event.wait(READ_TIMEOUT):
            with self._state_lock:
                self._pending.pop(key, None)
            self.notify(
                {
                    "jsonrpc": "2.0",
                    "method": "notifications/cancelled",
                    "params": {
                        "requestId": req_id,
                        "reason": "Bridge request timeout.",
                    },
                }
            )
            return _error_response(req_id, -32001, "Timed out waiting for Houdini.")
        if pending.error:
            return _error_response(req_id, -32001, pending.error)
        if pending.cancelled:
            return None
        return _normalise_reply(pending.reply, req_id)

    def notify(self, message: Dict[str, Any]) -> None:
        """Forward a lifecycle/cancellation notification without waiting.

        Args:
            message: JSON-RPC notification.
        """

        if message.get("method") == "notifications/cancelled":
            params = message.get("params", {})
            request_id = params.get("requestId") if isinstance(params, dict) else None
            if request_id is not None:
                key = _request_key(request_id)
                with self._state_lock:
                    pending = self._pending.pop(key, None)
                if pending is not None:
                    pending.cancelled = True
                    pending.event.set()
        try:
            self.connect()
            self._send(message)
        except (OSError, ValueError, ConnectionError) as exc:
            _log("notification not delivered: " + str(exc))

    def serve_forever(self) -> int:
        """Pump concurrent stdin requests until the client closes stdin.

        Returns:
            Process exit code ``0`` on clean shutdown.
        """

        self.notification_callback = _write_message
        target = self.pipe_name or (self.host + ":" + str(self.port))
        _log("bridge ready (target " + target + ")")
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                text = line.strip()
                if not text:
                    continue
                try:
                    message = json.loads(text)
                except ValueError as exc:
                    _log("dropping unparseable line: " + str(exc))
                    continue
                if not isinstance(message, dict):
                    _log("dropping non-object message: " + type(message).__name__)
                    continue
                if message.get("id") is None:
                    if "method" not in message:
                        _log("dropping message with neither id nor method")
                    else:
                        self.notify(message)
                    continue
                self._start_stdio_request(message)
        except KeyboardInterrupt:
            pass
        finally:
            self.close()
            _log("bridge stopped")
        return 0

    def _start_stdio_request(self, message: Dict[str, Any]) -> None:
        """Start one request worker so stdin remains responsive.

        Args:
            message: JSON-RPC request.
        """

        def run() -> None:
            """Forward, emit, and untrack one request."""

            try:
                reply = self.request(message)
                if reply is not None:
                    _write_message(reply)
            finally:
                with self._state_lock:
                    self._request_threads.discard(threading.current_thread())

        thread = threading.Thread(
            target=run,
            name="lh-mcp-stdio-request",
            daemon=True,
        )
        with self._state_lock:
            self._request_threads.add(thread)
        thread.start()

    def _reader_loop(self, generation: int) -> None:
        """Read and correlate responses/notifications for one connection."""

        try:
            while True:
                payload = self._receive()
                if not payload:
                    raise ConnectionError("Houdini closed the connection.")
                try:
                    message = json.loads(payload.decode("utf-8").strip())
                except ValueError as exc:
                    raise ConnectionError("Malformed Houdini reply: " + str(exc)) from exc
                if not isinstance(message, dict):
                    raise ConnectionError("Houdini sent a non-object message.")
                if "id" not in message:
                    callback = self.notification_callback
                    if callback is not None:
                        callback(message)
                    continue
                key = _request_key(message.get("id"))
                with self._state_lock:
                    pending = self._pending.pop(key, None)
                if pending is None:
                    _log("dropping unmatched response id " + key)
                    continue
                pending.reply = message
                pending.event.set()
        except (OSError, EOFError, ConnectionError) as exc:
            self._disconnect(str(exc), expected_generation=generation)

    def _send(self, message: Dict[str, Any]) -> None:
        """Send one framed message over the active transport."""

        encoded = (json.dumps(message) + "\n").encode("utf-8")
        if len(encoded) > MAX_MESSAGE_BYTES:
            raise OSError("MCP message exceeds the private IPC size limit.")
        with self._send_lock:
            with self._state_lock:
                connection = self._connection
            if connection is None:
                raise ConnectionError("Bridge is disconnected.")
            if self.pipe_name:
                connection.send_bytes(encoded)
            else:
                connection.sendall(encoded)

    def _receive(self) -> bytes:
        """Receive one framed message from the active transport."""

        with self._state_lock:
            connection = self._connection
        if connection is None:
            raise ConnectionError("Bridge is disconnected.")
        if self.pipe_name:
            return connection.recv_bytes(MAX_MESSAGE_BYTES)
        while b"\n" not in self._socket_buffer:
            chunk = connection.recv(65536)
            if not chunk:
                raise ConnectionError("Houdini closed the connection.")
            self._socket_buffer += chunk
            if len(self._socket_buffer) > MAX_MESSAGE_BYTES:
                raise ConnectionError("Houdini reply exceeds the size limit.")
        line, self._socket_buffer = self._socket_buffer.split(b"\n", 1)
        return line

    def _disconnect(
        self,
        reason: str,
        *,
        expected_generation: Optional[int],
    ) -> None:
        """Close one connection generation and fail pending requests."""

        with self._state_lock:
            if (
                expected_generation is not None
                and expected_generation != self._connection_generation
            ):
                return
            connection = self._connection
            self._connection = None
            pending = list(self._pending.values())
            self._pending.clear()
        if connection is not None:
            try:
                connection.close()
            except OSError:
                pass
        for state in pending:
            state.error = reason
            state.event.set()

    def _read_credential(self) -> Dict[str, Any]:
        """Read and validate the Houdini-produced credential record."""

        if self.auth_file is None:
            return {}
        try:
            value = json.loads(self.auth_file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise OSError(
                "Cannot read Houdini MCP credential file '"
                + str(self.auth_file)
                + "': "
                + str(exc)
            ) from exc
        if not isinstance(value, dict) or not isinstance(value.get("token"), str):
            raise ValueError("Houdini MCP credential record is malformed.")
        return value

    def _authenticate_tcp(self, connection: socket.socket, token: str) -> None:
        """Perform the private TCP fallback token handshake."""

        connection.settimeout(CONNECT_TIMEOUT)
        connection.sendall(
            (json.dumps({"lhAuth": token}) + "\n").encode("utf-8")
        )
        buffer = b""
        while b"\n" not in buffer and len(buffer) <= 4096:
            chunk = connection.recv(4096)
            if not chunk:
                raise OSError("Houdini closed during TCP authentication.")
            buffer += chunk
        response = json.loads(buffer.split(b"\n", 1)[0].decode("utf-8"))
        if not isinstance(response, dict) or response.get("lhAuth") != "ok":
            raise OSError("Houdini rejected the TCP authentication token.")

    def _offline_error(self, req_id: Any, exc: BaseException) -> Dict[str, Any]:
        """Build the user-facing offline response."""

        return _error_response(
            req_id,
            -32001,
            "Cannot reach the Houdini MCP server ("
            + str(exc)
            + "). Open Houdini and start the 'LH Pipeline > Houdini MCP' "
            "shelf tool.",
        )


def main(argv: Optional[list] = None) -> int:
    """Run the stdio bridge CLI.

    Args:
        argv: Arguments excluding the executable name.

    Returns:
        Process exit code.
    """

    parser = argparse.ArgumentParser(
        description="MCP stdio bridge to a running Houdini MCP server."
    )
    transport = parser.add_mutually_exclusive_group()
    transport.add_argument(
        "--pipe",
        default=None,
        help="Windows named-pipe endpoint (production default).",
    )
    transport.add_argument(
        "--tcp",
        action="store_true",
        help="Use authenticated loopback TCP fallback.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="TCP fallback host.")
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="TCP fallback port.",
    )
    parser.add_argument(
        "--auth-file",
        default=str(_default_auth_file()),
        help="Credential record written by the Houdini panel.",
    )
    args = parser.parse_args(argv)

    pipe_name = args.pipe
    if not args.tcp and pipe_name is None and os.name == "nt":
        pipe_name = DEFAULT_PIPE
    return HoudiniBridge(
        args.host,
        args.port,
        pipe_name=pipe_name,
        auth_file=args.auth_file,
    ).serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
