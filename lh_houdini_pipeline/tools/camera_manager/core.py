"""
lh_houdini_pipeline.tools.camera_manager.core
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pure camera description + parameter mapping -- NO ``hou``.

A :class:`CameraSpec` holds resolution-independent camera attributes and knows
how to translate itself into the parm dict for either an OBJ ``cam`` node or a
Solaris ``camera`` LOP (their parm names differ -- verified live on
H21.0.631).  Keeping the mapping pure makes it unit-testable outside Houdini
and keeps the ``service`` layer a thin node-creation shell.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class CameraContext(Enum):
    """Where a camera lives."""
    OBJ   = "obj"     # /obj  -> 'cam' object node
    STAGE = "stage"   # /stage -> 'camera' LOP (USD)


class ResolutionPreset(Enum):
    """Common output resolutions as ``(width, height)``."""
    HD720     = (1280, 720)
    HD1080    = (1920, 1080)
    UHD4K     = (3840, 2160)
    CINEMA2K  = (2048, 1080)
    CINEMA4K  = (4096, 2160)
    SQUARE1K  = (1024, 1024)
    SQUARE2K  = (2048, 2048)

    @property
    def width(self) -> int:
        return self.value[0]

    @property
    def height(self) -> int:
        return self.value[1]

    @property
    def aspect(self) -> float:
        """Height / width pixel aspect of the frame."""
        return self.value[1] / self.value[0]


@dataclass(frozen=True)
class CameraSpec:
    """Resolution-independent camera attributes.

    Defaults match Houdini's stock camera (35 mm-ish, 41.4214 mm aperture).

    Attributes:
        name:                Node name.
        focal_length:        Focal length in millimetres.
        horizontal_aperture: Horizontal film-back aperture in millimetres.
        vertical_aperture:   Vertical aperture; ``None`` derives it from the
                             resolution aspect (or the horizontal aperture).
        near:                Near clipping distance.
        far:                 Far clipping distance.
        fstop:               Lens f-stop.
        focus_distance:      Focus distance.
        resolution:          Optional ``(w, h)`` output resolution.
    """
    name:                str   = "cam1"
    focal_length:        float = 50.0
    horizontal_aperture: float = 41.4214
    vertical_aperture:   Optional[float] = None
    near:                float = 0.1
    far:                 float = 10000.0
    fstop:               float = 5.6
    focus_distance:      float = 5.0
    resolution:          Optional[Tuple[int, int]] = None

    def effective_vertical_aperture(self) -> float:
        """Return the vertical aperture, deriving it when not set explicitly.

        Priority: explicit value -> horizontal * resolution-aspect -> equal to
        the horizontal aperture (square fallback).
        """
        if self.vertical_aperture is not None:
            return self.vertical_aperture
        if self.resolution is not None and self.resolution[0]:
            return self.horizontal_aperture * (self.resolution[1] / self.resolution[0])
        return self.horizontal_aperture

    def to_parms(self, context: CameraContext) -> Dict[str, Any]:
        """Return the ``{parm_name: value}`` mapping for *context*.

        Parm names verified live on Houdini 21.0.631.

        Args:
            context: Target :class:`CameraContext`.

        Returns:
            A dict ready for ``houdini.lop.set_parms``.  Resolution is included
            for OBJ cameras only (USD cameras carry no resolution -- that lives
            on the render settings prim).
        """
        if context is CameraContext.OBJ:
            parms: Dict[str, Any] = {
                "focal":   self.focal_length,
                "aperture": self.horizontal_aperture,
                "near":    self.near,
                "far":     self.far,
                "fstop":   self.fstop,
                "focus":   self.focus_distance,
            }
            if self.resolution is not None:
                parms["resx"] = int(self.resolution[0])
                parms["resy"] = int(self.resolution[1])
            return parms

        # Solaris USD camera
        return {
            "focalLength":        self.focal_length,
            "horizontalAperture": self.horizontal_aperture,
            "verticalAperture":   self.effective_vertical_aperture(),
            "clippingRange1":     self.near,
            "clippingRange2":     self.far,
            "fStop":              self.fstop,
            "focusDistance":      self.focus_distance,
        }


def spec_from_preset(
    name: str,
    preset: ResolutionPreset,
    focal_length: float = 50.0,
    fstop: float = 5.6,
) -> CameraSpec:
    """Build a :class:`CameraSpec` from a resolution preset.

    The vertical aperture is derived from the preset's aspect ratio so the
    camera is non-distorting at that resolution.

    Args:
        name:         Camera node name.
        preset:       A :class:`ResolutionPreset`.
        focal_length: Focal length in mm.
        fstop:        Lens f-stop.

    Returns:
        A populated :class:`CameraSpec`.
    """
    return CameraSpec(
        name=name,
        focal_length=focal_length,
        fstop=fstop,
        resolution=(preset.width, preset.height),
    )


# ---------------------------------------------------------------------------
# Camera merging (Week 08: sequential merge + static-interpolation fix)
# ---------------------------------------------------------------------------

#: OBJ camera parms checked for animation / copied when merging.
CAMERA_ANIM_PARMS: Tuple[str, ...] = (
    "tx", "ty", "tz", "rx", "ry", "rz", "focal", "aperture", "fstop",
)


@dataclass(frozen=True)
class CameraTiming:
    """Source-camera timing for a merge.

    Attributes:
        name:  Camera name / identifier.
        start: First animated frame, or ``None`` for a static camera.
        end:   Last animated frame, or ``None`` for a static camera.
    """
    name:  str
    start: Optional[int] = None
    end:   Optional[int] = None

    @property
    def is_static(self) -> bool:
        """``True`` if the camera has no animation range."""
        return self.start is None or self.end is None


@dataclass(frozen=True)
class MergeSegment:
    """One camera's placement on the merged timeline.

    Attributes:
        name:      Source camera name.
        is_static: ``True`` if the source had no animation.
        offset:    Frame offset added to source keyframes (animated only).
        src_start: Source first frame (animated only).
        src_end:   Source last frame (animated only).
        dst_start: First frame this segment occupies on the merged timeline.
        dst_end:   Last frame this segment occupies on the merged timeline.
    """
    name:      str
    is_static: bool
    offset:    int
    src_start: Optional[int]
    src_end:   Optional[int]
    dst_start: int
    dst_end:   int


@dataclass(frozen=True)
class MergePlan:
    """Ordered placement of all source cameras on a single merged timeline."""
    segments:    Tuple[MergeSegment, ...]
    start_frame: int
    end_frame:   int

    def summary(self) -> str:
        """One-line human summary for logs / status labels."""
        return (
            str(len(self.segments)) + " camera(s) -> frames "
            + str(self.start_frame) + "-" + str(self.end_frame)
        )


def plan_merge(timings: List[CameraTiming], start_frame: int = 1001) -> MergePlan:
    """Lay source cameras end-to-end on one timeline (pure; Week 08 algorithm).

    Animated cameras come first (ordered by their start frame, then name);
    static cameras follow. Each animated camera keeps its internal length and
    is shifted so segments never overlap; each static camera occupies a single
    frame.

    Args:
        timings:     Per-camera :class:`CameraTiming`.
        start_frame: First frame of the merged timeline (default ``1001``).

    Returns:
        A :class:`MergePlan` with one :class:`MergeSegment` per camera.
    """
    def _key(t: CameraTiming):
        return (0, t.start, t.name) if not t.is_static else (1, 0, t.name)

    ordered = sorted(timings, key=_key)
    segments: List[MergeSegment] = []
    cur = start_frame

    for t in ordered:
        if not t.is_static:
            offset = cur - int(t.start)
            dst_start = cur
            dst_end = cur + (int(t.end) - int(t.start))
            segments.append(MergeSegment(
                t.name, False, offset, int(t.start), int(t.end), dst_start, dst_end))
            cur += (int(t.end) - int(t.start) + 1)
        else:
            segments.append(MergeSegment(t.name, True, 0, None, None, cur, cur))
            cur += 1

    return MergePlan(tuple(segments), start_frame, cur - 1)


# ---------------------------------------------------------------------------
# Turntable (Week 10: 360-degree lookdev spin)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TurntableSpec:
    """Parameters for a 360-degree lookdev turntable camera.

    Defaults follow the Week 10 lookdev convention (square 1:1 frame).

    Attributes:
        total_frames: Number of frames for a full 360-degree spin.
        start_frame:  First frame of the spin.
        pitch_deg:    Downward pitch of the camera (degrees).
        focal_length: Focal length (mm).
        aperture:     Horizontal == vertical aperture (mm) -> 1:1 frame.
        name:         Camera node name.
    """
    total_frames: int   = 120
    start_frame:  int   = 1
    pitch_deg:    float = 20.0
    focal_length: float = 35.0
    aperture:     float = 10.0
    name:         str   = "turntable_cam"

    def angle_at(self, index: int) -> float:
        """Spin angle (degrees) at *index* frames into the turntable."""
        return (index / self.total_frames) * 360.0 if self.total_frames else 0.0

    def frame_numbers(self) -> List[int]:
        """The absolute frame numbers the turntable spans."""
        return list(range(self.start_frame, self.start_frame + self.total_frames))


@dataclass(frozen=True)
class TurntableKey:
    """One frame of a turntable orbit: a camera translate + rotate sample."""
    frame: int
    tx: float
    ty: float
    tz: float
    rx: float
    ry: float
    rz: float


def turntable_transforms(
    spec: TurntableSpec,
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    radius: float = 10.0,
) -> List[TurntableKey]:
    """Compute the per-frame orbit transform for a turntable camera (pure).

    The camera orbits *center* on a circle of *radius* in the XZ plane, raised
    by ``radius * tan(pitch)`` and pitched down by ``spec.pitch_deg`` so it
    always frames the asset.  A Houdini/USD camera looks down its local -Z, so
    ``ry`` equals the spin angle (camera faces inward) and ``rx`` is the
    constant downward pitch.

    Args:
        spec:   The :class:`TurntableSpec` (frame count, pitch, etc.).
        center: World-space point to orbit.
        radius: Orbit radius.

    Returns:
        One :class:`TurntableKey` per turntable frame.
    """
    cx, cy, cz = center
    pitch = spec.pitch_deg
    height = radius * math.tan(math.radians(pitch))
    keys: List[TurntableKey] = []
    for i, frame in enumerate(spec.frame_numbers()):
        angle = spec.angle_at(i)
        a = math.radians(angle)
        keys.append(TurntableKey(
            frame=frame,
            tx=cx + radius * math.sin(a),
            ty=cy + height,
            tz=cz + radius * math.cos(a),
            rx=-pitch,
            ry=angle,
            rz=0.0,
        ))
    return keys
