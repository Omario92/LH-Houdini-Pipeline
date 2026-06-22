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

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple


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
