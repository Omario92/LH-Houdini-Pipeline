"""
lh_houdini_pipeline.tools.lops_asset_builder.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Houdini-side build of a USD component asset from an :class:`AssetBuildPlan`.

Creates, in ``/stage``::

    componentgeometry  ->  componentmaterial  ->  componentoutput
                              ^
                        materiallibrary  (mtlx networks via MtlxNetworkBuilder)

Node graph plumbing (create / connect / parm / multiparm / layout / save
button) is delegated to :mod:`lh_houdini_pipeline.houdini.lop`, keeping this
module focused on the *asset-specific* composition.  All ``hou`` use is lazy.

Node-type / parm names verified live on H21.0.631:
    * componentgeometry feeds geo through inner ``sopnet/geo`` (outputs
      ``default`` / ``proxy`` / ``simproxy``).
    * componentmaterial: input0 = stage, input1 = materials; multiparm
      ``nummaterials`` + ``primpattern#`` / ``matspecpath#``.
    * componentoutput: ``assetname`` / ``rootprim`` / ``lopoutput``; the
      Save-to-Disk button is ``execute`` (background: ``executebackground``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.houdini import lop as _lop
from lh_houdini_pipeline.materialx.builder import MtlxNetworkBuilder
from lh_houdini_pipeline.tools.lops_asset_builder.core import AssetBuildPlan

_log = get_logger(__name__)


@dataclass
class AssetBuildResult:
    """Paths of the nodes created for one asset.

    Attributes:
        asset_name:    The asset that was built.
        geometry:      componentgeometry node path.
        material_lib:  materiallibrary node path.
        assign:        componentmaterial node path.
        output:        componentoutput node path.
        materials_built: Names of materials created in the library.
    """
    asset_name:      str
    geometry:        str = ""
    material_lib:    str = ""
    assign:          str = ""
    output:          str = ""
    materials_built: tuple = field(default_factory=tuple)


def build_asset(
    plan: AssetBuildPlan,
    parent_path: str = "/stage",
    on_stage: Optional[Callable[[int, int, str], None]] = None,
) -> AssetBuildResult:
    """Build the component-asset LOP graph for *plan* under *parent_path*.

    Args:
        plan:        The pure :class:`AssetBuildPlan` to realise.
        parent_path: LOP network to build in (default ``/stage``).
        on_stage:    Optional ``on_stage(step, total, label)`` progress hook,
                     called on the calling (main) thread between build stages.

    Returns:
        An :class:`AssetBuildResult` with the created node paths.

    Raises:
        RuntimeError: If *parent_path* or a core node cannot be created.
    """
    import hou  # noqa: PLC0415

    parent = _lop.get_node(parent_path)
    if parent is None:
        raise RuntimeError("Build parent not found: " + parent_path)

    result = AssetBuildResult(asset_name=plan.asset_name)

    def _emit(step: int, label: str) -> None:
        if on_stage is not None:
            try:
                on_stage(step, 4, label)
            except Exception as exc:  # noqa: BLE001
                _log.debug("on_stage callback raised: " + str(exc))

    with hou.undos.group("Build asset " + plan.asset_name):
        _emit(1, "geometry")
        cg = _lop.create_node(parent, "componentgeometry", plan.asset_name + "_geo", force=True)
        _require(cg, "componentgeometry")
        _load_geometry(cg, plan)
        result.geometry = cg.path()

        _emit(2, "materials")
        matlib = _lop.create_node(parent, "materiallibrary", plan.asset_name + "_mtl", force=True)
        _require(matlib, "materiallibrary")
        prefix = _material_prefix(matlib)
        built = MtlxNetworkBuilder(force=True).build_all(matlib, list(plan.material_plans))
        result.material_lib = matlib.path()
        result.materials_built = tuple(r.material_name for r in built if r.created)

        _emit(3, "material assignment")
        cm = _lop.create_node(parent, "componentmaterial", plan.asset_name + "_assign", force=True)
        _require(cm, "componentmaterial")
        _lop.connect(cm, cg, 0)
        _lop.connect(cm, matlib, 1)
        _apply_assignments(cm, plan, prefix)
        result.assign = cm.path()

        _emit(4, "output")
        co = _lop.create_node(parent, "componentoutput", plan.asset_name, force=True)
        _require(co, "componentoutput")
        _lop.connect(co, cm, 0)
        _lop.set_parms(co, {"assetname": plan.asset_name, "rootprim": plan.root_prim})
        if plan.output_file:
            _lop.set_parm(co, "lopoutput", plan.output_file)
        result.output = co.path()

        _lop.layout(parent)

    _log.info(
        "Built asset '" + plan.asset_name + "': " + result.output
        + " (materials: " + ", ".join(result.materials_built) + ")"
    )
    return result


def save_asset(result: AssetBuildResult) -> bool:
    """Press componentoutput 'Save to Disk' (blocking) to write the USD.

    Args:
        result: An :class:`AssetBuildResult` from a previous build.

    Returns:
        ``True`` if a save button was pressed, ``False`` otherwise.
    """
    co = _lop.get_node(result.output)
    if co is None:
        _log.error("componentoutput node missing: " + result.output)
        return False
    return _lop.press_button(co, ("execute", "savetodisk", "save")) is not None


def save_asset_background(result: AssetBuildResult) -> bool:
    """Save the asset USD without blocking via Houdini's background execution.

    Args:
        result: An :class:`AssetBuildResult` from a previous build.

    Returns:
        ``True`` if a save was triggered, ``False`` otherwise.
    """
    co = _lop.get_node(result.output)
    if co is None:
        _log.error("componentoutput node missing: " + result.output)
        return False
    if _lop.press_button(co, ("executebackground",)) is not None:
        _log.info("Background save started: " + co.path())
        return True
    _log.info("No background save; falling back to blocking save.")
    return save_asset(result)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require(node: Any, what: str) -> None:
    """Raise if a required core node failed to create."""
    if node is None:
        raise RuntimeError("Could not create required node: " + what)


def _load_geometry(cg: Any, plan: AssetBuildPlan) -> None:
    """Load ``plan.geo_path`` into componentgeometry's inner ``sopnet/geo``.

    Creates a ``file`` SOP wired into the ``default`` output node.  Leaves the
    stock default geometry untouched when no geo path is given.
    """
    if plan.geo_path is None:
        return
    geo = cg.node("sopnet/geo")
    if geo is None:
        _log.warning("componentgeometry inner sopnet/geo not found; geo skipped.")
        return
    file_sop = _lop.create_node(geo, "file", "asset_geo")
    if file_sop is None:
        return
    _lop.set_parm(file_sop, "file", plan.geo_path.as_posix())
    default_out = geo.node("default")
    if default_out is not None:
        _lop.connect(default_out, file_sop, 0)
        
    if plan.generate_proxy:
        # Create a shrinkwrap SOP for the simulation proxy (convex hull)
        hull_sop = _lop.create_node(geo, "shrinkwrap", "sim_proxy")
        if hull_sop is not None:
            _lop.connect(hull_sop, file_sop, 0)
            sim_out = geo.node("simproxy")
            if sim_out is not None:
                _lop.connect(sim_out, hull_sop, 0)

        # Create a polyreduce SOP for the viewport proxy
        reduce_pct = {"Low": 10.0, "Medium": 30.0, "High": 60.0}.get(plan.proxy_quality, 30.0)
        reduce_sop = _lop.create_node(geo, "polyreduce", "viewport_proxy")
        if reduce_sop is not None:
            _lop.connect(reduce_sop, file_sop, 0)
            _lop.set_parm(reduce_sop, "percentage", reduce_pct)
            proxy_out = geo.node("proxy")
            if proxy_out is not None:
                _lop.connect(proxy_out, reduce_sop, 0)
                
    _lop.layout(geo)


def _material_prefix(matlib: Any) -> str:
    """Return the materiallibrary's prim-path prefix (always ends with '/')."""
    parm = matlib.parm("matpathprefix")
    prefix = parm.eval() if parm is not None else "/ASSET/mtl/"
    if not prefix:
        prefix = "/materials/"
    if not prefix.endswith("/"):
        prefix = prefix + "/"
    return prefix


def _apply_assignments(cm: Any, plan: AssetBuildPlan, prefix: str) -> None:
    """Populate componentmaterial's multiparm from the plan's assignments."""
    rows = [
        {"primpattern": a.primpattern, "matspecpath": prefix + a.material_name}
        for a in plan.assignments
    ]
    _lop.set_indexed_parms(cm, "nummaterials", rows)
