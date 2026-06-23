"""
lh_houdini_pipeline.tools.tex_to_mtlx.core
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pure orchestration for the TexToMtlx tool -- NO ``hou``, NO Qt.

Composes existing components:

    file.scanner          -> existence / directory checks
    file.texture_parser   -> filename -> TextureInfo
    materialx.builder     -> TextureInfo list -> MaterialBuildPlan list

The output (:class:`ScanResult`) is everything the UI needs to display a
material list, and everything the hou ``service`` layer needs to build.
Because this module is hou-free it backs the tool's dry-run mode and is
unit-testable with plain ``python``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.file.texture_parser import (
    TextureChannel,
    TextureInfo,
    TextureParser,
)
from lh_houdini_pipeline.materialx.builder import (
    MaterialBuildPlan,
    MaterialPlanner,
)

PathLike = Union[str, Path]
_log = get_logger(__name__)


@dataclass(frozen=True)
class ScanResult:
    """Result of scanning + planning a texture directory.

    Attributes:
        directory:   The directory that was scanned.
        infos:       Every parsed :class:`TextureInfo` (including unknowns).
        plans:       One :class:`MaterialBuildPlan` per discovered material.
        unknowns:    Stems whose channel could not be detected.
    """
    directory: Path
    infos:     Tuple[TextureInfo, ...]
    plans:     Tuple[MaterialBuildPlan, ...]
    unknowns:  Tuple[str, ...] = field(default_factory=tuple)

    @property
    def material_names(self) -> Tuple[str, ...]:
        """Names of all planned materials."""
        return tuple(p.name for p in self.plans)

    def summary(self) -> str:
        """Return a one-line human summary (for status labels / logs)."""
        return (
            str(len(self.plans)) + " material(s), "
            + str(len(self.infos)) + " texture(s), "
            + str(len(self.unknowns)) + " unrecognised"
        )


def scan_and_plan(
    directory: PathLike,
    recursive: bool = False,
    channels: Optional[Tuple[TextureChannel, ...]] = None,
    extensions: Optional[List[str]] = None,
    auto_recurse: bool = True,
) -> ScanResult:
    """Scan *directory*, parse textures, and produce build plans (dry-run safe).

    Args:
        directory:  Folder containing texture files.
        recursive:  Recurse into subdirectories.
        channels:   Override which channels to plan (defaults to MVP set).
        extensions: Override texture extensions (passed to the parser).
        auto_recurse: When ``recursive`` is ``False`` and the folder holds no
            textures directly but has sub-folders that do (a library layout
            like ``MSMC_Blobs/Blob_Dots/...``), automatically recurse so that
            scanning the parent finds every per-sub-folder material.

    Returns:
        A :class:`ScanResult`.  Never raises for an empty folder -- it returns
        an empty result so the UI can show "0 materials" gracefully.

    Raises:
        NotADirectoryError: If *directory* does not exist or is not a folder.
    """
    d = Path(directory)
    if not d.is_dir():
        raise NotADirectoryError("Not a directory: " + str(d))

    parser = TextureParser()
    infos = parser.parse_directory(d, extensions=extensions, recursive=recursive)

    # Library layout: the chosen folder is a parent of per-material sub-folders
    # (e.g. MSMC_Blobs/Blob_Dots/...).  If nothing was found at the top level
    # but sub-folders exist, recurse automatically so the user does not have to
    # open each sub-folder one by one.
    if not infos and not recursive and auto_recurse:
        has_subdirs = any(child.is_dir() for child in d.iterdir())
        if has_subdirs:
            _log.info("No textures at top level; recursing into sub-folders.")
            recursive = True
            infos = parser.parse_directory(
                d, extensions=extensions, recursive=True
            )

    # Collapse jpg/tx/rat variants of the same map to ONE, preferring the
    # Houdini-optimised .rat (then .tx) over the original source image.  Without
    # this, re-scanning a folder after conversion would pick an arbitrary
    # variant per channel (filesystem order) and the .mtlx would reference the
    # unoptimised source instead of the .rat.
    infos = _prefer_converted_infos(infos)

    unknowns = tuple(
        i.stem for i in infos if i.channel is TextureChannel.UNKNOWN
    )

    planner = MaterialPlanner(channels=channels)
    plans = tuple(planner.plan_from_infos(infos))

    result = ScanResult(
        directory=d,
        infos=tuple(infos),
        plans=plans,
        unknowns=unknowns,
    )
    _log.info("Scanned " + str(d) + ": " + result.summary())
    return result


def select_plans(
    result: ScanResult, names: Optional[List[str]] = None
) -> List[MaterialBuildPlan]:
    """Return the plans in *result* whose name is in *names* (all if ``None``).

    Args:
        result: A :class:`ScanResult`.
        names:  Material names to keep, or ``None`` for every plan.

    Returns:
        The matching list of :class:`MaterialBuildPlan`, order preserved.
    """
    if names is None:
        return list(result.plans)
    wanted = set(names)
    return [p for p in result.plans if p.name in wanted]


def format_dry_run(result: ScanResult) -> str:
    """Render a human-readable dry-run report of what would be built.

    Args:
        result: A :class:`ScanResult`.

    Returns:
        A multi-line string -- safe to print outside Houdini.
    """
    lines: List[str] = []
    lines.append("TexToMtlx dry-run for: " + str(result.directory))
    lines.append(result.summary())
    for plan in result.plans:
        lines.append("")
        lines.append("[material] " + plan.name)
        for img in plan.images:
            udim = "  (UDIM)" if img.is_udim else ""
            lines.append(
                "    " + img.channel.value.ljust(14)
                + " -> " + img.mtlx_input.ljust(20)
                + " cs=" + img.colorspace
                + " sig=" + img.signature + udim
            )
        if plan.warnings:
            for w in plan.warnings:
                lines.append("    ! " + w)
    if result.unknowns:
        lines.append("")
        lines.append("Unrecognised (skipped): " + ", ".join(result.unknowns))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Texture variant preference (.rat > .tx > source)
# ---------------------------------------------------------------------------
# When a folder has been converted, each logical map exists as several files,
# e.g. ``MSMC_Blob_Dots_Basecolor.{jpg,tx,rat}``.  Houdini renders .rat
# (tiled mip) most efficiently, so we prefer it; .tx next; the source last.

#: Higher rank wins.  Anything not listed is treated as a raw *source* (rank 0).
_VARIANT_RANK: Dict[str, int] = {"rat": 3, "tx": 2}

#: Source raster extensions whose token may trail a legacy ``name.png.rat`` stem.
_SOURCE_EXTS = frozenset({
    "exr", "tif", "tiff", "png", "jpg", "jpeg", "hdr", "dpx", "tga", "bmp",
})


def _variant_rank(info: TextureInfo) -> int:
    """Rank a texture variant; ``.rat`` highest, then ``.tx``, then source."""
    return _VARIANT_RANK.get((info.extension or "").lower(), 0)


def _variant_base(info: TextureInfo) -> str:
    """Return an extension-agnostic grouping base for a texture.

    Strips a trailing source-extension token so a legacy double-extension
    ``foo.png.rat`` groups with the original ``foo.png`` rather than splitting
    into its own material.
    """
    base = info.raw_name
    head, _, tail = base.rpartition(".")
    if head and tail in _SOURCE_EXTS:
        base = head
    return base


def _prefer_converted_infos(
    infos: List[TextureInfo],
) -> List[TextureInfo]:
    """Collapse duplicate variants of each map, preferring ``.rat`` then ``.tx``.

    Args:
        infos: Parsed texture infos (may contain jpg/tx/rat of the same map).

    Returns:
        One :class:`TextureInfo` per ``(folder, base-name, channel)``, keeping
        the highest-ranked variant.  Input order is otherwise preserved, so the
        UI listing stays stable.
    """
    chosen: Dict[Tuple[str, str, object], TextureInfo] = {}
    order: List[Tuple[str, str, object]] = []
    for info in infos:
        key = (
            info.path.parent.as_posix().lower(),
            _variant_base(info),
            info.channel,
        )
        current = chosen.get(key)
        if current is None:
            chosen[key] = info
            order.append(key)
        elif _variant_rank(info) > _variant_rank(current):
            chosen[key] = info
    return [chosen[k] for k in order]
