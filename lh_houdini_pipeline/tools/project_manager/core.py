"""
lh_houdini_pipeline.tools.project_manager.core
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pure planning for a Houdini project directory structure -- NO ``hou``.

Reuses existing components:

    core.path.PathResolver / normalize  -> path composition (forward slashes)
    file.versioning.VersionResolver     -> next work-file version (service layer)

A :class:`ProjectPlan` is a flat, deterministic list of directories to create
for a project plus its assets and shots.  Being hou-free, this backs a dry-run
and is fully unit-testable with plain ``python``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.core.path import PathResolver, normalize

PathLike = Union[str, "object"]
_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------

#: Top-level folders created directly under <root>/<project>.
DEFAULT_PROJECT_FOLDERS: Tuple[str, ...] = (
    "houdini", "houdini/scenes", "houdini/scripts", "hda",
    "geo", "tex", "usd", "abc", "cache", "render", "comp", "ref",
)
#: Per-asset folders created under <project>/assets/<asset>/.
DEFAULT_ASSET_FOLDERS: Tuple[str, ...] = ("model", "tex", "lookdev", "usd")
#: Per-shot folders created under <project>/shots/<shot>/.
DEFAULT_SHOT_FOLDERS: Tuple[str, ...] = ("anim", "fx", "light", "render", "cache")


@dataclass(frozen=True)
class ProjectTemplate:
    """A reusable description of a project's folder layout.

    Attributes:
        name:            Template label.
        project_folders: Folders directly under ``<root>/<project>``.
        asset_folders:   Folders under each ``<project>/assets/<asset>``.
        shot_folders:    Folders under each ``<project>/shots/<shot>``.
        work_template:   Path template (``core.path`` tokens) for a versioned
                         Houdini work file.
    """
    name:            str = "default"
    project_folders: Tuple[str, ...] = DEFAULT_PROJECT_FOLDERS
    asset_folders:   Tuple[str, ...] = DEFAULT_ASSET_FOLDERS
    shot_folders:    Tuple[str, ...] = DEFAULT_SHOT_FOLDERS
    work_template:   str = "{root}/{project}/houdini/scenes/{entity}/{department}_v{version:03d}.hip"


DEFAULT_TEMPLATE = ProjectTemplate()


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProjectPlan:
    """A flat, ordered list of directories to create for a project.

    Attributes:
        root:        Project root (forward-slash, normalised).
        project:     Sanitised project name.
        directories: Absolute directory paths, sorted and de-duplicated.
        assets:      Asset names included in the plan.
        shots:       Shot names included in the plan.
        template:    The :class:`ProjectTemplate` used.
    """
    root:        str
    project:     str
    directories: Tuple[str, ...]
    assets:      Tuple[str, ...] = field(default_factory=tuple)
    shots:       Tuple[str, ...] = field(default_factory=tuple)
    template:    ProjectTemplate = DEFAULT_TEMPLATE

    @property
    def project_root(self) -> str:
        """``<root>/<project>`` (forward slashes)."""
        return normalize(self.root + "/" + self.project)

    def summary(self) -> str:
        """One-line human summary for logs / status labels."""
        return (
            "project '" + self.project + "': " + str(len(self.directories))
            + " dirs, " + str(len(self.assets)) + " asset(s), "
            + str(len(self.shots)) + " shot(s)"
        )


def _sanitize(name: str) -> str:
    """Sanitise a project/asset/shot name into a safe folder token."""
    out = []
    for ch in str(name).strip():
        out.append(ch if (ch.isalnum() or ch in "_-") else "_")
    return "".join(out).strip("_-")


def sanitize_name(name: str) -> str:
    """Public, pure name sanitiser for UI live-suggestions.

    Mirrors the rule used by :func:`plan_project`: keep alphanumerics, ``_``
    and ``-``; replace everything else; strip leading/trailing separators.

    Args:
        name: Raw user-entered name.

    Returns:
        A filesystem-safe folder token (may be empty if *name* had no usable
        characters).
    """
    return _sanitize(name)


def plan_project(
    root: PathLike,
    project: str,
    assets: Optional[List[str]] = None,
    shots: Optional[List[str]] = None,
    template: ProjectTemplate = DEFAULT_TEMPLATE,
) -> ProjectPlan:
    """Plan the directory tree for *project* under *root* (dry-run safe).

    Args:
        root:     Parent directory that will contain the project folder.
        project:  Project name (sanitised to a folder token).
        assets:   Optional asset names; each gets ``assets/<asset>/<folders>``.
        shots:    Optional shot names; each gets ``shots/<shot>/<folders>``.
        template: Folder layout to use (defaults to :data:`DEFAULT_TEMPLATE`).

    Returns:
        A :class:`ProjectPlan` with a sorted, de-duplicated directory list.

    Raises:
        ValueError: If *project* is empty after sanitisation.
    """
    proj = _sanitize(project)
    if not proj:
        raise ValueError("Project name is empty after sanitisation: " + repr(project))

    root_n = normalize(str(root)).rstrip("/")
    resolver = PathResolver(root=root_n, project=proj)
    base = resolver.resolve("{root}/{project}")

    dirs = set()
    dirs.add(base)
    for folder in template.project_folders:
        dirs.add(normalize(base + "/" + folder))

    asset_names = tuple(_sanitize(a) for a in (assets or []) if _sanitize(a))
    shot_names = tuple(_sanitize(s) for s in (shots or []) if _sanitize(s))

    if asset_names:
        dirs.add(normalize(base + "/assets"))
        for asset in asset_names:
            adir = normalize(base + "/assets/" + asset)
            dirs.add(adir)
            for folder in template.asset_folders:
                dirs.add(normalize(adir + "/" + folder))

    if shot_names:
        dirs.add(normalize(base + "/shots"))
        for shot in shot_names:
            sdir = normalize(base + "/shots/" + shot)
            dirs.add(sdir)
            for folder in template.shot_folders:
                dirs.add(normalize(sdir + "/" + folder))

    plan = ProjectPlan(
        root=root_n,
        project=proj,
        directories=tuple(sorted(dirs)),
        assets=asset_names,
        shots=shot_names,
        template=template,
    )
    _log.info("Planned " + plan.summary())
    return plan


def work_file_template(plan: ProjectPlan) -> str:
    """Return the work-file path template partially resolved for *plan*.

    Resolves ``{root}`` and ``{project}`` from the plan, leaving ``{entity}``,
    ``{department}`` and ``{version}`` for the caller to fill at save time.

    Args:
        plan: A :class:`ProjectPlan`.

    Returns:
        A path-template string still containing ``{entity}`` / ``{department}``
        / ``{version}`` tokens.
    """
    from lh_houdini_pipeline.core.path import PathTemplate
    tmpl = PathTemplate(plan.template.work_template)
    return tmpl.format_partial(root=plan.root, project=plan.project).template
