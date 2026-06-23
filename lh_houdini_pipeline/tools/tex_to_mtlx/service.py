"""
lh_houdini_pipeline.tools.tex_to_mtlx.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Houdini-side orchestration for TexToMtlx -- resolves a build context and
drives ``materialx.builder`` to create networks.

All ``hou`` usage is lazy (inside functions), so importing this module never
requires Houdini.  The UI imports it freely; the build calls only touch
``hou`` when actually invoked.

Context resolution
------------------
* In ``/stage`` (LOPs):   find or create a ``materiallibrary`` LOP and build
  the materials inside it.
* In ``/mat`` (VOP/matnet): build the material subnets directly under it.
* Otherwise: fall back to ``/mat`` so the tool still does something useful
  instead of failing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.core.profiling import timed
from lh_houdini_pipeline.houdini import lop as _lop
from lh_houdini_pipeline.materialx.builder import (
    BuildResult,
    MaterialBuildPlan,
    MtlxNetworkBuilder,
)
from lh_houdini_pipeline.materialx.tx import (
    MaketxConverter,
    MaketxPlanner,
    TxFormat,
    TxResult,
)

_log = get_logger(__name__)

_MATLIB_NAME = "tex_to_mtlx_lib"


@dataclass
class BuildContext:
    """Where materials will be built.

    Attributes:
        parent_path: Full path of the node materials are created under.
        kind:        ``"stage"`` (materiallibrary LOP) or ``"mat"`` (matnet).
    """
    parent_path: str
    kind:        str


def resolve_parent(prefer_path: Optional[str] = None) -> Any:
    """Resolve and return the ``hou.Node`` to build materials under.

    Args:
        prefer_path: Explicit node path to build into (e.g. an existing
                     materiallibrary or matnet).  When given, it is used as-is
                     if it exists.

    Returns:
        A ``hou.Node`` suitable as the ``parent`` for
        :meth:`MtlxNetworkBuilder.build_all`.

    Raises:
        RuntimeError: If no usable build parent can be resolved or created.
    """
    import hou  # noqa: PLC0415

    if prefer_path:
        node = _lop.get_node(prefer_path)
        if node is not None:
            _log.info("Using explicit build parent: " + node.path())
            return node
        _log.warning("prefer_path not found, auto-resolving: " + prefer_path)

    pwd = _lop.network_pwd()

    # Walk up from the current network to find the context category.
    if pwd is not None:
        category = pwd.type().category().name()
        if category == "Lop":
            return _ensure_material_library(pwd)
        if category == "Vop":
            # Inside a VOP/material network already -- build right here.
            _log.info("Building into current VOP network: " + pwd.path())
            return pwd
        if category == "Shop" or pwd.path() == "/mat":
            return pwd

    # Fallback: /mat always exists.
    mat = _lop.get_node("/mat")
    if mat is None:
        raise RuntimeError("Could not resolve a build context (/mat missing).")
    _log.info("Falling back to /mat for material build.")
    return mat


@timed("tex_to_mtlx.build_plans")
def build_plans(
    plans: List[MaterialBuildPlan],
    prefer_path: Optional[str] = None,
    force: bool = False,
) -> List[BuildResult]:
    """Build *plans* into the resolved context inside a single undo block.

    Args:
        plans:       Plans from the (pure) ``core``/``builder`` layer.
        prefer_path: Optional explicit parent node path.
        force:       Replace existing same-named materials.

    Returns:
        One :class:`BuildResult` per plan.
    """
    import hou  # noqa: PLC0415

    if not plans:
        _log.warning("build_plans called with no plans.")
        return []

    parent = resolve_parent(prefer_path)
    builder = MtlxNetworkBuilder(force=force)

    with hou.undos.group("TexToMtlx build " + str(len(plans)) + " material(s)"):
        results = builder.build_all(parent, plans)
    return results


@timed("tex_to_mtlx.convert_textures_to_tx")
def convert_textures_to_tx(
    infos,
    out_dir=None,
    tx_format: TxFormat = TxFormat.RAT,
    dry_run: bool = False,
    on_each=None,
) -> List[TxResult]:
    """Convert source textures to ``.tx``/``.rat`` via ``imaketx``.

    Thin orchestration over ``materialx.tx`` so the UI stays logic-free.

    Args:
        infos:     Iterable of :class:`TextureInfo` (e.g. ``ScanResult.infos``).
        out_dir:   Optional output directory; defaults to each source's folder.
        tx_format: Output format (default ``RAT``).
        dry_run:   Build/log commands without running ``imaketx``.
        on_each:   Optional ``on_each(done, total, tx_result)`` progress hook.

    Returns:
        One :class:`TxResult` per input texture.

    Note:
        Inputs whose extension already equals the target format (e.g. a ``.rat``
        when converting to ``RAT``) are skipped.  Re-running ``imaketx`` on an
        already-converted file would otherwise apply the colour transform a
        second time -- which double-linearises colour maps and darkens them.
    """
    target_ext = tx_format.extension.lower()
    source_infos = []
    skipped = 0
    for info in infos:
        if (info.extension or "").lower() == target_ext:
            skipped += 1
            continue
        source_infos.append(info)
    if skipped:
        _log.info(
            "imaketx: skipped " + str(skipped)
            + " already-" + target_ext + " texture(s) to avoid double conversion."
        )

    planner = MaketxPlanner(tx_format=tx_format)
    specs = planner.plan_many(source_infos, out_dir=out_dir)
    converter = MaketxConverter(dry_run=dry_run)
    results = converter.convert_many(specs, on_each=on_each)
    ok = sum(1 for r in results if r.success)
    _log.info("imaketx: " + str(ok) + "/" + str(len(results)) + " texture(s) converted.")
    return results


# ---------------------------------------------------------------------------
# Internal helpers (LOP plumbing delegated to houdini.lop)
# ---------------------------------------------------------------------------

def _ensure_material_library(lop_node: Any) -> Any:
    """Find or create a ``materiallibrary`` LOP near *lop_node* and return it.

    If *lop_node* is already a materiallibrary it is reused; otherwise one is
    created in the same parent network (and wired to *lop_node*) so materials
    land in /stage.
    """
    if lop_node.type().name() == "materiallibrary":
        return lop_node

    parent_net = lop_node.parent()
    matlib = _lop.find_or_create(parent_net, "materiallibrary", _MATLIB_NAME)
    if matlib is None:
        raise RuntimeError("Could not create materiallibrary under " + parent_net.path())
    _lop.connect(matlib, lop_node, 0)
    try:
        matlib.moveToGoodPosition()
    except Exception as exc:  # noqa: BLE001
        _log.debug("moveToGoodPosition skipped: " + str(exc))
    _log.info("Material library ready: " + matlib.path())
    return matlib
