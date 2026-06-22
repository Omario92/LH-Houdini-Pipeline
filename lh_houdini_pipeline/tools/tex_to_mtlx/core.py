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
from typing import List, Optional, Tuple, Union

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
) -> ScanResult:
    """Scan *directory*, parse textures, and produce build plans (dry-run safe).

    Args:
        directory:  Folder containing texture files.
        recursive:  Recurse into subdirectories.
        channels:   Override which channels to plan (defaults to MVP set).
        extensions: Override texture extensions (passed to the parser).

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
