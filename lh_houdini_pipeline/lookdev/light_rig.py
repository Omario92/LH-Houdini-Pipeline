"""
lh_houdini_pipeline.lookdev.light_rig
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Programmatic studio light rig (Rebelway Week 07-08).

Production reasoning
--------------------
A lookdev light rig must *hug the asset*: a 3-point setup placed in absolute
world units looks wrong the moment the asset's scale changes.  So the geometry
of the rig (where each light sits, how far, how bright) is derived from the
asset's bounding box.  That derivation is pure trigonometry and lives here,
unit-testable, in two halves:

* :func:`three_point_rig` -- pure: turn ``(center, max_dim)`` into Key/Fill/Rim
  :class:`LightSpec` objects (position + look-at rotation + intensity).
* :func:`build_light_rig` -- hou: realise those specs as USD light LOPs in
  Solaris, optionally adding a dome (HDRI) for ambient fill.

Look-at math
------------
A USD light points down its local -Z.  To aim a light at ``center`` from
``position`` we need yaw (around Y) and pitch (around X):

    dir = center - position
    yaw   = atan2(dir.x, -dir.z)
    pitch = atan2(dir.y, hypot(dir.x, dir.z))

(``rz`` stays 0 -- roll is irrelevant for a single light.)

Domain layer: imports only ``houdini/`` (never ``tools/``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Tuple

from lh_houdini_pipeline.core.logger import get_logger

if TYPE_CHECKING:
    import hou

_log = get_logger(__name__)

Vec3 = Tuple[float, float, float]


class LightRole(str, Enum):
    """The role of a light in a 3-point rig."""

    KEY = "key"
    FILL = "fill"
    RIM = "rim"
    DOME = "dome"


@dataclass(frozen=True)
class LightSpec:
    """A single light's placement + look, resolved from the asset bounds (pure).

    Attributes:
        name:       Node/prim name.
        role:       :class:`LightRole`.
        light_type: USD light token (e.g. ``"UsdLuxSphereLight"``).
        position:   World-space (x, y, z).
        rotation:   Euler (rx, ry, rz) degrees aiming the light at the subject.
        intensity:  Light intensity (linear).
        exposure:   Light exposure (stops); total = intensity * 2**exposure.
    """

    name: str
    role: LightRole
    light_type: str
    position: Vec3
    rotation: Vec3
    intensity: float
    exposure: float


@dataclass(frozen=True)
class LightRigPlan:
    """A full rig: the three key lights plus optional dome (pure value object)."""

    lights: Tuple[LightSpec, ...] = field(default_factory=tuple)
    dome_hdri: Optional[str] = None
    dome_intensity: float = 1.0


# ---------------------------------------------------------------------------
# Pure geometry
# ---------------------------------------------------------------------------

def look_at_rotation(position: Vec3, center: Vec3) -> Vec3:
    """Return Euler ``(rx, ry, rz)`` degrees aiming a -Z light from *position* at *center*.

    See module docstring for the derivation.  Returns ``(0, 0, 0)`` for a
    degenerate zero-length direction.
    """
    dx = center[0] - position[0]
    dy = center[1] - position[1]
    dz = center[2] - position[2]
    if dx == 0.0 and dy == 0.0 and dz == 0.0:
        return (0.0, 0.0, 0.0)
    yaw = math.degrees(math.atan2(dx, -dz))
    pitch = math.degrees(math.atan2(dy, math.hypot(dx, dz)))
    return (pitch, yaw, 0.0)


def three_point_rig(
    center: Vec3,
    max_dim: float,
    *,
    distance_factor: float = 2.2,
    key_intensity: float = 1.0,
    key_exposure: float = 6.0,
    fill_ratio: float = 0.4,
    rim_ratio: float = 0.7,
) -> List[LightSpec]:
    """Build pure Key/Fill/Rim :class:`LightSpec` objects sized to the asset.

    Layout (subject faces +Z, camera at +Z):

    * **Key**  -- front, camera-right, raised; brightest.
    * **Fill** -- front, camera-left, slightly raised; ``fill_ratio`` of key.
    * **Rim**  -- behind, raised; ``rim_ratio`` of key, separates subject from bg.

    Args:
        center:          Asset world center.
        max_dim:         Asset's largest dimension (the scale handle).
        distance_factor: Light distance as a multiple of *max_dim*.
        key_intensity:   Key light base intensity.
        key_exposure:    Key light exposure (stops).
        fill_ratio:      Fill intensity as a fraction of the key.
        rim_ratio:       Rim intensity as a fraction of the key.

    Returns:
        ``[key, fill, rim]`` light specs.
    """
    d = max(max_dim, 0.001) * distance_factor
    cx, cy, cz = center

    # Offsets are unit directions * d; chosen for a classic 3-point look.
    offsets = {
        LightRole.KEY:  (0.8, 0.7, 0.9),    # front-right-up
        LightRole.FILL: (-0.9, 0.3, 0.7),   # front-left, low
        LightRole.RIM:  (0.2, 0.9, -1.0),   # behind-up
    }
    intensities = {
        LightRole.KEY:  key_intensity,
        LightRole.FILL: key_intensity * fill_ratio,
        LightRole.RIM:  key_intensity * rim_ratio,
    }

    specs: List[LightSpec] = []
    for role in (LightRole.KEY, LightRole.FILL, LightRole.RIM):
        ox, oy, oz = offsets[role]
        pos = (cx + ox * d, cy + oy * d, cz + oz * d)
        specs.append(
            LightSpec(
                name=role.value + "_light",
                role=role,
                light_type="UsdLuxSphereLight",
                position=pos,
                rotation=look_at_rotation(pos, center),
                intensity=intensities[role],
                exposure=key_exposure,
            )
        )
    return specs


def plan_rig(
    center: Vec3,
    max_dim: float,
    dome_hdri: Optional[str] = None,
    **kwargs: float,
) -> LightRigPlan:
    """Compose a full :class:`LightRigPlan` (3 lights + optional dome)."""
    return LightRigPlan(
        lights=tuple(three_point_rig(center, max_dim, **kwargs)),
        dome_hdri=dome_hdri,
    )


# ---------------------------------------------------------------------------
# hou builder
# ---------------------------------------------------------------------------

def _resolve_value_parm(node: "hou.Node", contains: str):
    """Find a light's value parm by substring, skipping the ``_control_`` toggle.

    Karma light parms carry build-specific name suffixes
    (``xn__inputsintensity_i0a``); resolving by substring is robust to those
    differences instead of hardcoding a fragile token.
    """
    best = None
    for p in node.parms():
        nm = p.name().lower()
        if contains in nm and "_control_" not in nm:
            best = p
            break
    return best


def build_light_rig(
    plan: LightRigPlan,
    parent_path: str = "/stage",
    target_path: Optional[str] = None,
    name_prefix: str = "rig_",
) -> List[str]:
    """Realise a :class:`LightRigPlan` as USD light LOPs under *parent_path*.

    When *target_path* is a LOP node, the rig is re-derived from that stage's
    world bounds so it frames whatever is actually there (the *plan* passed in
    is then used only for its dome/ratio settings).

    Args:
        plan:        The rig to build (may be re-derived from bounds).
        parent_path: LOP network to build in (``/stage``).
        target_path: Optional LOP node to size the rig to.
        name_prefix: Node-name prefix to namespace the rig.

    Returns:
        List of created light node paths.
    """
    from lh_houdini_pipeline.houdini import lop as _lop
    from lh_houdini_pipeline.houdini import parm as _parm
    from lh_houdini_pipeline.houdini import usd as _usd

    parent = _lop.get_node(parent_path)
    if parent is None:
        _log.error("build_light_rig: parent not found: " + parent_path)
        return []

    # Re-derive geometry from live bounds when a target is given.
    lights = list(plan.lights)
    if target_path:
        wb = _usd.compute_world_bounds(_lop.get_node(target_path))
        if wb is not None:
            lights = three_point_rig(wb.center, wb.max_dim)
            _log.info("Light rig framed to " + target_path
                      + " center=" + str(tuple(round(c, 2) for c in wb.center))
                      + " max_dim=" + str(round(wb.max_dim, 3)))

    created: List[str] = []
    prev = _lop.get_node(target_path) if target_path else None

    for spec in lights:
        node = _lop.create_node(parent, "light::2.0", name_prefix + spec.name, force=True)
        if node is None:
            continue
        # Chain lights so each layers onto the asset stage (USD sublayering).
        if prev is not None:
            try:
                node.setInput(0, prev)
            except Exception:  # noqa: BLE001
                pass
        prev = node

        _parm.try_set_parm(node, "lighttype", spec.light_type)
        # transform
        for pn, val in (("tx", spec.position[0]), ("ty", spec.position[1]),
                        ("tz", spec.position[2]), ("rx", spec.rotation[0]),
                        ("ry", spec.rotation[1]), ("rz", spec.rotation[2])):
            p = node.parm(pn)
            if p is not None:
                p.set(val)
        # intensity / exposure via resolved parm names
        ip = _resolve_value_parm(node, "inputsintensity")
        if ip is not None:
            ip.set(spec.intensity)
        ep = _resolve_value_parm(node, "inputsexposure")
        if ep is not None:
            ep.set(spec.exposure)
        created.append(node.path())

    # Optional dome (HDRI) for ambient fill.
    if plan.dome_hdri:
        dome = _lop.create_node(parent, "domelight::2.0", name_prefix + "dome", force=True)
        if dome is not None:
            if prev is not None:
                try:
                    dome.setInput(0, prev)
                except Exception:  # noqa: BLE001
                    pass
            tp = _resolve_value_parm(dome, "inputstexturefile")
            if tp is not None:
                tp.set(plan.dome_hdri)
            dp = _resolve_value_parm(dome, "inputsintensity")
            if dp is not None:
                dp.set(plan.dome_intensity)
            created.append(dome.path())

    _lop.layout(parent)
    _log.info("build_light_rig created " + str(len(created)) + " light(s).")
    return created
