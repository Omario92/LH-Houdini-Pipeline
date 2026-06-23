"""
lh_houdini_pipeline.tools.asset_ingest
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Drag-and-drop / batch ingestion: FBX/OBJ/ABC/USD -> USD component asset.

Composition (no monolith):

    core                    -> pure ingest planning (names, textures, expand)
    lops_asset_builder      -> the actual USD component build (reused)
    service                 -> batch orchestration + Solaris-context guard
    ui                      -> compact PySide batch window
    scripts/externaldragdrop.py -> Houdini OS drag-drop hook (dropAccept)

Public surface
--------------
* Pure / testable: ``IngestItem``, ``plan_ingest``, ``derive_asset_name``,
  ``find_texture_folder``, ``is_geometry_file``, ``expand_inputs``
* Houdini: ``ingest_paths``, ``ingest_items``, ``is_solaris_context``,
  ``IngestResult``, ``IngestSummary``
* ``launch`` -- open the PySide UI (Houdini only)
"""

from __future__ import annotations

from lh_houdini_pipeline.tools.asset_ingest.core import (
    GEO_EXTS,
    IngestItem,
    derive_asset_name,
    expand_inputs,
    find_texture_folder,
    is_geometry_file,
    plan_ingest,
)
from lh_houdini_pipeline.tools.asset_ingest.service import (
    IngestResult,
    IngestSummary,
    ingest_items,
    ingest_paths,
    is_solaris_context,
)

__all__ = [
    "GEO_EXTS",
    "IngestItem",
    "plan_ingest",
    "derive_asset_name",
    "find_texture_folder",
    "is_geometry_file",
    "expand_inputs",
    "IngestResult",
    "IngestSummary",
    "ingest_items",
    "ingest_paths",
    "is_solaris_context",
    "launch",
]

_WINDOW = None


def launch(*args, **kwargs):
    """Open the Asset Ingestion window and return it (cached module-side)."""
    global _WINDOW
    from lh_houdini_pipeline.tools.asset_ingest import ui as _ui
    _WINDOW = _ui.launch()
    return _WINDOW
