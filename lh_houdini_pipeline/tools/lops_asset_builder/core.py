"""
lh_houdini_pipeline.tools.lops_asset_builder.core
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pure planning for a USD component asset -- NO ``hou``.

Produces an :class:`AssetBuildPlan` describing the LOP graph to create:

    componentgeometry  ->  componentmaterial  ->  componentoutput
                              ^
                        materiallibrary (built from a texture folder)

Reuses existing components:

    tools.tex_to_mtlx.core.scan_and_plan  -> material plans from a tex folder
    materialx.builder.MaterialBuildPlan   -> per-material plan objects

Being hou-free, this module backs a dry-run and is unit-testable with plain
``python``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import List, Optional, Tuple, Union

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.file.texture_parser import ColorSpace, TextureChannel, TextureInfo
from lh_houdini_pipeline.materialx.builder import MaterialBuildPlan, MaterialPlanner
from lh_houdini_pipeline.tools.tex_to_mtlx.core import scan_and_plan

PathLike = Union[str, Path]
_log = get_logger(__name__)

#: USD ascii/binary/auto extensions accepted for the output file.
_USD_EXTS = (".usd", ".usda", ".usdc")
_DATE_TOKEN_RE = re.compile(r"(?:(?<=^)|(?<=[_\-. ]))\d{8}(?=$|[_\-. ])")
_TEXTURE_SOURCE_EXTS = {
    ".exr", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".hdr", ".dpx",
}


@dataclass(frozen=True)
class MaterialAssignment:
    """Bind one material to prims matching a pattern.

    Attributes:
        primpattern:   USD primitive pattern (e.g. ``"%type:Mesh"`` or a path).
        material_name: Name of the material (resolved to a prim path at build).
    """
    primpattern:   str
    material_name: str


@dataclass(frozen=True)
class AssetBuildPlan:
    """Everything needed to build one USD component asset (hou-free).

    Attributes:
        asset_name:     Sanitised asset / root-prim name.
        geo_path:       Geometry file to load (``None`` keeps the default box).
        material_plans: Material plans to build into the material library.
        assignments:    Material-to-prim bindings.
        output_dir:     Directory for the written USD (``None`` = don't set).
        output_ext:     Output USD extension (default ``.usd``).
    """
    asset_name:     str
    geo_path:       Optional[Path]
    material_plans: Tuple[MaterialBuildPlan, ...] = field(default_factory=tuple)
    assignments:    Tuple[MaterialAssignment, ...] = field(default_factory=tuple)
    output_dir:     Optional[Path] = None
    output_ext:     str = ".usd"
    generate_proxy: bool = False
    proxy_quality:  str = "Medium"

    @property
    def root_prim(self) -> str:
        """The asset's USD root primitive path (``/asset_name``)."""
        return "/" + self.asset_name

    @property
    def output_file(self) -> Optional[str]:
        """Full output USD path (forward slashes), or ``None`` if no dir set."""
        if self.output_dir is None:
            return None
        return (self.output_dir / (self.asset_name + self.output_ext)).as_posix()

    def summary(self) -> str:
        """One-line human summary for logs / status labels."""
        geo = self.geo_path.name if self.geo_path else "(default geo)"
        return (
            "asset '" + self.asset_name + "' geo=" + geo
            + " materials=" + str(len(self.material_plans))
            + " assignments=" + str(len(self.assignments))
        )


def _safe_asset_name(name: str) -> str:
    """Sanitise *name* into a valid USD prim / node name."""
    out = []
    for ch in name.strip():
        out.append(ch if (ch.isalnum() or ch == "_") else "_")
    safe = "".join(out).strip("_")
    if not safe:
        safe = "asset"
    if safe[0].isdigit():
        safe = "a_" + safe
    return safe


def plan_asset(
    asset_name: str,
    geo_path: Optional[PathLike] = None,
    tex_folder: Optional[PathLike] = None,
    output_dir: Optional[PathLike] = None,
    assignments: Optional[List[MaterialAssignment]] = None,
    recursive: bool = False,
    output_ext: str = ".usd",
    generate_proxy: bool = False,
    proxy_quality: str = "Medium",
) -> AssetBuildPlan:
    """Build an :class:`AssetBuildPlan` from simple inputs (dry-run safe).

    Args:
        asset_name:  Desired asset name (sanitised).
        geo_path:    Optional geometry file (``.bgeo``/``.abc``/``.obj``...).
        tex_folder:  Optional texture folder; materials are planned from it via
                     the TexToMtlx scanner/planner.
        output_dir:  Optional directory for the written USD.
        assignments: Explicit material bindings.  When ``None`` and materials
                     exist, a sensible default is generated (see below).
        recursive:   Recurse into texture subfolders.
        output_ext:  Output USD extension (validated against USD types).

    Returns:
        A fully-populated :class:`AssetBuildPlan`.

    Raises:
        ValueError: If *output_ext* is not a USD extension.

    Default assignment rule:
        * No materials -> no assignments.
        * One material -> bind it to every mesh (``%type:Mesh``).
        * Many materials -> one binding per material to a same-named subset
          (``%type:Mesh & %name:<material>*``); refine per project as needed.
    """
    if output_ext not in _USD_EXTS:
        raise ValueError(
            "output_ext must be one of " + ", ".join(_USD_EXTS) + ", got " + output_ext
        )

    name = _safe_asset_name(asset_name)

    geo = Path(geo_path) if geo_path is not None else None
    material_plans: Tuple[MaterialBuildPlan, ...] = ()
    if tex_folder is not None:
        result = scan_and_plan(tex_folder, recursive=recursive)
        infos = _prefer_rat_infos(result.infos)
        if _is_fbx(geo):
            infos = _normalise_fbx_texture_infos(infos)
        material_plans = tuple(MaterialPlanner().plan_from_infos(list(infos)))
        if _should_promote_untagged_base_color(geo, infos, material_plans):
            material_plans = _plan_with_untagged_base_color(list(infos))
        _log.info("Asset '" + name + "' textures: " + result.summary())

    if assignments is not None:
        binds = tuple(assignments)
    else:
        binds = _default_assignments(material_plans)

    plan = AssetBuildPlan(
        asset_name=name,
        geo_path=geo,
        material_plans=material_plans,
        assignments=binds,
        output_dir=Path(output_dir) if output_dir is not None else None,
        output_ext=output_ext,
        generate_proxy=generate_proxy,
        proxy_quality=proxy_quality,
    )
    _log.info("Planned " + plan.summary())
    return plan


def _default_assignments(
    material_plans: Tuple[MaterialBuildPlan, ...]
) -> Tuple[MaterialAssignment, ...]:
    """Generate sensible default bindings for *material_plans*."""
    if not material_plans:
        return ()
    if len(material_plans) == 1:
        return (MaterialAssignment("%type:Mesh", material_plans[0].name),)
    return tuple(
        MaterialAssignment("%type:Mesh & %name:" + mp.name + "*", mp.name)
        for mp in material_plans
    )


def _should_promote_untagged_base_color(
    geo_path: Optional[Path],
    infos: Tuple[TextureInfo, ...],
    material_plans: Tuple[MaterialBuildPlan, ...],
) -> bool:
    """Return ``True`` when FBX textures need an untagged base-color fallback.

    FBX exports often ship one diffuse/base-color bitmap named only after the
    material, e.g. ``texture_pbr_20250901.png``.  The generic texture parser
    correctly marks that as ``UNKNOWN`` because it has no channel suffix, but
    for FBX asset assembly it is useful to treat it as base color when no other
    base-color texture exists in the folder.
    """
    if not _is_fbx(geo_path):
        return False
    if any(
        img.channel is TextureChannel.BASE_COLOR
        for plan in material_plans
        for img in plan.images
    ):
        return False
    return any(info.channel is TextureChannel.UNKNOWN for info in infos)


def _plan_with_untagged_base_color(infos: List[TextureInfo]) -> Tuple[MaterialBuildPlan, ...]:
    """Promote unrecognised textures to base-color and re-run material planning.

    Args:
        infos: Texture infos from the original scan.

    Returns:
        Replanned materials where untagged textures act as base-color maps.
    """
    promoted: List[TextureInfo] = []
    for info in infos:
        if info.channel is TextureChannel.UNKNOWN:
            promoted.append(
                replace(
                    info,
                    channel=TextureChannel.BASE_COLOR,
                    colorspace=ColorSpace.SRGB,
                    warnings=info.warnings + ("Promoted untagged FBX texture to baseColor.",),
                )
            )
        else:
            promoted.append(info)
    return tuple(MaterialPlanner().plan_from_infos(promoted))


def _is_fbx(path: Optional[Path]) -> bool:
    """Return ``True`` when *path* points to an FBX file."""
    return path is not None and path.suffix.lower() == ".fbx"


def _prefer_rat_infos(infos: Tuple[TextureInfo, ...]) -> Tuple[TextureInfo, ...]:
    """Prefer converted ``.rat`` textures over same-stem source images.

    Args:
        infos: Parsed texture infos from the texture folder.

    Returns:
        Texture infos with source images replaced by matching ``.rat`` files.
    """
    chosen = {}
    order = []
    for info in infos:
        key = (info.path.parent.as_posix().lower(), _rat_preference_stem(info).lower())
        if key not in chosen:
            order.append(key)
            chosen[key] = info
            continue
        current = chosen[key]
        if _rat_rank(info) > _rat_rank(current):
            chosen[key] = info
    return tuple(chosen[key] for key in order)


def _normalise_fbx_texture_infos(infos: Tuple[TextureInfo, ...]) -> Tuple[TextureInfo, ...]:
    """Normalize FBX texture names so date tokens do not split materials.

    Args:
        infos: Parsed texture infos.

    Returns:
        Infos with 8-digit date/version tokens removed from ``raw_name``.
    """
    normalized: List[TextureInfo] = []
    for info in infos:
        raw = _strip_date_tokens(info.raw_name)
        normalized.append(replace(info, raw_name=raw))
    return tuple(normalized)


def _strip_date_tokens(name: str) -> str:
    """Remove standalone 8-digit date/version tokens from a texture stem."""
    stripped = _DATE_TOKEN_RE.sub("", name)
    stripped = re.sub(r"[_\-. ]{2,}", "_", stripped)
    return stripped.strip("_-. ")


def _rat_preference_stem(info: TextureInfo) -> str:
    """Return a comparison stem that treats legacy ``.png.rat`` as ``.rat``."""
    stem = info.stem
    if info.extension == "rat":
        inner_suffix = Path(stem).suffix.lower()
        if inner_suffix in _TEXTURE_SOURCE_EXTS:
            return Path(stem).stem
    return stem


def _rat_rank(info: TextureInfo) -> int:
    """Rank texture variants, preferring clean converted ``.rat`` names."""
    if info.extension != "rat":
        return 0
    inner_suffix = Path(info.stem).suffix.lower()
    if inner_suffix in _TEXTURE_SOURCE_EXTS:
        return 1
    return 2
