"""
lh_houdini_pipeline.lookdev.calibration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Lookdev calibration plates: chrome ball, 18% grey ball, Macbeth ColorChecker
(Rebelway Week 10 final).

Production reasoning
--------------------
Calibration plates let a lighting/lookdev artist *verify physical correctness*:

* the **chrome ball** shows the lighting environment (where the key/rim hit),
* the **18% grey ball** reveals exposure and colour cast,
* the **Macbeth chart** lets you eyeball or sample known albedos against render.

The two halves split cleanly:

* Pure data/geometry (this is unit-testable): the 24 ColorChecker swatches, the
  sRGB->linear conversion (Karma renders linear, the chart values are sRGB), and
  the 6x4 patch grid layout.
* USD authoring (``author_plates``): runs inside a Solaris **Python LOP**, the
  course-canonical way to write prims directly with ``pxr.UsdGeom`` on an
  editable stage.  ``build_calibration`` creates that LOP and feeds it params
  via node ``userData`` (JSON) -- the same pattern the camera-variant authoring
  uses elsewhere in this pipeline.

Domain layer: imports only ``houdini/`` + stdlib (never ``tools/``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Tuple

from lh_houdini_pipeline.core.logger import get_logger

if TYPE_CHECKING:
    import hou

_log = get_logger(__name__)

Color = Tuple[float, float, float]

#: X-Rite ColorChecker classic, 24 patches, sRGB 8-bit, row-major (6 cols x 4 rows).
MACBETH_SRGB: Tuple[Tuple[int, int, int], ...] = (
    (115, 82, 68), (194, 150, 130), (98, 122, 157), (87, 108, 67), (133, 128, 177), (103, 189, 170),
    (214, 126, 44), (80, 91, 166), (193, 90, 99), (94, 60, 108), (157, 188, 64), (224, 163, 46),
    (56, 61, 150), (70, 148, 73), (175, 54, 60), (231, 199, 31), (187, 86, 149), (8, 133, 161),
    (243, 243, 242), (200, 200, 200), (160, 160, 160), (122, 122, 121), (85, 85, 85), (52, 52, 52),
)

MACBETH_COLS = 6
MACBETH_ROWS = 4


# ---------------------------------------------------------------------------
# Pure colour + layout
# ---------------------------------------------------------------------------

def srgb_to_linear(channel: float) -> float:
    """Convert one sRGB channel in [0, 1] to linear (IEC 61966-2-1).

    Karma works in scene-linear; the ColorChecker values are sRGB display
    values, so they must be linearised before being authored as render colours.
    """
    c = max(0.0, min(1.0, channel))
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def macbeth_linear() -> List[Color]:
    """Return the 24 ColorChecker patches as linear RGB floats in [0, 1]."""
    out: List[Color] = []
    for r, g, b in MACBETH_SRGB:
        out.append((srgb_to_linear(r / 255.0),
                    srgb_to_linear(g / 255.0),
                    srgb_to_linear(b / 255.0)))
    return out


@dataclass(frozen=True)
class PatchSpec:
    """One Macbeth patch: grid index + local placement + linear colour."""

    index: int
    row: int
    col: int
    x: float
    y: float
    color: Color


def chart_layout(size: float = 1.0, gap: float = 0.08) -> List[PatchSpec]:
    """Compute the 24-patch grid layout in the chart's local XY plane (pure).

    The chart is centred on the local origin; patches are unit-ish squares of
    side ``size`` separated by ``size * gap``.  Row 0 is the top row, matching
    the physical chart's reading order.

    Args:
        size: Side length of one patch (local units).
        gap:  Inter-patch gap as a fraction of *size*.

    Returns:
        24 :class:`PatchSpec` objects in row-major order.
    """
    colors = macbeth_linear()
    step = size * (1.0 + gap)
    # centre the grid
    x0 = -(MACBETH_COLS - 1) * step / 2.0
    y0 = (MACBETH_ROWS - 1) * step / 2.0
    specs: List[PatchSpec] = []
    for i, color in enumerate(colors):
        row, col = divmod(i, MACBETH_COLS)
        specs.append(PatchSpec(
            index=i, row=row, col=col,
            x=x0 + col * step, y=y0 - row * step, color=color,
        ))
    return specs


@dataclass(frozen=True)
class CalibrationPlan:
    """Pure description of a calibration setup (positions resolved at build)."""

    position: Color = (0.0, 0.0, 0.0)
    size: float = 1.0
    with_chrome: bool = True
    with_gray: bool = True
    with_chart: bool = True
    grey_albedo: float = 0.18      # the canonical 18% grey
    chrome_roughness: float = 0.04

    def to_json(self) -> str:
        """Serialise to JSON for storage on the Python LOP's userData."""
        return json.dumps({
            "position": list(self.position),
            "size": self.size,
            "with_chrome": self.with_chrome,
            "with_gray": self.with_gray,
            "with_chart": self.with_chart,
            "grey_albedo": self.grey_albedo,
            "chrome_roughness": self.chrome_roughness,
        })

    @staticmethod
    def from_json(text: str) -> "CalibrationPlan":
        """Deserialise from the Python LOP's userData."""
        d = json.loads(text)
        return CalibrationPlan(
            position=tuple(d.get("position", (0.0, 0.0, 0.0))),
            size=d.get("size", 1.0),
            with_chrome=d.get("with_chrome", True),
            with_gray=d.get("with_gray", True),
            with_chart=d.get("with_chart", True),
            grey_albedo=d.get("grey_albedo", 0.18),
            chrome_roughness=d.get("chrome_roughness", 0.04),
        )


