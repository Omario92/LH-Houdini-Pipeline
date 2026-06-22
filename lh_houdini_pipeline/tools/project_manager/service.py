"""
lh_houdini_pipeline.tools.project_manager.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Effecting layer for the project manager: create directories on disk, scan for
existing projects, resolve the next work-file version, and (optionally) point
Houdini's ``$JOB`` at a project.

Directory creation and scanning are **pure Python** -- they need no Houdini
and run anywhere.  Only :func:`set_houdini_job` touches ``hou`` (lazily), so
importing this module never requires Houdini.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.core.path import ensure_dir, normalize
from lh_houdini_pipeline.file.scanner import find_files
from lh_houdini_pipeline.file.versioning import Version, VersionResolver
from lh_houdini_pipeline.tools.project_manager.core import ProjectPlan

PathLike = Union[str, Path]
_log = get_logger(__name__)


@dataclass
class CreateResult:
    """Outcome of realising a :class:`ProjectPlan` on disk.

    Attributes:
        created:  Directories newly created.
        existed:  Directories that were already present.
        failed:   ``(path, error)`` pairs for directories that could not be made.
        dry_run:  ``True`` if nothing was actually written.
    """
    created: List[str] = field(default_factory=list)
    existed: List[str] = field(default_factory=list)
    failed:  List[tuple] = field(default_factory=list)
    dry_run: bool = False

    @property
    def ok(self) -> bool:
        """``True`` if no directory creation failed."""
        return not self.failed

    def summary(self) -> str:
        """One-line human summary for logs / status labels."""
        prefix = "[DRY-RUN] " if self.dry_run else ""
        return (
            prefix + str(len(self.created)) + " created, "
            + str(len(self.existed)) + " existed, "
            + str(len(self.failed)) + " failed"
        )


def create_project(plan: ProjectPlan, dry_run: bool = False) -> CreateResult:
    """Create every directory in *plan* (``mkdir -p`` semantics).

    Args:
        plan:    The :class:`ProjectPlan` to realise.
        dry_run: If ``True``, classify each path as created/existed but write
                 nothing to disk.

    Returns:
        A :class:`CreateResult` describing what happened.
    """
    result = CreateResult(dry_run=dry_run)
    for d in plan.directories:
        path = Path(d)
        if path.is_dir():
            result.existed.append(d)
            continue
        if dry_run:
            result.created.append(d)
            continue
        try:
            ensure_dir(path)
            result.created.append(d)
        except OSError as exc:
            _log.error("Could not create " + d + ": " + str(exc))
            result.failed.append((d, str(exc)))
    _log.info("create_project " + plan.project + ": " + result.summary())
    return result


def scan_projects(root: PathLike) -> List[str]:
    """List immediate sub-directories of *root* (candidate projects).

    Args:
        root: Directory expected to contain project folders.

    Returns:
        Sorted list of project names (folder names), empty if *root* is missing.
    """
    r = Path(root)
    if not r.is_dir():
        return []
    return sorted(p.name for p in r.iterdir() if p.is_dir())


def next_work_version(directory: PathLike, pattern: Optional[str] = None) -> Version:
    """Return the next work-file :class:`Version` for *directory*.

    Thin wrapper over :class:`file.versioning.VersionResolver` so callers get
    versioning without importing the file layer directly.

    Args:
        directory: Folder holding versioned work files.
        pattern:   Glob with the version wildcard as ``*`` (e.g.
                   ``"fx_v*.hip"``).  ``None`` matches any versioned file.

    Returns:
        The :class:`Version` to use for the next save (``v001`` if none exist).
    """
    return VersionResolver(directory, pattern=pattern).next_version()


def list_work_files(directory: PathLike, pattern: str = "*.hip*") -> List[str]:
    """Return work files in *directory* (forward-slash paths).

    Args:
        directory: Folder to list.
        pattern:   Glob pattern (defaults to Houdini hip files).

    Returns:
        Sorted list of matching file paths.
    """
    return [normalize(p) for p in find_files(directory, pattern=pattern)]


def set_houdini_job(path: PathLike) -> bool:
    """Point Houdini's ``$JOB`` at *path* (lazy ``hou`` import).

    Args:
        path: Project directory to use as ``$JOB``.

    Returns:
        ``True`` if set, ``False`` if running outside Houdini.
    """
    try:
        import hou  # noqa: PLC0415
    except ImportError:
        _log.warning("set_houdini_job called outside Houdini; $JOB unchanged.")
        return False
    hou.putenv("JOB", normalize(str(path)))
    _log.info("$JOB set to " + normalize(str(path)))
    return True
