"""
lh_houdini_pipeline.houdini.geometry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SOP geometry inspection: bounding box, point/prim counts, attribute queries.

Production reasoning
--------------------
The asset-ingestion pipeline (Week 04) classifies parts of an imported mesh by
*size* -- trunk vs branch vs leaf -- using bounding boxes, and detects wrong
scale by comparing bbox diagonal against an expected real-world size.  These
read-only helpers wrap the noisy ``hou`` geometry API in typed,
frozen-dataclass results so the pure-domain layers can reason about geometry
without touching ``hou`` themselves.

All helpers are *read-only* -- they never cook-with-side-effects or mutate
geometry; they call ``geometry()`` on an already-cooked SOP.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    import hou


@dataclass(frozen=True)
class BBox:
    """An axis-aligned bounding box result (frozen value object).

    Attributes:
        min_pt:   (x, y, z) minimum corner.
        max_pt:   (x, y, z) maximum corner.
        size:     (sx, sy, sz) dimensions.
        center:   (cx, cy, cz) centroid.
        diagonal: Length of the box diagonal (a scale-invariant size proxy).
    """

    min_pt: Tuple[float, float, float]
    max_pt: Tuple[float, float, float]
    size: Tuple[float, float, float]
    center: Tuple[float, float, float]
    diagonal: float


def _resolve_geo(node: "hou.Node") -> "hou.Geometry":
    """Return the display/render geometry of a SOP *node*.

    Raises:
        ValueError: If the node has no geometry (not a SOP, or uncooked).
    """
    geo = node.geometry()
    if geo is None:
        raise ValueError(
            "Node " + node.path() + " has no geometry "
            "(not a SOP, or it has not cooked)."
        )
    return geo


def bbox(node: "hou.Node") -> BBox:
    """Compute the bounding box of a SOP node's geometry.

    Returns:
        A frozen :class:`BBox`.  ``diagonal`` is handy for scale checks:
        a model whose diagonal is ~1000 when you expected ~1.8 (metres) is
        almost certainly in centimetres or mis-scaled on import.
    """
    geo = _resolve_geo(node)
    b = geo.boundingBox()
    mn = (b.minvec()[0], b.minvec()[1], b.minvec()[2])
    mx = (b.maxvec()[0], b.maxvec()[1], b.maxvec()[2])
    size = (mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2])
    center = (b.center()[0], b.center()[1], b.center()[2])
    diag = (size[0] ** 2 + size[1] ** 2 + size[2] ** 2) ** 0.5
    return BBox(min_pt=mn, max_pt=mx, size=size, center=center, diagonal=diag)


def point_count(node: "hou.Node") -> int:
    """Return the number of points in the SOP geometry (O(1) -- intrinsic)."""
    return _resolve_geo(node).intrinsicValue("pointcount")


def prim_count(node: "hou.Node") -> int:
    """Return the number of primitives in the SOP geometry (O(1) -- intrinsic)."""
    return _resolve_geo(node).intrinsicValue("primitivecount")


def point_attribs(node: "hou.Node") -> List[str]:
    """Return point-attribute names (e.g. for validating ``N``/``uv`` presence)."""
    return [a.name() for a in _resolve_geo(node).pointAttribs()]


def prim_attribs(node: "hou.Node") -> List[str]:
    """Return primitive-attribute names (e.g. ``shop_materialpath``)."""
    return [a.name() for a in _resolve_geo(node).primAttribs()]


def material_paths(node: "hou.Node", attrib: str = "shop_materialpath") -> List[str]:
    """Return the distinct material-path values across primitives.

    This is the exact signal Week 04/06 use to split a mesh into per-material
    chunks before USD componentisation.  Returns an **empty list** (not an
    error) when the attribute is absent -- a non-fatal lookup.

    Args:
        node:   A cooked SOP node.
        attrib: Primitive string attribute holding material assignments.
    """
    geo = _resolve_geo(node)
    if geo.findPrimAttrib(attrib) is None:
        return []
    # set() dedupes; sorted() gives stable, diff-friendly output.
    return sorted({prim.attribValue(attrib) for prim in geo.prims()})
