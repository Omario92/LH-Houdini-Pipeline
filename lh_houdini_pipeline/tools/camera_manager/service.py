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
    TurntableSpec,
    CameraFrameData,
    plan_merge,
    turntable_transforms,
    write_nuke_camera_script,
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


def create_turntable(
    spec: Optional[TurntableSpec] = None,
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    radius: float = 10.0,
    parent_path: str = "/stage",
    target_path: Optional[str] = None,
    name: Optional[str] = None,
) -> Optional[str]:
    """Create a 360-degree turntable camera in /stage (Week 10).

    Builds a Solaris ``camera`` LOP and keyframes its transform to orbit the
    asset; Houdini authors these as USD xform time-samples (one sample per
    ``Usd.TimeCode``), giving a USD-native turntable.  When *target_path* is a
    LOP node, the orbit *center* and *radius* are derived from that stage's
    world bounds; otherwise the explicit *center* / *radius* are used.

    Args:
        spec:        Turntable parameters; defaults to :class:`TurntableSpec`.
        center:      Orbit center (used when no *target_path*).
        radius:      Orbit radius (used when no *target_path*).
        parent_path: LOP network to build in (``/stage``).
        target_path: Optional LOP node to frame (derives center + radius).
        name:        Camera node name; defaults to ``spec.name``.

    Returns:
        The turntable camera node path, or ``None`` on failure.
    """
    import hou  # noqa: PLC0415

    spec = spec or TurntableSpec()
    parent = _lop.get_node(parent_path)
    if parent is None:
        _log.error("create_turntable: parent not found: " + parent_path)
        return None

    if target_path:
        derived = _bounds_center_radius(target_path)
        if derived is not None:
            center, radius = derived
            _log.info("Turntable framed to " + target_path
                      + " center=" + str(center) + " radius=" + str(round(radius, 2)))

    cam = _lop.create_node(parent, "camera", name or spec.name, force=True)
    if cam is None:
        return None
    _lop.set_parms(cam, {
        "focalLength": spec.focal_length,
        "horizontalAperture": spec.aperture,
        "verticalAperture": spec.aperture,
    })

    keys = turntable_transforms(spec, center=center, radius=radius)
    with hou.undos.group("Create turntable " + cam.name()):
        for key in keys:
            for pname, value in (
                ("tx", key.tx), ("ty", key.ty), ("tz", key.tz),
                ("rx", key.rx), ("ry", key.ry), ("rz", key.rz),
            ):
                parm = cam.parm(pname)
                if parm is not None:
                    kf = hou.Keyframe()
                    kf.setFrame(key.frame)
                    kf.setValue(value)
                    parm.setKeyframe(kf)

    frames = spec.frame_numbers()
    if frames:
        hou.playbar.setFrameRange(frames[0], frames[-1])
        hou.playbar.setPlaybackRange(frames[0], frames[-1])
        hou.setFrame(frames[0])
    _lop.layout(parent)
    _log.info("Created turntable " + cam.path() + " (" + str(len(keys)) + " frames)")
    return cam.path()


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _bounds_center_radius(target_path: str):
    """Best-effort orbit center + radius from a LOP node's world bounds.

    Returns ``(center, radius)`` or ``None`` if it cannot be computed (the
    caller then falls back to explicit values).
    """
    node = _lop.get_node(target_path)
    if node is None or not hasattr(node, "stage"):
        return None
    try:
        from pxr import Usd, UsdGeom  # noqa: PLC0415
        stage = node.stage()
        prim = stage.GetDefaultPrim() or stage.GetPseudoRoot()
        cache = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            [UsdGeom.Tokens.default_, UsdGeom.Tokens.render],
        )
        rng = cache.ComputeWorldBound(prim).ComputeAlignedRange()
        mn, mx = rng.GetMin(), rng.GetMax()
        center = ((mn[0] + mx[0]) / 2.0, (mn[1] + mx[1]) / 2.0, (mn[2] + mx[2]) / 2.0)
        max_dim = max(mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2])
        radius = max_dim * 2.5 if max_dim > 0 else 10.0
        return center, radius
    except Exception as exc:  # noqa: BLE001
        _log.warning("create_turntable: bounds compute failed (" + str(exc) + ")")
        return None


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


