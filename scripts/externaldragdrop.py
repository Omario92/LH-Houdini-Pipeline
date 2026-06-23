"""
externaldragdrop.py
~~~~~~~~~~~~~~~~~~~~
Houdini external (OS) drag-and-drop handler -- drop FBX/OBJ/ABC/USD from the
file browser onto a Solaris (LOP) network and have it auto-built into a USD
component via the Asset Ingestion pipeline (Rebelway Week 10).

Houdini contract
----------------
Houdini scans every ``scripts/`` directory on ``HOUDINI_PATH`` for a module
named ``externaldragdrop`` and, on an external drop, calls ``dropAccept(files)``
with a list of dropped paths.  Returning ``True`` marks the drop as handled
(Houdini does nothing further); ``False`` lets Houdini fall back to its default
behaviour.

Install
-------
Put this repo's ``scripts/`` dir on ``HOUDINI_PATH`` (e.g. via a Houdini package
JSON).  ``drop_accept`` is provided as an alias to match the course naming.
"""

from __future__ import annotations

import os
import sys
import traceback


def _ensure_package_on_path() -> None:
    """Make ``lh_houdini_pipeline`` importable regardless of how Houdini started.

    This file lives at ``<repo>/scripts/externaldragdrop.py``; the package root
    is the repo dir one level up.  We add it to ``sys.path`` if needed so the
    handler works even when only ``scripts/`` is on HOUDINI_PATH.
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


# Geometry extensions this handler claims (compound .bgeo.sc handled in core).
_ACCEPT_EXTS = (
    ".fbx", ".obj", ".abc", ".usd", ".usda", ".usdc", ".usdz",
    ".bgeo", ".sc", ".ply", ".stl",
)


def dropAccept(files):  # noqa: N802 -- Houdini-mandated callback name
    """Houdini external-drop callback.

    Args:
        files: List of dropped file/folder path strings.

    Returns:
        ``True`` if we ingested the drop (handled), ``False`` to defer to
        Houdini's default handling.
    """
    if not files:
        return False

    # Quick pre-filter (no hou needed): do any dropped paths look like geometry?
    # Folders are accepted too -- the ingest core expands them.
    def _looks_geo(p: str) -> bool:
        if os.path.isdir(p):
            return True
        return os.path.splitext(p.lower())[1] in _ACCEPT_EXTS

    if not any(_looks_geo(f) for f in files):
        return False

    import hou  # safe: only reached for a geometry drop inside Houdini

    try:
        _ensure_package_on_path()
        from lh_houdini_pipeline.tools.asset_ingest import service as _svc

        # Only hijack the drop when the artist is in Solaris; otherwise let
        # Houdini do its normal thing (e.g. import into /obj).
        if not _svc.is_solaris_context():
            return False

        summary = _svc.ingest_paths(list(files), parent_path="/stage")
        if not summary.results:
            return False  # nothing ingestable -> let Houdini handle it

        ok, bad = len(summary.succeeded), len(summary.failed)
        msg = "Ingested " + str(ok) + " asset(s)."
        if bad:
            msg += "  " + str(bad) + " failed (see console)."
        hou.ui.setStatusMessage(msg, severity=hou.severityType.Message)
        return True

    except Exception as exc:  # noqa: BLE001 -- never let a drop crash Houdini
        traceback.print_exc()
        try:
            hou.ui.displayMessage(
                "Asset ingest drag-drop failed:\n" + str(exc),
                severity=hou.severityType.Error,
            )
        except Exception:  # noqa: BLE001
            pass
        return False


# Course-compatibility alias (some material refers to ``drop_accept``).
drop_accept = dropAccept
