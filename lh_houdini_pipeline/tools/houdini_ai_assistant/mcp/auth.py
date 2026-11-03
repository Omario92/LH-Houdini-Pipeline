"""
lh_houdini_pipeline.tools.houdini_ai_assistant.mcp.auth
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Credential record shared between the in-Houdini MCP server and the external
``scripts/lh_mcp_stdio.py`` bridge.

The server generates a fresh random token every time it starts and writes it
to a user-local JSON file. The bridge reads that file on each connect and
proves possession of the token (named pipe: ``multiprocessing`` authkey
challenge; TCP: an ``{"lhAuth": token}`` first line).

Pure standard library -- no ``hou``, no Qt -- so it is unit-testable outside
Houdini. The default path resolution MUST stay identical to
``_default_auth_file()`` in ``scripts/lh_mcp_stdio.py``.
"""

from __future__ import annotations

import hmac
import json
import os
import secrets
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_PIPE = r"\\.\pipe\lh-houdini-mcp"
"""Windows named-pipe endpoint used by default (matches the bridge)."""

AUTH_ENV_VAR = "LH_MCP_AUTH_FILE"
"""Environment variable that overrides the credential file location."""


def default_auth_file() -> Path:
    """Return the user-local credential file path.

    Resolution order (same as the bridge): ``$LH_MCP_AUTH_FILE``, then
    ``%LOCALAPPDATA%/LH-Houdini-Pipeline/mcp-auth.json``, then
    ``$TEMP/lh-houdini-mcp-auth.json`` (or the current directory).

    Returns:
        Path of the credential file (it may not exist yet).
    """
    override = os.environ.get(AUTH_ENV_VAR)
    if override:
        return Path(override)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "LH-Houdini-Pipeline" / "mcp-auth.json"
    return Path(os.environ.get("TEMP") or ".") / "lh-houdini-mcp-auth.json"


def generate_token() -> str:
    """Return a new URL-safe random token (256 bits).

    Returns:
        The token string.
    """
    return secrets.token_urlsafe(32)


def tokens_match(expected: str, candidate: Any) -> bool:
    """Compare a presented token with the expected one in constant time.

    Args:
        expected: The server's current token.
        candidate: Value presented by the client (any type).

    Returns:
        ``True`` only when *candidate* is a string equal to *expected*.
    """
    if not isinstance(candidate, str) or not expected:
        return False
    return hmac.compare_digest(expected.encode("utf-8"), candidate.encode("utf-8"))


def write_credential(path: Path, token: str, **info: Any) -> Path:
    """Atomically write the credential record, readable by the user only.

    Args:
        path: Destination file; parent directories are created.
        token: Secret token for this server run.
        **info: Extra JSON-serialisable metadata (pipe name, port, pid...).

    Returns:
        The written path.

    Raises:
        OSError: If the directory or file cannot be written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record: Dict[str, Any] = {"token": token, "created": time.time(), "pid": os.getpid()}
    record.update(info)
    fd, tmp = tempfile.mkstemp(prefix=".mcp-auth-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2)
        try:
            os.chmod(tmp, 0o600)  # best effort; Windows only honours read-only bit
        except OSError:
            pass
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


def read_credential(path: Path) -> Optional[Dict[str, Any]]:
    """Read a credential record, returning ``None`` when absent or malformed.

    Args:
        path: Credential file path.

    Returns:
        The record dict (with a string ``token``) or ``None``.
    """
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(value, dict) or not isinstance(value.get("token"), str):
        return None
    return value


def remove_credential(path: Path, token: str) -> bool:
    """Delete the credential file, but only if it still holds *token*.

    Prevents one Houdini session from deleting the credential another
    session wrote after it.

    Args:
        path: Credential file path.
        token: The token this server wrote.

    Returns:
        ``True`` if the file was removed.
    """
    record = read_credential(path)
    if record is None or not tokens_match(token, record.get("token")):
        return False
    try:
        Path(path).unlink()
        return True
    except OSError:
        return False
