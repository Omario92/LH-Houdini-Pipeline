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
from typing import Any, List, Optional, Tuple

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.houdini import lop as _lop
from lh_houdini_pipeline.tools.camera_manager.core import (
    CAMERA_ANIM_PARMS,
    CameraContext,
    CameraSpec,
    CameraTiming,
    MergePlan,
    plan_merge,
)

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


def delete_camera(camera_path: str) -> bool:
    """Delete a camera node by path.

    Args:
        camera_path: Full path to the camera node (OBJ ``cam`` or LOP ``camera``).

    Returns:
        ``True`` if the node existed and was deleted, ``False`` otherwise.
    """
    node = _lop.get_node(camera_path)
    if node is None:
        _log.warning("delete_camera: node not found: " + camera_path)
        return False
    path = node.path()
    try:
        node.destroy()
    except Exception as exc:  # noqa: BLE001
        _log.error("delete_camera failed for " + path + ": " + str(exc))
        return False
    _log.info("Deleted camera " + path)
    return True


def camera_frame_range(
    camera_path: str, parms: Tuple[str, ...] = CAMERA_ANIM_PARMS
) -> Optional[Tuple[int, int]]:
    """Return ``(start, end)`` animated frame range of an OBJ camera, or ``None``.

    Scans the standard animatable camera parms for keyframes (Week 08).

    Args:
        camera_path: Path to an OBJ ``cam`` node.
        parms:       Parm names to inspect for animation.

    Returns:
        ``(start, end)`` if any parm is time-dependent, else ``None`` (static).
    """
    node = _lop.get_node(camera_path)
    if node is None:
        return None
    frames: List[float] = []
    for name in parms:
        parm = node.parm(name)
        if parm is not None and parm.isTimeDependent():
            frames.extend(kf.frame() for kf in parm.keyframes())
    if not frames:
        return None
    return int(min(frames)), int(max(frames))


def sync_playback_range(
    camera_path: str, fallback: Tuple[int, int] = (1001, 1050)
) -> Tuple[int, int]:
    """Set the Houdini playbar to *camera_path*'s animation range (Week 08).

    Args:
        camera_path: Path to an OBJ ``cam`` node.
        fallback:    Range to use when the camera is static.

    Returns:
        The ``(start, end)`` range that was applied.
    """
    import hou  # noqa: PLC0415
    rng = camera_frame_range(camera_path) or fallback
    start, end = rng
    hou.playbar.setFrameRange(start, end)
    hou.playbar.setPlaybackRange(start, end)
    hou.setFrame(start)
    _log.info("Playbar synced to " + str(start) + "-" + str(end) + " from " + camera_path)
    return rng


def merge_cameras(
    cameras: List[str],
    merged_name: str = "merged_camera",
    start_frame: int = 1001,
    parent_path: str = "/obj",
) -> Optional[str]:
    """Merge OBJ cameras sequentially into one (Week 08 + static-interp fix).

    Source cameras are placed end-to-end on a single timeline (see
    :func:`core.plan_merge`).  Animated parms are copied keyframe-by-keyframe
    with a frame offset; **static parms on an animated camera get explicit
    hold keyframes at both ends of their segment** so they don't drift by
    interpolation -- the key correctness fix from the course.

    Args:
        cameras:     Camera names (under ``parent_path``) or full node paths.
        merged_name: Name for the new merged camera.
        start_frame: First frame of the merged timeline.
        parent_path: Network holding the source cameras / new camera (``/obj``).

    Returns:
        Path to the merged camera, or ``None`` on failure.
    """
    import hou  # noqa: PLC0415

    parent = _lop.get_node(parent_path)
    if parent is None or len(cameras) < 1:
        _log.error("merge_cameras: bad parent or empty camera list.")
        return None

    # Resolve names -> nodes and build timings.
    nodes = {}
    timings: List[CameraTiming] = []
    for cam in cameras:
        path = cam if cam.startswith("/") else parent_path + "/" + cam
        node = _lop.get_node(path)
        if node is None:
            _log.warning("merge_cameras: skipping missing camera " + path)
            continue
        nodes[node.name()] = node
        rng = camera_frame_range(path)
        timings.append(CameraTiming(node.name(),
                                    rng[0] if rng else None,
                                    rng[1] if rng else None))
    if not timings:
        _log.error("merge_cameras: no valid source cameras.")
        return None

    plan = plan_merge(timings, start_frame=start_frame)
    merged = _lop.create_node(parent, "cam", merged_name, force=True)
    if merged is None:
        return None
    try:
        merged.setColor(hou.Color((0.3, 0.7, 0.3)))
    except Exception:  # noqa: BLE001
        pass

    with hou.undos.group("Merge " + str(len(plan.segments)) + " cameras"):
        for seg in plan.segments:
            src = nodes.get(seg.name)
            if src is None:
                continue
            for pname in CAMERA_ANIM_PARMS:
                src_parm = src.parm(pname)
                dst_parm = merged.parm(pname)
                if src_parm is None or dst_parm is None:
                    continue
                if seg.is_static:
                    _set_hold_key(dst_parm, seg.dst_start, src_parm.eval())
                elif src_parm.isTimeDependent():
                    for kf in src_parm.keyframes():
                        new_kf = hou.Keyframe()
                        new_kf.setFrame(kf.frame() + seg.offset)
                        new_kf.setValue(kf.value())
                        expr = kf.expression()
                        if expr:
                            new_kf.setExpression(expr, kf.expressionLanguage())
                        dst_parm.setKeyframe(new_kf)
                else:
                    # static parm on an animated camera -> hold at both ends
                    val = src_parm.eval()
                    _set_hold_key(dst_parm, seg.dst_start, val)
                    _set_hold_key(dst_parm, seg.dst_end, val)

    _lop.layout(parent)
    hou.playbar.setFrameRange(plan.start_frame, plan.end_frame)
    hou.playbar.setPlaybackRange(plan.start_frame, plan.end_frame)
    _log.info("Merged camera " + merged.path() + " (" + plan.summary() + ")")
    return merged.path()


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _set_hold_key(parm: Any, frame: int, value: float) -> None:
    """Insert a constant (hold) keyframe at *frame* with *value*."""
    import hou  # noqa: PLC0415
    kf = hou.Keyframe()
    kf.setFrame(frame)
    kf.setValue(value)
    parm.setKeyframe(kf)


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
