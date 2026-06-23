"""
lh_houdini_pipeline.tools.lookdev_builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
One-click lookdev: Asset + Light Rig + Turntable camera (Rebelway Week 10).

Composition (no monolith):

    lops_asset_builder  -> USD component asset
    asset_ingest.core   -> name/texture derivation from the geo file
    lookdev.light_rig   -> 3-point rig framed to the asset
    camera_manager      -> 360 turntable camera framed to the asset

Public surface
--------------
* Pure / testable: ``LookdevConfig``
* Houdini: ``build_lookdev`` / ``LookdevResult``
* ``launch`` -- open the PySide UI (Houdini only)
"""

from __future__ import annotations

from lh_houdini_pipeline.tools.lookdev_builder.core import LookdevConfig
from lh_houdini_pipeline.tools.lookdev_builder.service import (
    LookdevResult,
    build_lookdev,
)

__all__ = ["LookdevConfig", "LookdevResult", "build_lookdev", "launch"]

_WINDOW = None


def launch(*args, **kwargs):
    """Open the Lookdev Builder window and return it (cached module-side)."""
    global _WINDOW
    from lh_houdini_pipeline.tools.lookdev_builder import ui as _ui
    _WINDOW = _ui.launch()
    return _WINDOW
