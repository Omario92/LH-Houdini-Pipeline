"""
lh_houdini_pipeline.tools.asset_ingest.core
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pure ingestion planning: turn dropped/selected geometry files into a list of
build-ready :class:`IngestItem` objects (Rebelway Week 04 + Week 10 drag-drop).

Production reasoning
--------------------
The whole value of an ingestion pipeline is that an artist drops a messy folder
of marketplace assets and gets clean, named USD components -- *without manual
wiring*.  The "decisions" in that sentence are pure data work and live here:

* **Which files are geometry?**          -> :func:`is_geometry_file`
* **What should the asset be called?**    -> :func:`derive_asset_name`
  (strip version/date noise so ``rock_v003_2024-01-12.fbx`` -> ``rock``)
* **Where are its textures?**             -> :func:`find_texture_folder`
* **Expand a dropped folder to files**    -> :func:`expand_inputs`

The actual LOP build is delegated to the proven ``lops_asset_builder`` tool --
ingestion *composes* it rather than re-implementing USD componentisation
(DRY, and we inherit its verified .rat/material handling for free).

No ``hou`` -- fully unit-testable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

from lh_houdini_pipeline.tools.lops_asset_builder.core import AssetBuildPlan, plan_asset

PathLike = Union[str, Path]

#: Geometry formats we accept for ingestion (lower-case, leading dot).
GEO_EXTS: Tuple[str, ...] = (
    ".fbx", ".obj", ".abc", ".usd", ".usda", ".usdc", ".usdz",
    ".bgeo", ".bgeo.sc", ".ply", ".stl",
)

#: Conventional sibling folder names that hold an asset's textures.
_TEX_FOLDER_NAMES = ("textures", "tex", "maps", "sourceimages", "texture")

#: Image extensions used to sniff whether a folder "looks like" textures.
_IMG_EXTS = (".exr", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".tga", ".rat", ".tx", ".hdr")

# Version (v003 / _v3) and ISO-ish date (2024-01-12 / 20240112) noise tokens.
_VERSION_TOKEN = re.compile(r"[_.-]?[vV]\d{1,4}\b")
_DATE_TOKEN = re.compile(r"[_.-]?\d{4}[-_]?\d{2}[-_]?\d{2}\b")


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def _compound_ext(path: Path) -> str:
    """Return the (possibly compound) lower-case extension, e.g. ``.bgeo.sc``."""
    name = path.name.lower()
    if name.endswith(".bgeo.sc"):
        return ".bgeo.sc"
    return path.suffix.lower()


def is_geometry_file(path: PathLike) -> bool:
    """Return True if *path* is an accepted geometry file."""
    return _compound_ext(Path(path)) in GEO_EXTS


def derive_asset_name(path: PathLike) -> str:
    """Derive a clean asset name from a geometry filename.

    Strips version (``v003``) and date (``2024-01-12``) noise, then sanitises
    to a USD/Node-safe identifier.

    Examples::

        "rock_v003_2024-01-12.fbx" -> "rock"
        "Tree Trunk.obj"           -> "Tree_Trunk"
        "123mesh.abc"              -> "a_123mesh"
    """
    stem = Path(path).name
    # drop compound/simple extension first
    ext = _compound_ext(Path(path))
    if ext and stem.lower().endswith(ext):
        stem = stem[: -len(ext)]
    stem = _DATE_TOKEN.sub("", stem)
    stem = _VERSION_TOKEN.sub("", stem)
    # sanitise to identifier
    out = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in stem.strip())
    out = re.sub(r"_+", "_", out).strip("_")
    if not out:
        out = "asset"
    if out[0].isdigit():
        out = "a_" + out
    return out


def find_texture_folder(geo_path: PathLike) -> Optional[str]:
    """Locate a texture folder for *geo_path*, or ``None`` if none is obvious.

    Search order (cheap, deterministic):

    1. A sibling directory named ``textures``/``tex``/``maps``/... .
    2. A child of the geo's own directory with one of those names.
    3. The geo's own directory, *only if* it already contains image files
       (the "flat" layout where geo + textures sit together).
    """
    geo = Path(geo_path)
    parent = geo.parent
    if not parent.is_dir():
        return None

    # 1) + 2) named texture folders next to / under the geo
    candidates: List[Path] = []
    for name in _TEX_FOLDER_NAMES:
        candidates.append(parent / name)
        candidates.append(parent.parent / name)
    for c in candidates:
        if c.is_dir() and _has_images(c):
            return str(c)

    # 3) flat layout: geo dir itself holds images
    if _has_images(parent):
        return str(parent)
    return None


def _has_images(folder: Path) -> bool:
    """True if *folder* contains at least one image file (shallow check)."""
    try:
        for p in folder.iterdir():
            if p.is_file() and p.suffix.lower() in _IMG_EXTS:
                return True
    except OSError:
        return False
    return False


def expand_inputs(paths: Sequence[PathLike]) -> List[str]:
    """Expand a mix of files and folders into a flat list of geometry files.

    * A geometry file is kept as-is.
    * A directory is scanned (non-recursive) for geometry files.
    * Non-geometry files are dropped.

    Returns a de-duplicated, sorted list of absolute-ish path strings.
    """
    out: List[str] = []
    seen = set()
    for raw in paths:
        p = Path(raw)
        files: List[Path] = []
        if p.is_dir():
            files = [c for c in sorted(p.iterdir()) if c.is_file() and is_geometry_file(c)]
        elif p.is_file() and is_geometry_file(p):
            files = [p]
        for f in files:
            key = str(f)
            if key not in seen:
                seen.add(key)
                out.append(key)
    return out


# ---------------------------------------------------------------------------
# Value object + planning
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IngestItem:
    """One geometry file resolved into build inputs (frozen value object)."""

    geo_path: str
    asset_name: str
    tex_folder: Optional[str]

    def to_build_plan(
        self,
        output_dir: Optional[PathLike] = None,
        recursive: bool = False,
        output_ext: str = ".usd",
    ) -> AssetBuildPlan:
        """Compose an :class:`AssetBuildPlan` via the asset-builder planner.

        Delegates to ``lops_asset_builder.core.plan_asset`` so ingestion reuses
        its texture scanning + material defaulting unchanged.
        """
        return plan_asset(
            asset_name=self.asset_name,
            geo_path=self.geo_path,
            tex_folder=self.tex_folder,
            output_dir=output_dir,
            recursive=recursive,
            output_ext=output_ext,
        )


def plan_ingest(paths: Sequence[PathLike]) -> List[IngestItem]:
    """Resolve dropped/selected *paths* into a list of :class:`IngestItem`.

    Pure: discovers files, derives names, and locates textures, but builds
    nothing.  The service layer turns each item into LOP nodes.
    """
    items: List[IngestItem] = []
    for geo in expand_inputs(paths):
        items.append(
            IngestItem(
                geo_path=geo,
                asset_name=derive_asset_name(geo),
                tex_folder=find_texture_folder(geo),
            )
        )
    return items
