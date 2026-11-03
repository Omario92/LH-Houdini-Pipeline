"""
Tests for the external MCP bridge (scripts/lh_mcp_stdio.py) against the
in-Houdini MCP server (tools/houdini_ai_assistant/mcp/server.py).

Run from the project root:

    python test_mcp_bridge.py

Notes:
    * Pure credential tests always run.
    * Server tests need PySide6/PySide2 (the server is a QObject); they SKIP
      otherwise.
    * Real Windows named pipes (AF_PIPE) cannot run on POSIX. The pipe code
      path is exercised with AF_UNIX instead; this validates framing and the
      authkey handshake, NOT Windows pipe behaviour. Tools are dummies: no
      hou calls happen, so nothing here validates behaviour inside Houdini.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from lh_houdini_pipeline.tools.houdini_ai_assistant.mcp import auth  # noqa: E402

PASS = "\033[32mOK\033[0m"
FAIL = "\033[31mFAIL\033[0m"
SKIP = "\033[33mSKIP\033[0m"
errors: List[Any] = []
TMP = Path(tempfile.mkdtemp(prefix="lh-mcp-test-"))
BRIDGE = ROOT / "scripts" / "lh_mcp_stdio.py"


class _Skip(Exception):
    """Raised when an optional runtime is unavailable."""


def check(label: str, fn: Any) -> None:
    """Run one test and print its status."""
    try:
        fn()
        print("  " + label.ljust(50) + " " + PASS)
    except _Skip as s:
        print("  " + label.ljust(50) + " " + SKIP + "  " + str(s))
    except Exception as e:  # noqa: BLE001
        print("  " + label.ljust(50) + " " + FAIL + "  " + repr(e))
        errors.append((label, e))


def _require_qt() -> None:
    try:
        import PySide6  # noqa: F401
    except ImportError:
        try:
            import PySide2  # noqa: F401
        except ImportError:
            raise _Skip("PySide not installed")


def _load_bridge() -> Any:
    spec = importlib.util.spec_from_file_location("lh_mcp_stdio", str(BRIDGE))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _make_server() -> Any:
    """Server with one read-only and one gated dummy tool (no hou)."""
    from lh_houdini_pipeline.tools.houdini_ai_assistant.mcp.server import McpTcpServer
    from lh_houdini_pipeline.tools.houdini_ai_assistant.tools.base import AITool

    class Echo(AITool):
        name = "echo"
        description = "echo"
        schema = {"type": "object"}
        read_only = True

        def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
            return {"success": True, "echo": arguments.get("v")}

    class Mutate(AITool):
        name = "create_node"
        description = "gated"
        schema = {"type": "object"}
        calls: List[Any] = []

        def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
            Mutate.calls.append(arguments)
            return {"success": True}

    server = McpTcpServer()
    server._tools = [Echo(), Mutate()]
    server.use_thread_dispatch = False
    server.approval_callback = lambda name, args: False  # artist rejects
    server.mutate_calls = Mutate.calls
    return server


# ---------------------------------------------------------------------------
print("\n=== Credential (pure) ===")


def _test_default_path_parity() -> None:
    bridge = _load_bridge()
    cases = [
        {"LH_MCP_AUTH_FILE": str(TMP / "x.json"), "LOCALAPPDATA": "C:/L", "TEMP": "C:/T"},
        {"LOCALAPPDATA": "C:/Users/ADMIN/AppData/Local", "TEMP": "C:/T"},
        {"TEMP": str(TMP)},
    ]
    for env in cases:
        clean = {k: v for k, v in os.environ.items()
                 if k not in ("LH_MCP_AUTH_FILE", "LOCALAPPDATA", "TEMP")}
        clean.update(env)
        with patch.dict(os.environ, clean, clear=True):
            assert auth.default_auth_file() == bridge._default_auth_file(), env
    with patch.dict(os.environ, {"LOCALAPPDATA": "C:/Users/ADMIN/AppData/Local"}, clear=True):
        assert auth.default_auth_file().as_posix() == \
            "C:/Users/ADMIN/AppData/Local/LH-Houdini-Pipeline/mcp-auth.json"

check("server/bridge resolve the same default auth file", _test_default_path_parity)


def _test_credential_roundtrip() -> None:
    path = TMP / "sub" / "mcp-auth.json"
    tok = auth.generate_token()
    assert len(tok) >= 40 and tok != auth.generate_token()
    auth.write_credential(path, tok, pipe=auth.DEFAULT_PIPE, port=14848)
    rec = auth.read_credential(path)
    assert rec["token"] == tok and rec["pipe"] == auth.DEFAULT_PIPE and rec["port"] == 14848
    # The bridge's own validator accepts the record.
    assert _load_bridge().HoudiniBridge(auth_file=str(path))._read_credential()["token"] == tok
    # Another session's token must not delete our file.
    assert auth.remove_credential(path, "other") is False and path.exists()
    assert auth.remove_credential(path, tok) is True and not path.exists()
    assert auth.read_credential(path) is None
    assert auth.tokens_match(tok, tok) and not auth.tokens_match(tok, None)
    assert not auth.tokens_match("", "")

check("credential write/read/remove + token compare", _test_credential_roundtrip)


# ---------------------------------------------------------------------------
print("\n=== Bridge subprocess <-> server (TCP fallback) ===")


def _bridge_exchange(args: List[str], messages: List[Dict[str, Any]]) -> Dict[Any, Dict[str, Any]]:
    """Run the bridge CLI exactly like an MCP client would; map id -> reply.

    Requests are fed one at a time (reply read before the next) because the
    bridge stops at stdin EOF and does not wait for in-flight requests.
    """
    out: Dict[Any, Dict[str, Any]] = {}
    proc = subprocess.Popen(
        [sys.executable, str(BRIDGE)] + args,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        for msg in messages:
            proc.stdin.write(json.dumps(msg) + "\n")
            proc.stdin.flush()
            if "id" in msg:
                reply = json.loads(proc.stdout.readline())  # stdout is JSON-RPC only
                out[reply.get("id")] = reply
        proc.stdin.close()
        rest = proc.stdout.read()
        assert not rest.strip(), "unexpected extra stdout: " + rest  # no reply to notifications
        proc.wait(timeout=30)
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.stdout.close()
        proc.stderr.close()
    return out


_MCP_SESSION = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"}}},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
     "params": {"name": "echo", "arguments": {"v": "hi"}}},
    {"jsonrpc": "2.0", "id": "c4", "method": "tools/call",
     "params": {"name": "create_node", "arguments": {"parent": "/obj"}}},
]


def _test_bridge_tcp_session() -> None:
    _require_qt()
    server = _make_server()
    port = _free_port()
    cred = TMP / "tcp-auth.json"
    assert server.start(port=port, auth_file=str(cred))
    try:
        assert cred.exists(), "start() must write the credential file"
        r = _bridge_exchange(["--tcp", "--port", str(port), "--auth-file", str(cred)], _MCP_SESSION)
        assert r[1]["result"]["serverInfo"]["name"] == "LH-Houdini-AI-Server"
        names = [t["name"] for t in r[2]["result"]["tools"]]
        assert names == ["echo", "create_node"], names
        body = json.loads(r[3]["result"]["content"][0]["text"])
        assert body["echo"] == "hi" and r[3]["result"]["isError"] is False
        # Gated tool: approval rejected -> isError result, tool never ran.
        assert r["c4"]["result"]["isError"] is True
        assert "rejected" in r["c4"]["result"]["content"][0]["text"]
        assert server.mutate_calls == []
    finally:
        server.stop()
    assert not cred.exists(), "stop() must remove the credential file"

check("initialize/list/call over bridge (authenticated TCP)", _test_bridge_tcp_session)


def _test_bridge_rejects_bad_credentials() -> None:
    _require_qt()
    server = _make_server()
    port = _free_port()
    cred = TMP / "tcp-auth2.json"
    assert server.start(port=port, auth_file=str(cred))
    try:
        bad = TMP / "wrong.json"
        auth.write_credential(bad, "not-the-token")
        req = [{"jsonrpc": "2.0", "id": 9, "method": "tools/list"}]
        r = _bridge_exchange(["--tcp", "--port", str(port), "--auth-file", str(bad)], req)
        assert r[9]["error"]["code"] == -32001 and "rejected" in r[9]["error"]["message"], r
        r = _bridge_exchange(["--tcp", "--port", str(port), "--auth-file", str(TMP / "missing.json")], req)
        assert "credential" in r[9]["error"]["message"].lower(), r
        # A raw client that skips the handshake gets nothing but a denial.
        with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
            s.sendall(b'{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n')
            reply = s.makefile("r").readline()
        assert json.loads(reply) == {"lhAuth": "denied"}, reply
    finally:
        server.stop()

check("wrong/missing token and no handshake are refused", _test_bridge_rejects_bad_credentials)


# ---------------------------------------------------------------------------
print("\n=== Pipe code path (AF_UNIX stand-in for AF_PIPE) ===")


def _test_pipe_path_with_bridge() -> None:
    _require_qt()
    if not hasattr(socket, "AF_UNIX"):
        raise _Skip("AF_UNIX unavailable")
    from multiprocessing import AuthenticationError
    from multiprocessing import connection as mpc
    import lh_houdini_pipeline.tools.houdini_ai_assistant.mcp.server as srv

    sock_path = str(TMP / "lh-mcp.sock")
    cred = TMP / "pipe-auth.json"
    server = _make_server()
    with patch.object(srv, "_PIPE_FAMILY", "AF_UNIX"):
        assert server.start(port=_free_port(), pipe_name=sock_path, auth_file=str(cred))
        try:
            assert auth.read_credential(cred)["pipe"] == sock_path

            # Wrong authkey is refused by the multiprocessing challenge.
            try:
                mpc.Client(sock_path, family="AF_UNIX", authkey=b"wrong")
                raise AssertionError("pipe accepted a wrong authkey")
            except AuthenticationError:
                pass

            bridge_mod = _load_bridge()
            real_client = bridge_mod.Client

            def unix_client(address: str, family: str = "", authkey: bytes = b"") -> Any:
                assert family == "AF_PIPE"  # what the bridge uses on Windows
                return real_client(address, family="AF_UNIX", authkey=authkey)

            with patch.object(bridge_mod, "Client", unix_client):
                b = bridge_mod.HoudiniBridge(pipe_name=sock_path, auth_file=str(cred))
                try:
                    init = b.request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
                    assert "result" in init, init
                    b.notify({"jsonrpc": "2.0", "method": "notifications/initialized"})
                    tools = b.request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
                    assert len(tools["result"]["tools"]) == 2
                    call = b.request({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                      "params": {"name": "echo", "arguments": {"v": 5}}})
                    assert json.loads(call["result"]["content"][0]["text"])["echo"] == 5
                finally:
                    b.close()
        finally:
            server.stop()
    assert not server.is_running() and not cred.exists()

check("bridge pipe framing + authkey against server", _test_pipe_path_with_bridge)


def _test_failed_start_writes_nothing() -> None:
    _require_qt()
    port = _free_port()
    blocker = socket.socket()
    blocker.bind(("127.0.0.1", port))
    blocker.listen(1)
    cred = TMP / "never.json"
    try:
        server = _make_server()
        assert server.start(port=port, auth_file=str(cred)) is False
        assert not server.is_running() and not cred.exists()
    finally:
        blocker.close()

check("failed start leaves no credential / listener", _test_failed_start_writes_nothing)


# ---------------------------------------------------------------------------
shutil.rmtree(TMP, ignore_errors=True)
print("\n=== Summary ===")
if errors:
    print(f"{len(errors)} tests failed:")
    for label, exc in errors:
        print(f"  - {label}: {exc!r}")
    sys.exit(1)
print("  All MCP bridge assertions passed.")
sys.exit(0)
