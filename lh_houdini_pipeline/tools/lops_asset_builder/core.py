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

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Union

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.materialx.builder import MaterialBuildPlan
from lh_houdini_pipeline.tools.tex_to_mtlx.core import scan_and_plan

PathLike = Union[str, Path]
_log = get_logger(__name__)

#: USD ascii/binary/auto extensions accepted for the output file.
_USD_EXTS = (".usd", ".usda", ".usdc")


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

    material_plans: Tuple[MaterialBuildPlan, ...] = ()
    if tex_folder is not None:
        result = scan_and_plan(tex_folder, recursive=recursive)
        material_plans = result.plans
        _log.info("Asset '" + name + "' textures: " + result.summary())

    if assignments is not None:
        binds = tuple(assignments)
    else:
        binds = _default_assignments(material_plans)

    plan = AssetBuildPlan(
        asset_name=name,
        geo_path=Path(geo_path) if geo_path is not None else None,
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
