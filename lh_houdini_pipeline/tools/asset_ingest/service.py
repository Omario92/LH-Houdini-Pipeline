"""
lh_houdini_pipeline.tools.asset_ingest.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Houdini-side execution of an ingestion plan.

Each :class:`~lh_houdini_pipeline.tools.asset_ingest.core.IngestItem` is turned
into a USD component by *delegating* to the verified ``lops_asset_builder``
service -- we never re-wire componentgeometry/material/output here.  This layer
only orchestrates: loop items, report progress, isolate per-item failures, and
lay the resulting networks out tidily.

``hou`` is imported lazily; the module imports for unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.core.profiling import timed
from lh_houdini_pipeline.tools.asset_ingest.core import IngestItem, PathLike, plan_ingest

_log = get_logger(__name__)

# Progress hook: on_progress(index, total, asset_name).
ProgressHook = Callable[[int, int, str], None]


@dataclass
class IngestResult:
    """Outcome of ingesting one geometry file.

    Attributes:
        asset_name:  Derived asset name.
        geo_path:    Source geometry file.
        output_node: componentoutput node path (empty on failure).
        error:       Error string if the build failed, else ``None``.
    """

    asset_name: str
    geo_path: str
    output_node: str = ""
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class IngestSummary:
    """Aggregate result of a batch ingest."""

    results: List[IngestResult] = field(default_factory=list)

    @property
    def succeeded(self) -> List[IngestResult]:
        return [r for r in self.results if r.ok]

    @property
    def failed(self) -> List[IngestResult]:
        return [r for r in self.results if not r.ok]


# ---------------------------------------------------------------------------
# Solaris-context detection (for the drag-drop guard)
# ---------------------------------------------------------------------------

def is_solaris_context() -> bool:
    """Return True if the network editor under the cursor is a LOP (Solaris) net.

    Used by the drag-drop handler so dropping geometry only triggers ingestion
    when the artist is actually in Solaris.  Best-effort and never raises.
    """
    try:
        import hou  # noqa: PLC0415

        pane = hou.ui.paneTabUnderCursor()
        if pane is None:
            # fall back to the current network editor
            pane = hou.ui.curDesktop().paneTabOfType(hou.paneTabType.NetworkEditor)
        if pane is None or not hasattr(pane, "pwd"):
            return False
        return pane.pwd().childTypeCategory() == hou.lopNodeTypeCategory()
    except Exception:  # noqa: BLE001
        return False


def _stage_root() -> str:
    """Return a LOP build parent path, creating ``/stage`` context if needed."""
    return "/stage"


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------

@timed("asset_ingest.ingest_items")
def ingest_items(
    items: Sequence[IngestItem],
    parent_path: str = "/stage",
    output_dir: Optional[PathLike] = None,
    recursive: bool = False,
    on_progress: Optional[ProgressHook] = None,
) -> IngestSummary:
    """Build a USD component for each *items* entry under *parent_path*.

    Per-item failures are caught and recorded so one bad FBX never aborts a
    100-asset batch (the Week-04 "ingest a messy marketplace dump" reality).

    Args:
        items:       Resolved ingest items (from :func:`core.plan_ingest`).
        parent_path: LOP network to build in (default ``/stage``).
        output_dir:  Optional directory to set each component's USD output.
        recursive:   Recurse into texture subfolders when planning materials.
        on_progress: Optional ``on_progress(i, total, name)`` callback.

    Returns:
        An :class:`IngestSummary` of per-item results.
    """
    from lh_houdini_pipeline.tools import lops_asset_builder as _lab

    summary = IngestSummary()
    total = len(items)
    for i, item in enumerate(items, start=1):
        if on_progress is not None:
            try:
                on_progress(i, total, item.asset_name)
            except Exception as exc:  # noqa: BLE001
                _log.debug("on_progress raised: " + str(exc))
        try:
            plan = item.to_build_plan(output_dir=output_dir, recursive=recursive)
            res = _lab.build_asset(plan, parent_path=parent_path)
            summary.results.append(
                IngestResult(
                    asset_name=item.asset_name,
                    geo_path=item.geo_path,
                    output_node=res.output,
                )
            )
            _log.info("Ingested '" + item.asset_name + "' -> " + res.output)
        except Exception as exc:  # noqa: BLE001 -- isolate one bad asset
            summary.results.append(
                IngestResult(
                    asset_name=item.asset_name,
                    geo_path=item.geo_path,
                    error=str(exc),
                )
            )
            _log.warning("Ingest failed for '" + item.geo_path + "': " + str(exc))

    _log.info(
        "Ingest batch done: " + str(len(summary.succeeded)) + " ok, "
        + str(len(summary.failed)) + " failed."
    )
    return summary


def ingest_paths(
    paths: Sequence[PathLike],
    parent_path: str = "/stage",
    output_dir: Optional[PathLike] = None,
    recursive: bool = False,
    on_progress: Optional[ProgressHook] = None,
) -> IngestSummary:
    """Convenience: plan *paths* (files/folders) and ingest them in one call.

    This is the entry point the drag-drop handler and shelf tools use.
    """
    items = plan_ingest(paths)
    if not items:
        _log.warning("ingest_paths: no geometry files found in input.")
        return IngestSummary()
    return ingest_items(
        items,
        parent_path=parent_path,
        output_dir=output_dir,
        recursive=recursive,
        on_progress=on_progress,
    )
