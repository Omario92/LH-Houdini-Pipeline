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


def launch(*args, **kwargs):
    """Lazy proxy to the UI launcher (imports PySide/``hou`` only when called)."""
    from lh_houdini_pipeline.tools.lops_asset_builder.launch import launch as _l
    return _l()
