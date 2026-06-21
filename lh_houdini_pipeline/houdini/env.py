"""
lh_houdini_pipeline.houdini.env
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Houdini environment variable helpers and session-context accessors.

Provides safe wrappers around ``hou.getenv`` / ``hou.hscriptExpression``
and a ``HoudiniContext`` dataclass that snapshots the current session's
key paths ($HIP, $JOB, $HFS, etc.) for use by the resolver layer.

Stub -- to be implemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class HoudiniContext:
    """Snapshot of key Houdini environment paths for the current session.

    Attributes:
        hip:     Path to the current HIP file directory ($HIP).
        hipname: Current HIP filename without extension ($HIPNAME).
        job:     Project job root ($JOB).
        hfs:     Houdini install root ($HFS).
        hip_file: Full path to the current HIP file.
    """
    hip:      str = ""
    hipname:  str = ""
    job:      str = ""
    hfs:      str = ""
    hip_file: str = ""


def get_context() -> HoudiniContext:
    """Return a :class:`HoudiniContext` for the current Houdini session.

    Raises:
        ImportError: If called outside of a Houdini Python session.
    """
    import hou  # noqa: PLC0415
    return HoudiniContext(
        hip=hou.getenv("HIP", ""),
        hipname=hou.getenv("HIPNAME", ""),
        job=hou.getenv("JOB", ""),
        hfs=hou.getenv("HFS", ""),
        hip_file=hou.hipFile.path(),
    )


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Safe wrapper around ``hou.getenv`` with a default.

    Args:
        key:     Houdini environment variable name (without ``$``).
        default: Returned when the variable is not set.
    """
    import hou  # noqa: PLC0415
    value = hou.getenv(key)
    return value if value is not None else default
