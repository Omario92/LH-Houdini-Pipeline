"""
lh_houdini_pipeline.tools.cache_manager.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Houdini + filesystem side of the Scene Cache Manager.

Responsibilities (the *only* impure parts of the tool):

* **Discover** cache output directories from the live scene by finding cache
  nodes (``filecache``, ``rop_geometry``, ``geometry``, ``filecache::2.0`` ...)
  and evaluating their output-path parm.
* **Scan** those directories into sequences (delegates to ``file.cache_utils``).
* **Delete** selected paths *safely*: send-to-trash when available, with a
  guarded ``os.remove`` fallback, never raising mid-batch.

``hou`` is imported lazily so the module imports for unit tests; only the
discovery calls require a live session.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.file.cache_utils import CacheSequence, scan_directory

_log = get_logger(__name__)

#: Node types whose output parm points at a cache on disk.
#: (type_name, parm_name) -- parm holds the file path template.
_CACHE_NODE_PARMS = (
    ("filecache", "file"),
    ("filecache::2.0", "file"),
    ("rop_geometry", "sopoutput"),
    ("geometry", "sopoutput"),
    ("rop_alembic", "filename"),
    ("alembic", "filename"),
    ("usd_rop", "lopoutput"),
    ("usdrender_rop", "lopoutput"),
)

#: Default cache formats to scan for (overridable from config).
DEFAULT_FORMATS: Tuple[str, ...] = ("bgeo.sc", "bgeo", "vdb", "usd", "usdc", "abc")


@dataclass
class DeleteResult:
    """Outcome of a :func:`delete_paths` batch.

    Attributes:
        deleted:    Paths successfully removed.
        failed:     ``(path, reason)`` pairs that could not be removed.
        used_trash: Whether send-to-trash was used (vs hard delete).
    """

    deleted: List[str] = field(default_factory=list)
    failed: List[Tuple[str, str]] = field(default_factory=list)
    used_trash: bool = False

    @property
    def freed_count(self) -> int:
        return len(self.deleted)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_cache_dirs() -> List[str]:
    """Return distinct directories referenced by cache nodes in the scene.

    Walks ``/obj`` and ``/stage`` for known cache node types, evaluates each
    output parm, and collects the parent directory.  Unreadable/unset parms
    are skipped (non-fatal).  Requires a live Houdini session.
    """
    import hou  # noqa: PLC0415
    from lh_houdini_pipeline.houdini import traversal as T

    dirs: List[str] = []
    seen = set()
    roots = [hou.node("/obj"), hou.node("/stage"), hou.node("/out")]
    type_to_parm = dict(_CACHE_NODE_PARMS)

    for root in roots:
        if root is None:
            continue
        # find_by_type per known type is O(N) each; acceptable for typical
        # scenes. We loop the small fixed set of cache types.
        for type_name, parm_name in _CACHE_NODE_PARMS:
            for node in T.find_by_type(root, type_name, exact=False):
                # re-resolve the right parm for this node's actual type
                pn = type_to_parm.get(node.type().name(), parm_name)
                parm = node.parm(pn) or node.parm(parm_name)
                if parm is None:
                    continue
                try:
                    raw = parm.eval()
                except Exception:  # noqa: BLE001 -- expression errors, etc.
                    continue
                if not raw:
                    continue
                folder = str(Path(hou.text.expandString(raw)).parent)
                if folder and folder not in seen and os.path.isdir(folder):
                    seen.add(folder)
                    dirs.append(folder)
    _log.info("discover_cache_dirs found " + str(len(dirs)) + " directory(ies)")
    return dirs


def scan_dirs(
    directories: List[str],
    formats: Tuple[str, ...] = DEFAULT_FORMATS,
    recursive: bool = False,
) -> List[CacheSequence]:
    """Scan an explicit list of *directories* into cache sequences.

    Pure delegation to ``file.cache_utils.scan_directory`` -- listed here so
    the UI has a single service entry point and does not import the file layer
    directly.
    """
    out: List[CacheSequence] = []
    for d in directories:
        out.extend(scan_directory(d, formats=formats, recursive=recursive))
    return out


def scan_scene(
    formats: Tuple[str, ...] = DEFAULT_FORMATS,
) -> List[CacheSequence]:
    """Discover cache dirs from the live scene and scan them in one call."""
    return scan_dirs(discover_cache_dirs(), formats=formats)


# ---------------------------------------------------------------------------
# Deletion -- safe by default
# ---------------------------------------------------------------------------

def delete_paths(paths: List[str], use_trash: bool = True) -> DeleteResult:
    """Delete *paths*, preferring the OS trash; never raise mid-batch.

    Safety design:

    * **Trash first** -- ``send2trash`` (if installed) is recoverable; a
      misclick does not nuke a 40 GB sim irreversibly.
    * **Per-file try/except** -- one locked/permission-denied file must not
      abort the rest of the batch.  Failures are collected and reported.

    Args:
        paths:     Absolute file paths to remove.
        use_trash: Attempt send-to-trash before hard delete.

    Returns:
        A :class:`DeleteResult` summarising successes and failures.
    """
    result = DeleteResult(used_trash=False)

    trash_fn = None
    if use_trash:
        try:
            from send2trash import send2trash as trash_fn  # type: ignore
            result.used_trash = True
        except Exception:  # noqa: BLE001 -- not installed; fall back
            trash_fn = None
            _log.warning("send2trash unavailable; falling back to hard delete.")

    for p in paths:
        try:
            if trash_fn is not None:
                trash_fn(p)
            else:
                os.remove(p)
            result.deleted.append(p)
        except FileNotFoundError:
            # Already gone -- treat as success (idempotent).
            result.deleted.append(p)
        except Exception as exc:  # noqa: BLE001
            result.failed.append((p, str(exc)))
            _log.warning("Failed to delete " + p + ": " + str(exc))

    _log.info(
        "delete_paths removed " + str(result.freed_count)
        + " file(s); " + str(len(result.failed)) + " failure(s)."
    )
    return result


def open_in_explorer(path: str) -> bool:
    """Reveal *path* in the OS file browser (Explorer/Finder/xdg-open).

    Best-effort and never raises -- returns ``False`` on any failure.
    """
    import subprocess  # noqa: PLC0415
    import sys  # noqa: PLC0415

    target = path if os.path.isdir(path) else str(Path(path).parent)
    try:
        if sys.platform.startswith("win"):
            os.startfile(target)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", target], check=False)
        else:
            subprocess.run(["xdg-open", target], check=False)
        return True
    except Exception as exc:  # noqa: BLE001
        _log.warning("open_in_explorer failed for " + target + ": " + str(exc))
        return False