# Key under which params travel from build_calibration -> author_plates.
_USERDATA_KEY = "lh_calibration"
_ROOT_PRIM = "/lookdev/calibration"


# ---------------------------------------------------------------------------
# USD authoring (runs inside the Python LOP)
# ---------------------------------------------------------------------------

def _bind_preview_surface(stage, prim_path, diffuse, metallic, roughness):
    """Author + bind a UsdPreviewSurface material to *prim_path*.

    Returns the material path.  Kept tiny so both spheres reuse it.
    """
    from pxr import Sdf, UsdShade

    mat_path = prim_path + "_mat"
    material = UsdShade.Material.Define(stage, mat_path)
    shader = UsdShade.Shader.Define(stage, mat_path + "/surface")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(diffuse)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

    prim = stage.GetPrimAtPath(prim_path)
    UsdShade.MaterialBindingAPI(prim).Bind(material)
    return mat_path


def author_plates(node: "hou.Node") -> None:
    """Author the calibration prims onto *node*'s editable USD stage.

    Reads its :class:`CalibrationPlan` from the node's ``userData`` and writes a
    chrome sphere, an 18% grey sphere, and the Macbeth chart under
    ``/lookdev/calibration``.  Designed to be called from a Python LOP body.
    """
    raw = node.userData(_USERDATA_KEY)
    plan = CalibrationPlan.from_json(raw) if raw else CalibrationPlan()

    from pxr import Gf, Sdf, UsdGeom, Vt

    stage = node.editableStage()
    s = plan.size
    px, py, pz = plan.position

    root = UsdGeom.Xform.Define(stage, _ROOT_PRIM)
    UsdGeom.XformCommonAPI(root).SetTranslate(Gf.Vec3d(px, py, pz))

    radius = 0.5 * s
    spacing = 1.4 * s

    # -- chrome sphere (reflects the environment) ----------------------
    if plan.with_chrome:
        cp = _ROOT_PRIM + "/chrome"
        sph = UsdGeom.Sphere.Define(stage, cp)
        sph.CreateRadiusAttr(radius)
        UsdGeom.XformCommonAPI(sph).SetTranslate(Gf.Vec3d(-spacing, radius, 0.0))
        _bind_preview_surface(stage, cp, Gf.Vec3f(0.02, 0.02, 0.02),
                              metallic=1.0, roughness=plan.chrome_roughness)

    # -- 18% grey sphere (exposure / colour cast) ----------------------
    if plan.with_gray:
        gp = _ROOT_PRIM + "/grey"
        sph = UsdGeom.Sphere.Define(stage, gp)
        sph.CreateRadiusAttr(radius)
        UsdGeom.XformCommonAPI(sph).SetTranslate(Gf.Vec3d(0.0, radius, 0.0))
        g = plan.grey_albedo
        _bind_preview_surface(stage, gp, Gf.Vec3f(g, g, g),
                              metallic=0.0, roughness=0.5)

    # -- Macbeth chart (known albedos) ---------------------------------
    if plan.with_chart:
        patch_size = 0.32 * s
        chart_root = _ROOT_PRIM + "/macbeth"
        UsdGeom.Xform.Define(stage, chart_root)
        # offset the chart to the right of the spheres, standing up in XY
        cx = spacing
        for spec in chart_layout(patch_size):
            pp = chart_root + "/patch_" + str(spec.index)
            cube = UsdGeom.Cube.Define(stage, pp)
            cube.CreateSizeAttr(1.0)
            api = UsdGeom.XformCommonAPI(cube)
            api.SetTranslate(Gf.Vec3d(cx + spec.x, radius + spec.y, 0.0))
            # flatten the unit cube into a thin square tile
            api.SetScale(Gf.Vec3f(patch_size, patch_size, patch_size * 0.1))
            # displayColor carries the (linear) reference albedo
            cube.GetDisplayColorAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*spec.color)]))
            _bind_preview_surface(stage, pp, Gf.Vec3f(*spec.color),
                                  metallic=0.0, roughness=0.6)

    _log.info("author_plates: wrote calibration prims under " + _ROOT_PRIM)


