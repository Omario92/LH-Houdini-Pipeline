"""
lh_houdini_pipeline.tools.tex_to_mtlx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TexToMtlx -- scan a texture folder and build MaterialX shader networks.

Composition of existing components (no monolith):

    file.scanner / file.texture_parser  ->  parse filenames
    materialx.rules                      ->  channel -> input / colorspace
    materialx.builder                    ->  plan + create VOP networks
    core.logger                          ->  structured logging

Public surface
--------------
* ``scan_and_plan`` / ``format_dry_run`` -- pure, hou-free (dry-run + tests)
* ``build_plans``                        -- hou-side build
* ``launch``                             -- open the PySide UI (Houdini only)

The pure pieces import cleanly outside Houdini; ``build_plans`` and ``launch``
import ``hou`` / Qt lazily, so importing this package never requires Houdini.
"""

from __future__ import annotations

from lh_houdini_pipeline.tools.tex_to_mtlx.core import (
    ScanResult,
    format_dry_run,
    scan_and_plan,
    select_plans,
)

__all__ = [
    "ScanResult",
    "scan_and_plan",
    "select_plans",
    "format_dry_run",
    "build_plans",
    "launch",
]


def build_plans(*args, **kwargs):
    """Lazy proxy to ``service.build_plans`` (imports ``hou`` only when called).

    See :func:`lh_houdini_pipeline.tools.tex_to_mtlx.service.build_plans`.
    """
    from lh_houdini_pipeline.tools.tex_to_mtlx.service import build_plans as _bp
    return _bp(*args, **kwargs)


def launch(*args, **kwargs):
    """Lazy proxy to the UI launcher (imports PySide/``hou`` only when called).

    See :func:`lh_houdini_pipeline.tools.tex_to_mtlx.launch.launch`.
    """
    from lh_houdini_pipeline.tools.tex_to_mtlx.launch import launch as _launch
    return _launch()
