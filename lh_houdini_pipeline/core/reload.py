"""
lh_houdini_pipeline.core.reload
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Hot-reload utilities for iterative development inside Houdini.

Because Houdini keeps Python modules resident across HIP file reloads,
edited pipeline code does not take effect until the module is explicitly
reloaded.  This module provides helpers for reloading the entire
``lh_houdini_pipeline`` package tree in the correct dependency order.

Stub -- to be implemented.
"""

from __future__ import annotations

import importlib
import sys
from typing import List

_PACKAGE_ROOT = "lh_houdini_pipeline"


def reload_package(verbose: bool = False) -> List[str]:
    """Reload all ``lh_houdini_pipeline.*`` modules currently in sys.modules.

    Modules are reloaded in import order (leaves first) to avoid stale
    references.

    Args:
        verbose: If True, print each reloaded module name.

    Returns:
        List of module names that were reloaded.
    """
    # Collect matching modules; sort so sub-packages reload before parents.
    targets = sorted(
        [name for name in sys.modules if name.startswith(_PACKAGE_ROOT)],
        key=lambda n: n.count("."),
        reverse=True,
    )
    reloaded: List[str] = []
    for name in targets:
        try:
            importlib.reload(sys.modules[name])
            reloaded.append(name)
            if verbose:
                print("Reloaded:", name)
        except Exception as exc:
            print(f"Warning: could not reload '{name}': {exc}")
    return reloaded
