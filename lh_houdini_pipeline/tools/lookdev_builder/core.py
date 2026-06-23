"""
lh_houdini_pipeline.tools.lookdev_builder.core
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pure configuration for the one-click Lookdev super-tool (Rebelway Week 10).

Holds only the *intent* of a lookdev build (what to include, how to name it).
The actual orchestration is in :mod:`service`; keeping the config pure makes it
trivial to test and to drive from a headless batch as well as the UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

PathLike = Union[str, Path]


@dataclass(frozen=True)
class LookdevConfig:
    """Everything the super-tool needs to assemble a lookdev scene.

    Attributes:
        geo_path:        Geometry file to ingest (``None`` builds default geo).
        asset_name:      Explicit asset name; ``None`` derives from the file.
        tex_folder:      Texture folder; ``None`` auto-detects beside the geo.
        with_lights:     Build the 3-point light rig.
        with_turntable:  Build the 360-degree turntable camera.
        with_calibration: Build chrome/grey/Macbeth calibration plates.
        dome_hdri:       Optional HDRI for an ambient dome light.
        turntable_frames: Frames for a full spin.
        output_dir:      Optional directory to write the component USD.
        parent_path:     LOP network to build everything in.
    """

    geo_path: Optional[PathLike] = None
    asset_name: Optional[str] = None
    tex_folder: Optional[PathLike] = None
    with_lights: bool = True
    with_turntable: bool = True
    with_calibration: bool = True
    dome_hdri: Optional[str] = None
    turntable_frames: int = 120
    output_dir: Optional[PathLike] = None
    parent_path: str = "/stage"

    def step_count(self) -> int:
        """Number of build stages this config will run (for progress bars)."""
        return (1 + int(self.with_lights) + int(self.with_turntable)
                + int(self.with_calibration))