# ---------------------------------------------------------------------------
# Camera Export and Baking (USD / Alembic / Nuke .nk)
# ---------------------------------------------------------------------------

def get_camera_frames(camera_path: str, start_frame: int, end_frame: int) -> List[CameraFrameData]:
    """Extract world-space CameraFrameData from an OBJ or LOP camera over a range.

    Args:
        camera_path: Path to the camera node.
        start_frame: Start frame.
        end_frame:   End frame.

    Returns:
        List of CameraFrameData.
    """
    import hou  # noqa: PLC0415
    node = _lop.get_node(camera_path)
    if node is None:
        _log.error("get_camera_frames: Node not found: " + camera_path)
        return []

    is_lop = (node.type().name() == "camera")
    frames_data: List[CameraFrameData] = []

    if is_lop:
        from pxr import Usd, UsdGeom  # noqa: PLC0415
        stage = node.stage()
        prim_path = node.parm("primpath").eval() if node.parm("primpath") else "/" + node.name()
        prim = stage.GetPrimAtPath(prim_path)
        if not prim.IsValid():
            _log.error("get_camera_frames: LOP prim not found at " + prim_path)
            return []

        usd_cam = UsdGeom.Camera(prim)
        xformable = UsdGeom.Xformable(prim)

        for f in range(start_frame, end_frame + 1):
            time_code = Usd.TimeCode(f)
            # Compute world transform matrix
            matrix = xformable.ComputeLocalToWorldTransform(time_code)
            # Convert to hou.Matrix4 to explode
            flat_vals = list(matrix.GetFlat())
            hou_matrix = hou.Matrix4(flat_vals)
            exploded = hou_matrix.explode(rotate_order="xyz")
            tx, ty, tz = exploded["translate"]
            rx, ry, rz = exploded["rotate"]

            # Evaluate other attributes
            focal = usd_cam.GetFocalLengthAttr().Get(time_code)
            focal = focal if focal is not None else 50.0

            hap = usd_cam.GetHorizontalApertureAttr().Get(time_code)
            hap = hap if hap is not None else 41.4214

            vap = usd_cam.GetVerticalApertureAttr().Get(time_code)
            vap = vap if vap is not None else 41.4214
            
            near = 0.1
            far = 10000.0
            clipping = usd_cam.GetClippingRangeAttr().Get(time_code)
            if clipping:
                near, far = clipping[0], clipping[1]

            fstop = usd_cam.GetFStopAttr().Get(time_code)
            fstop = fstop if fstop is not None else 5.6

            focus = usd_cam.GetFocusDistanceAttr().Get(time_code)
            focus = focus if focus is not None else 5.0

            frames_data.append(CameraFrameData(
                frame=f, tx=tx, ty=ty, tz=tz, rx=rx, ry=ry, rz=rz,
                focal=focal, haperture=hap, vaperture=vap,
                near=near, far=far, fstop=fstop, focus=focus
            ))
    else:
        # OBJ camera
        for f in range(start_frame, end_frame + 1):
            time = hou.playbar.time(f)
            # Compute world transform
            hou_matrix = node.worldTransformAtTime(time)
            exploded = hou_matrix.explode(rotate_order="xyz")
            tx, ty, tz = exploded["translate"]
            rx, ry, rz = exploded["rotate"]

            focal = node.parm("focal").evalAtTime(time) if node.parm("focal") else 50.0
            hap = node.parm("aperture").evalAtTime(time) if node.parm("aperture") else 41.4214
            
            # Derive vertical aperture
            resx = node.parm("resx").evalAtTime(time) if node.parm("resx") else 1920.0
            resy = node.parm("resy").evalAtTime(time) if node.parm("resy") else 1080.0
            vap = hap * (resy / resx) if resx else hap

            near = node.parm("near").evalAtTime(time) if node.parm("near") else 0.1
            far = node.parm("far").evalAtTime(time) if node.parm("far") else 10000.0
            fstop = node.parm("fstop").evalAtTime(time) if node.parm("fstop") else 5.6
            focus = node.parm("focus").evalAtTime(time) if node.parm("focus") else 5.0

            frames_data.append(CameraFrameData(
                frame=f, tx=tx, ty=ty, tz=tz, rx=rx, ry=ry, rz=rz,
                focal=focal, haperture=hap, vaperture=vap,
                near=near, far=far, fstop=fstop, focus=focus
            ))

    return frames_data


