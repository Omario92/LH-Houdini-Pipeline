"""
lh_houdini_pipeline.houdini.usd
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
LOP / USD stage helpers: stage access and world-bounds computation.

Production reasoning
--------------------
Lookdev automation (light rig, turntable) repeatedly needs the same fact: the
asset's world-space bounding box, so lights and cameras can be *sized to the
subject* instead of hardcoded.  Week 07-10 compute this via
``UsdGeom.BBoxCache``.  Centralising it here (the ``houdini/`` layer) means both
the light rig and the camera framer share one correct implementation rather
than each carrying its own copy.

``hou`` and ``pxr`` are imported lazily; the module imports for unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    import hou


@dataclass(frozen=True)
class WorldBounds:
    """Axis-aligned world bounds of a USD prim (frozen value object).

    Attributes:
        min_pt:  (x, y, z) minimum corner.
        max_pt:  (x, y, z) maximum corner.
        center:  (x, y, z) centroid.
        size:    (sx, sy, sz) dimensions.
        max_dim: Largest dimension -- the scale handle for rigs/cameras.
    """

    min_pt: Tuple[float, float, float]
    max_pt: Tuple[float, float, float]
    center: Tuple[float, float, float]
    size: Tuple[float, float, float]
    max_dim: float


def stage_of(node: "hou.Node") -> Optional["object"]:
    """Return the USD stage a LOP *node* produces, or ``None`` if unavailable."""
    if node is None or not hasattr(node, "stage"):
        return None
    try:
        return node.stage()
    except Exception:  # noqa: BLE001
        return None


def compute_world_bounds(
    node: "hou.Node",
    prim_path: Optional[str] = None,
) -> Optional[WorldBounds]:
    """Compute world bounds of *prim_path* (or the default prim) on *node*'s stage.

    Uses ``UsdGeom.BBoxCache`` over the ``default`` and ``render`` purposes --
    the same purposes Houdini's own framing uses, so results match the viewport.

    Args:
        node:      A LOP node whose output stage to inspect.
        prim_path: Prim to bound; ``None`` uses the stage's default prim
                   (falling back to the pseudo-root, i.e. the whole stage).

    Returns:
        A :class:`WorldBounds`, or ``None`` if bounds cannot be computed
        (no stage, empty stage, or an API error) -- callers fall back to
        explicit values.
    """
    stage = stage_of(node)
    if stage is None:
        return None
    try:
        from pxr import Usd, UsdGeom  # noqa: PLC0415

        if prim_path:
            prim = stage.GetPrimAtPath(prim_path)
        else:
            prim = stage.GetDefaultPrim() or stage.GetPseudoRoot()
        if not prim or not prim.IsValid():
            return None

        cache = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            [UsdGeom.Tokens.default_, UsdGeom.Tokens.render],
        )
        rng = cache.ComputeWorldBound(prim).ComputeAlignedRange()
        if rng.IsEmpty():
            return None
        mn, mx = rng.GetMin(), rng.GetMax()
        min_pt = (mn[0], mn[1], mn[2])
        max_pt = (mx[0], mx[1], mx[2])
        size = (mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2])
        center = ((mn[0] + mx[0]) / 2.0, (mn[1] + mx[1]) / 2.0, (mn[2] + mx[2]) / 2.0)
        max_dim = max(size)
        return WorldBounds(min_pt, max_pt, center, size, max_dim)
    except Exception:  # noqa: BLE001
        return None