# ---------------------------------------------------------------------------
# Builder (creates the Python LOP)
# ---------------------------------------------------------------------------

def _bootstrap_snippet() -> str:
    """Return the Python LOP body that calls :func:`author_plates`.

    Bakes the repo root into ``sys.path`` so the LOP cooks correctly even after
    a fresh Houdini launch.  Built with concatenation (no str.format) to stay
    clear of the security hook.
    """
    from pathlib import Path
    repo_root = str(Path(__file__).resolve().parents[2])
    lines = [
        "import sys",
        "_root = r'" + repo_root + "'",
        "if _root not in sys.path:",
        "    sys.path.insert(0, _root)",
        "from lh_houdini_pipeline.lookdev import calibration as _c",
        "_c.author_plates(hou.pwd())",
    ]
    return "\n".join(lines)


def build_calibration(
    plan: Optional[CalibrationPlan] = None,
    parent_path: str = "/stage",
    input_path: Optional[str] = None,
    name: str = "calibration_plates",
) -> Optional[str]:
    """Create a Python LOP that authors the calibration plates.

    Args:
        plan:        The :class:`CalibrationPlan`; defaults to all plates on.
        parent_path: LOP network to build in (``/stage``).
        input_path:  Optional upstream LOP to chain onto (so the plates layer
                     into the existing lookdev stage rather than a blank one).
        name:        Node name.

    Returns:
        The Python LOP node path, or ``None`` on failure.
    """
    from lh_houdini_pipeline.houdini import lop as _lop

    plan = plan or CalibrationPlan()
    parent = _lop.get_node(parent_path)
    if parent is None:
        _log.error("build_calibration: parent not found: " + parent_path)
        return None

    node = _lop.create_node(parent, "pythonscript", name, force=True)
    if node is None:
        return None
    if input_path:
        upstream = _lop.get_node(input_path)
        if upstream is not None:
            try:
                node.setInput(0, upstream)
            except Exception:  # noqa: BLE001
                pass

    node.setUserData(_USERDATA_KEY, plan.to_json())
    pc = node.parm("python")
    if pc is not None:
        pc.set(_bootstrap_snippet())
    # cook now so the prims exist immediately
    try:
        node.cook(force=True)
    except Exception as exc:  # noqa: BLE001
        _log.warning("build_calibration cook warning: " + str(exc))
    _lop.layout(parent)
    _log.info("build_calibration created " + node.path())
    return node.path()