def bake_camera_to_usd(
    camera_path: str,
    output_path: str,
    start_frame: int,
    end_frame: int,
) -> bool:
    """Bake an OBJ or LOP camera's animation to a standalone USD file.

    Args:
        camera_path: Path to the camera node.
        output_path: Destination USD file path.
        start_frame: First frame of baked animation.
        end_frame:   Last frame of baked animation.

    Returns:
        True if baking succeeded, False otherwise.
    """
    from pxr import Usd, UsdGeom, Gf  # noqa: PLC0415
    import os  # noqa: PLC0415

    frames_data = get_camera_frames(camera_path, start_frame, end_frame)
    if not frames_data:
        return False

    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        # If file exists, remove it so CreateNew succeeds
        if os.path.exists(output_path):
            os.remove(output_path)

        stage = Usd.Stage.CreateNew(output_path)
        stage.SetMetadata("startFrame", float(start_frame))
        stage.SetMetadata("endFrame", float(end_frame))

        root_prim = stage.DefinePrim("/root", "Xform")
        stage.SetDefaultPrim(root_prim)

        # Create camera prim
        cam_prim = stage.DefinePrim("/root/camera", "Camera")
        usd_cam = UsdGeom.Camera(cam_prim)
        xformable = UsdGeom.Xformable(cam_prim)
        
        # Clear existing ops and add a single transform matrix op
        xformable.ClearXformOpOrder()
        transform_op = xformable.AddTransformOp()

        for fd in frames_data:
            time_code = Usd.TimeCode(fd.frame)

            # Reconstruct Gf.Matrix4d from translation/rotation (XYZ Euler)
            m = Gf.Matrix4d()
            m.SetTranslate(Gf.Vec3d(fd.tx, fd.ty, fd.tz))
            m.SetRotate(Gf.Rotation(Gf.Vec3d(1, 0, 0), fd.rx) *
                        Gf.Rotation(Gf.Vec3d(0, 1, 0), fd.ry) *
                        Gf.Rotation(Gf.Vec3d(0, 0, 1), fd.rz))

            transform_op.Set(m, time_code)

            # Set camera attributes
            usd_cam.GetFocalLengthAttr().Set(fd.focal, time_code)
            usd_cam.GetHorizontalApertureAttr().Set(fd.haperture, time_code)
            usd_cam.GetVerticalApertureAttr().Set(fd.vaperture, time_code)
            usd_cam.GetClippingRangeAttr().Set(Gf.Vec2f(fd.near, fd.far), time_code)
            usd_cam.GetFStopAttr().Set(fd.fstop, time_code)
            usd_cam.GetFocusDistanceAttr().Set(fd.focus, time_code)

        stage.GetRootLayer().Save()
        _log.info("Baked camera " + camera_path + " to USD: " + output_path)
        return True
    except Exception as exc:
        _log.error("bake_camera_to_usd failed: " + str(exc))
        return False


