"""
lh_houdini_pipeline.core.validators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Reusable validation helpers for pipeline data.

Planned validators:
    * Path existence / extension checks
    * Version string format validation
    * USD prim path validation
    * Frame-range sanity checks
    * Config schema validation (via jsonschema or manual)

Stub -- to be implemented.
"""

from __future__ import annotations


def validate_path_exists(path: str) -> bool:
    """Return True if *path* exists on disk."""
    from pathlib import Path
    return Path(path).exists()


def validate_extension(path: str, *allowed: str) -> bool:
    """Return True if *path* has one of the *allowed* extensions (case-insensitive)."""
    from pathlib import Path
    return Path(path).suffix.lstrip(".").lower() in {e.lstrip(".").lower() for e in allowed}
