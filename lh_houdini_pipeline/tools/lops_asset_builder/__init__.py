"""
lh_houdini_pipeline.tools.lops_asset_builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Build a USD component asset (geometry + materials + output) in /stage from a
geometry file and an optional texture folder.

Composition (no monolith):

    tools.tex_to_mtlx.core   -> material plans from textures
    materialx.builder        -> mtlx networks inside a material library
    core.logger              -> logging

Public surface
--------------
* ``plan_asset`` / ``AssetBuildPlan`` -- pure, hou-free (dry-run + tests)
* ``build_asset`` / ``save_asset``    -- hou-side build (lazy ``hou`` import)
"""

from __future__ import annotations

from lh_houdini_pipeline.tools.lops_asset_builder.core import (
    AssetBuildPlan,
    MaterialAssignment,
    plan_asset,
)

__all__ = [
    "AssetBuildPlan",
    "MaterialAssignment",
    "plan_asset",
    "build_asset",
    "save_asset",
    "save_asset_background",
    "launch",
]


def build_asset(*args, **kwargs):
    """Lazy proxy to ``service.build_asset`` (imports ``hou`` only when called)."""
    from lh_houdini_pipeline.tools.lops_asset_builder.service import build_asset as _b
    return _b(*args, **kwargs)


def save_asset(*args, **kwargs):
    """Lazy proxy to ``service.save_asset`` (imports ``hou`` only when called)."""
    from lh_houdini_pipeline.tools.lops_asset_builder.service import save_asset as _s
    return _s(*args, **kwargs)


def save_asset_background(*args, **kwargs):
    """Lazy proxy to ``service.save_asset_background``."""
    from lh_houdini_pipeline.tools.lops_asset_builder.service import save_asset_background as _sb
    return _sb(*args, **kwargs)


_WINDOW = None  # keep a reference so the window is not garbage-collected


def launch(*args, **kwargs):
    """Open the LOPs Asset Builder window and return it (cached module-side).

    Imports the ``ui`` submodule directly (never a ``launch`` submodule),
    so the package attribute ``launch`` stays this function across repeated
    calls -- importing a same-named submodule would otherwise shadow it.
    """
    global _WINDOW
    from lh_houdini_pipeline.tools.lops_asset_builder import ui as _ui
    _WINDOW = _ui.launch()
    return _WINDOW