def export_camera_to_alembic(
    camera_path: str,
    output_path: str,
    start_frame: int,
    end_frame: int,
) -> bool:
    """Export an OBJ or LOP camera to an Alembic (.abc) file.

    Args:
        camera_path: Path to the camera node.
        output_path: Destination Alembic file path.
        start_frame: Start frame.
        end_frame:   End frame.

    Returns:
        True if export succeeded, False otherwise.
    """
    import hou  # noqa: PLC0415
    import os  # noqa: PLC0415

    node = _lop.get_node(camera_path)
    if node is None:
        _log.error("export_camera_to_alembic: Camera node not found: " + camera_path)
        return False

    is_lop = (node.type().name() == "camera")
    temp_obj_cam = None

    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if is_lop:
            # LOP camera must be baked onto a temp OBJ camera first
            frames_data = get_camera_frames(camera_path, start_frame, end_frame)
            if not frames_data:
                return False

            temp_obj_cam = hou.node("/obj").createNode("cam", "temp_abc_bake_cam")
            for fd in frames_data:
                for pname, val in [
                    ("tx", fd.tx), ("ty", fd.ty), ("tz", fd.tz),
                    ("rx", fd.rx), ("ry", fd.ry), ("rz", fd.rz),
                    ("focal", fd.focal), ("aperture", fd.haperture),
                    ("near", fd.near), ("far", fd.far),
                    ("fstop", fd.fstop), ("focus", fd.focus),
                ]:
                    parm = temp_obj_cam.parm(pname)
                    if parm is not None:
                        kf = hou.Keyframe()
                        kf.setFrame(fd.frame)
                        kf.setValue(val)
                        parm.setKeyframe(kf)
                
                # set resolution to match aspect ratio
                if fd.haperture:
                    resx = 1920.0
                    resy = 1920.0 * (fd.vaperture / fd.haperture)
                    temp_obj_cam.parm("resx").set(int(resx))
                    temp_obj_cam.parm("resy").set(int(resy))

            export_target_path = temp_obj_cam.path()
        else:
            export_target_path = camera_path

        # Create temporary Alembic ROP in /out
        out_node = hou.node("/out")
        rop = out_node.createNode("alembic", "abc_export_temp")
        rop.parm("filename").set(output_path)
        rop.parm("objects").set(export_target_path)
        rop.parm("trange").set(1)  # Render Frame Range
        rop.parm("f1").set(start_frame)
        rop.parm("f2").set(end_frame)
        
        # Cook/Execute ROP
        rop.parm("execute").pressButton()
        rop.destroy()

        _log.info("Exported camera " + camera_path + " to Alembic: " + output_path)
        return True

    except Exception as exc:
        _log.error("export_camera_to_alembic failed: " + str(exc))
        return False

    finally:
        if temp_obj_cam is not None:
            try:
                temp_obj_cam.destroy()
            except Exception:
                pass


def export_camera(
    camera_path: str,
    output_dir: str,
    file_name_base: str,
    formats: List[str],
    start_frame: int,
    end_frame: int,
) -> Dict[str, str]:
    """Export a camera to multiple formats (usd, alembic, nuke).

    Args:
        camera_path:    Path to the camera node (OBJ or LOP).
        output_dir:     Directory to write the files to.
        file_name_base: Filename base (without extension).
        formats:        List of formats: 'usd', 'alembic', 'nuke'.
        start_frame:    First frame.
        end_frame:      Last frame.

    Returns:
        Dict mapping format name to exported file path.
    """
    import os  # noqa: PLC0415
    results = {}
    
    # Ensure dir exists
    os.makedirs(output_dir, exist_ok=True)
    
    node = _lop.get_node(camera_path)
    if node is None:
        _log.error("export_camera: Camera node not found: " + camera_path)
        return results

    if "nuke" in formats:
        nk_path = os.path.join(output_dir, file_name_base + ".nk")
        frames_data = get_camera_frames(camera_path, start_frame, end_frame)
        if frames_data:
            if write_nuke_camera_script(node.name(), frames_data, nk_path):
                results["nuke"] = nk_path
            else:
                _log.error("Failed to export Nuke script to " + nk_path)

    if "usd" in formats:
        usd_path = os.path.join(output_dir, file_name_base + ".usd")
        if bake_camera_to_usd(camera_path, usd_path, start_frame, end_frame):
            results["usd"] = usd_path
        else:
            _log.error("Failed to bake camera to USD: " + usd_path)

    if "alembic" in formats:
        abc_path = os.path.join(output_dir, file_name_base + ".abc")
        if export_camera_to_alembic(camera_path, abc_path, start_frame, end_frame):
            results["alembic"] = abc_path
        else:
            _log.error("Failed to export camera to Alembic: " + abc_path)

    return results

