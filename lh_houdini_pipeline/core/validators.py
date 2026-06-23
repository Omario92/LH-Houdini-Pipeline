"""
lh_houdini_pipeline.core.validators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Reusable validation helpers for pipeline data.

Pure Python -- no ``hou``.  Validators come in two flavours per the project's
Error-Handling convention:

* ``validate_*`` / ``is_*``  -> return ``bool`` (cheap predicate).
* ``require_*``              -> raise :class:`ValidationError` with a clear,
                               actionable message (use at trust boundaries:
                               UI input, config, CLI args).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Tuple


class ValidationError(ValueError):
    """Raised by ``require_*`` validators when input is invalid."""


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def validate_path_exists(path: str) -> bool:
    """Return True if *path* exists on disk."""
    return Path(path).exists()


def validate_extension(path: str, *allowed: str) -> bool:
    """Return True if *path* has one of the *allowed* extensions (case-insensitive)."""
    suffix = Path(path).suffix.lstrip(".").lower()
    return suffix in {e.lstrip(".").lower() for e in allowed}


def require_extension(path: str, *allowed: str) -> str:
    """Return *path* unchanged if its extension is allowed, else raise.

    Raises:
        ValidationError: If the extension is not in *allowed*.
    """
    if not validate_extension(path, *allowed):
        raise ValidationError(
            "File '" + path + "' must have one of these extensions: "
            + ", ".join(allowed)
        )
    return path


# ---------------------------------------------------------------------------
# Version strings  (mirrors file.versioning's VersionFormat order: v### etc.)
# ---------------------------------------------------------------------------

# Accept: v1, v01, v001, V123, _v003 -- the formats VersionResolver understands.
_VERSION_RE = re.compile(r"(?:^|_)[vV](\d{1,4})$")


def is_version_token(token: str) -> bool:
    """Return True if *token* looks like a version tag (``v001``, ``_v3``...)."""
    return _VERSION_RE.search(token) is not None


def parse_version_number(token: str) -> Optional[int]:
    """Extract the integer version from a token, or ``None`` if not a version.

    Example::

        parse_version_number("v012")  -> 12
        parse_version_number("hero")  -> None
    """
    m = _VERSION_RE.search(token)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# USD prim paths
# ---------------------------------------------------------------------------

# A valid Sdf prim path: absolute, slash-separated, each segment a C-identifier
# (USD also allows a leading digit-free identifier; we enforce the common rule).
_PRIM_SEGMENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$")


def is_valid_prim_path(path: str) -> bool:
    """Return True if *path* is a syntactically valid absolute USD prim path.

    Checks: starts with ``/`` and every segment is a valid identifier.
    (Does not check existence on a stage -- that's a houdini-layer concern.)
    """
    if not path.startswith("/") or path == "/":
        return path == "/"  # "/" (the pseudo-root) is itself valid
    return all(_PRIM_SEGMENT_RE.match(seg) for seg in path.strip("/").split("/"))


def require_prim_path(path: str) -> str:
    """Return *path* if it is a valid prim path, else raise.

    Raises:
        ValidationError: With guidance on what a valid path looks like.
    """
    if not is_valid_prim_path(path):
        raise ValidationError(
            "'" + path + "' is not a valid USD prim path. Expected an absolute "
            "path of identifier segments, e.g. '/ASSET/geo' (no spaces, no "
            "leading digits, no hyphens)."
        )
    return path


# ---------------------------------------------------------------------------
# Frame ranges
# ---------------------------------------------------------------------------

def validate_frame_range(start: int, end: int, step: int = 1) -> bool:
    """Return True if (start, end, step) is a sane, non-empty frame range."""
    return step >= 1 and end >= start


def require_frame_range(start: int, end: int, step: int = 1) -> Tuple[int, int, int]:
    """Return ``(start, end, step)`` if valid, else raise.

    Raises:
        ValidationError: If step < 1 or end < start.
    """
    if step < 1:
        raise ValidationError("Frame step must be >= 1, got " + str(step) + ".")
    if end < start:
        raise ValidationError(
            "Frame range end (" + str(end) + ") is before start ("
            + str(start) + ")."
        )
    return (start, end, step)
