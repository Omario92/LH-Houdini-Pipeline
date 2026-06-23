"""
lh_houdini_pipeline.tools.cache_manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Scan, inspect, and safely purge on-disk scene caches.

Composition (no monolith):

    file.cache_utils    -> pure sequence model, gap/staleness/size
    core                -> cleanup policy + dry-run CleanupPlan (pure)
    houdini.traversal   -> discover cache nodes in the scene
    service             -> scan dirs + safe delete (trash-first)
    ui                  -> PySide table + threaded delete

Public surface
--------------
* Pure / testable: ``CleanupPolicy``, ``plan_cleanup``, ``classify``, ``CacheStatus``
* Houdini / filesystem: ``discover_cache_dirs``, ``scan_scene``, ``scan_dirs``,
  ``delete_paths``, ``open_in_explorer``
* ``launch`` -- open the PySide UI (Houdini only)
"""

from __future__ import annotations

from lh_houdini_pipeline.tools.cache_manager.core import (
    CacheReportRow,
    CacheStatus,
    CleanupPlan,
    CleanupPolicy,
    classify,
    plan_cleanup,
    paths_for_sequences,
)
from lh_houdini_pipeline.tools.cache_manager.service import (
    DEFAULT_FORMATS,
    DeleteResult,
    delete_paths,
    discover_cache_dirs,
    open_in_explorer,
    scan_dirs,
    scan_scene,
)

__all__ = [
    "CacheStatus",
    "CleanupPolicy",
    "CleanupPlan",
    "CacheReportRow",
    "classify",
    "plan_cleanup",
    "paths_for_sequences",
    "DeleteResult",
    "DEFAULT_FORMATS",
    "discover_cache_dirs",
    "scan_scene",
    "scan_dirs",
    "delete_paths",
    "open_in_explorer",
    "launch",
]

_WINDOW = None


def launch(*args, **kwargs):
    """Open the Cache Manager window and return it (cached module-side)."""
    global _WINDOW
    from lh_houdini_pipeline.tools.cache_manager import ui as _ui
    _WINDOW = _ui.launch()
    return _WINDOW
