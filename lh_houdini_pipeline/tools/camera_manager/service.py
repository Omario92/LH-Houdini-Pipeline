"""
lh_houdini_pipeline.tools.camera_manager.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Houdini-side camera creation and listing.

Node plumbing (create / set parms) is delegated to
:mod:`lh_houdini_pipeline.houdini.lop`; this module only resolves the build
context and maps a :class:`CameraSpec` onto the right node type.  All ``hou``
use is lazy, so importing the module never requires Houdini.

Node types / parms verified live on H21.0.631:
    * OBJ   -> ``cam``    (focal / aperture / resx / resy / near / far / fstop / focus)
    * STAGE -> ``camera`` (focalLength / horizontalAperture / verticalAperture /
                           clippingRange1,2 / fStop / focusDistance)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.houdini import lop as _lop
from lh_houdini_pipeline.tools.camera_manager.core import CameraContext, CameraSpec

_log = get_logger(__name__)

_CONTEXT_ROOT = {CameraContext.OBJ: "/obj", CameraContext.STAGE: "/stage"}
_CONTEXT_TYPE = {CameraContext.OBJ: "cam", CameraContext.STAGE: "camera"}


@dataclass
class CameraInfo:
    """Lightweight summary of a camera node found in the scene."""
    path:         str
    focal_length: float = 0.0
    resolution:   tuple = field(default_factory=tuple)


def create_camera(
    spec: CameraSpec,
    context: CameraContext = CameraContext.OBJ,
    parent_path: Optional[str] = None,
    force: bool = False,
) -> Optional[str]:
    """Create a camera for *spec* in *context* and return its node path.

    Args:
        spec:        The pure :class:`CameraSpec`.
        context:     OBJ object camera or STAGE USD camera.
        parent_path: Network to create in; defaults to ``/obj`` or ``/stage``.
        force:       Replace an existing same-named camera.

    Returns:
        The created node path, or ``None`` on failure.
    """
    parent = _lop.get_node(parent_path or _CONTEXT_ROOT[context])
    if parent is None:
        _log.error("Camera parent not found: " + (parent_path or _CONTEXT_ROOT[context]))
        return None

    node = _lop.create_node(parent, _CONTEXT_TYPE[context], spec.name, force=force)
    if node is None:
        return None

    set_count = _lop.set_parms(node, spec.to_parms(context))
    _lop.layout(parent)
    _log.info(
        "Created " + context.value + " camera " + node.path()
        + " (" + str(set_count) + " parms set)"
    )
    return node.path()


def list_cameras(context: CameraContext = CameraContext.OBJ) -> List[CameraInfo]:
    """List cameras in *context* with their focal length / resolution.

    Args:
        context: OBJ or STAGE.

    Returns:
        A list of :class:`CameraInfo`, sorted by node path.
    """
    root = _lop.get_node(_CONTEXT_ROOT[context])
    if root is None:
        return []
    type_name = _CONTEXT_TYPE[context]

    infos: List[CameraInfo] = []
    for node in root.allSubChildren():
        if node.type().name() != type_name:
            continue
        infos.append(_describe(node, context))
    infos.sort(key=lambda i: i.path)
    return infos


def apply_resolution(camera_path: str, width: int, height: int) -> bool:
    """Set ``resx``/``resy`` on an OBJ camera (USD cameras have no resolution).

    Args:
        camera_path: Path to an OBJ ``cam`` node.
        width:       Pixel width.
        height:      Pixel height.

    Returns:
        ``True`` if both parms were set, ``False`` otherwise.
    """
    node = _lop.get_node(camera_path)
    if node is None:
        _log.error("Camera not found: " + camera_path)
        return False
    n = _lop.set_parms(node, {"resx": int(width), "resy": int(height)})
    return n == 2


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _describe(node: Any, context: CameraContext) -> CameraInfo:
    """Read a camera node's key attributes into a :class:`CameraInfo`."""
    if context is CameraContext.OBJ:
        focal = _eval(node, "focal")
        res = (_eval(node, "resx"), _eval(node, "resy"))
        return CameraInfo(path=node.path(), focal_length=focal, resolution=res)
    focal = _eval(node, "focalLength")
    return CameraInfo(path=node.path(), focal_length=focal, resolution=())


def _eval(node: Any, parm_name: str) -> float:
    """Evaluate a parm, returning 0 if it's absent."""
    parm = node.parm(parm_name)
    try:
        return parm.eval() if parm is not None else 0
    except Exception:  # noqa: BLE001
        return 0
