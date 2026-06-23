"""
lh_houdini_pipeline.tools.lookdev_builder.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
One-click lookdev assembly: Asset + Light Rig + Turntable (Rebelway Week 10).

This is the capstone "super tool" that fuses three independently-verified
pieces into a single click, by *composition*:

    lops_asset_builder  -> USD component (geometry + materials + output)
    lookdev.light_rig   -> 3-point rig framed to the asset's bounds
    camera_manager      -> 360-degree turntable camera framed to the asset

It owns no USD-authoring logic of its own -- it sequences proven tools and
reports a single consolidated result.  Each stage is isolated so a failure in,
say, the light rig still leaves a valid built asset.

``hou`` is imported lazily (via the composed tools); imports for unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.core.profiling import timed
from lh_houdini_pipeline.tools.lookdev_builder.core import LookdevConfig

_log = get_logger(__name__)

# Progress hook: on_progress(step, total, label).
ProgressHook = Callable[[int, int, str], None]


@dataclass
class LookdevResult:
    """Consolidated result of a one-click lookdev build.

    Attributes:
        asset_name:   The asset that was built.
        output_node:  componentoutput node path (empty if asset build failed).
        light_nodes:  Created light node paths.
        camera_node:  Turntable camera node path (empty if skipped/failed).
        calibration_node: Calibration-plates LOP path (empty if skipped).
        errors:       Per-stage error strings (empty == clean run).
    """

    asset_name: str = ""
    output_node: str = ""
    light_nodes: List[str] = field(default_factory=list)
    camera_node: str = ""
    calibration_node: str = ""
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


@timed("lookdev_builder.build")
def build_lookdev(
    config: LookdevConfig,
    on_progress: Optional[ProgressHook] = None,
) -> LookdevResult:
    """Assemble a full lookdev scene from *config* in one call.

    Stages (each guarded so one failure does not abort the rest):

      1. Build the USD component asset.
      2. Build the 3-point light rig framed to the asset (if enabled).
      3. Build the turntable camera framed to the asset (if enabled).

    Args:
        config:      The :class:`LookdevConfig` describing what to build.
        on_progress: Optional ``on_progress(step, total, label)`` callback.

    Returns:
        A :class:`LookdevResult` with all created node paths + any errors.
    """
    from lh_houdini_pipeline.tools import lops_asset_builder as _lab
    from lh_houdini_pipeline.tools.asset_ingest import core as _ingest
    from lh_houdini_pipeline.lookdev import light_rig as _rig

    result = LookdevResult()
    total = config.step_count()
    step = 0

    def _emit(label: str) -> None:
        nonlocal step
        step += 1
        if on_progress is not None:
            try:
                on_progress(step, total, label)
            except Exception as exc:  # noqa: BLE001
                _log.debug("on_progress raised: " + str(exc))

    # -- 1) asset -------------------------------------------------------
    _emit("asset")
    # Derive name/textures from the file when not given (reuse ingestion logic).
    asset_name = config.asset_name
    tex_folder = config.tex_folder
    if config.geo_path is not None:
        if not asset_name:
            asset_name = _ingest.derive_asset_name(config.geo_path)
        if tex_folder is None:
            tex_folder = _ingest.find_texture_folder(config.geo_path)
    asset_name = asset_name or "asset"

    try:
        plan = _lab.plan_asset(
            asset_name=asset_name,
            geo_path=config.geo_path,
            tex_folder=tex_folder,
            output_dir=config.output_dir,
        )
        built = _lab.build_asset(plan, parent_path=config.parent_path)
        result.asset_name = built.asset_name
        result.output_node = built.output
    except Exception as exc:  # noqa: BLE001
        result.errors.append("asset: " + str(exc))
        _log.warning("build_lookdev asset stage failed: " + str(exc))
        return result  # nothing to frame lights/camera to

    target = result.output_node

    # -- 2) light rig ---------------------------------------------------
    if config.with_lights:
        _emit("lights")
        try:
            plan_rig = _rig.plan_rig((0.0, 0.0, 0.0), 1.0, dome_hdri=config.dome_hdri)
            result.light_nodes = _rig.build_light_rig(
                plan_rig, parent_path=config.parent_path, target_path=target,
            )
        except Exception as exc:  # noqa: BLE001
            result.errors.append("lights: " + str(exc))
            _log.warning("build_lookdev light stage failed: " + str(exc))

    # -- 3) turntable ---------------------------------------------------
    if config.with_turntable:
        _emit("turntable")
        try:
            from lh_houdini_pipeline.tools import camera_manager as _cam
            spec = _cam.TurntableSpec(total_frames=config.turntable_frames)
            cam_path = _cam.create_turntable(
                spec=spec, parent_path=config.parent_path, target_path=target,
            )
            result.camera_node = cam_path or ""
        except Exception as exc:  # noqa: BLE001
            result.errors.append("turntable: " + str(exc))
            _log.warning("build_lookdev turntable stage failed: " + str(exc))

    # -- 4) calibration plates -----------------------------------------
    if config.with_calibration:
        _emit("calibration")
        try:
            from lh_houdini_pipeline.lookdev import calibration as _cal
            # chain onto the last light (or the asset) so plates layer in
            upstream = result.light_nodes[-1] if result.light_nodes else target
            result.calibration_node = _cal.build_calibration(
                parent_path=config.parent_path, input_path=upstream,
            ) or ""
        except Exception as exc:  # noqa: BLE001
            result.errors.append("calibration: " + str(exc))
            _log.warning("build_lookdev calibration stage failed: " + str(exc))

    _log.info(
        "build_lookdev done: asset=" + result.asset_name
        + " lights=" + str(len(result.light_nodes))
        + " cam=" + (result.camera_node or "-")
        + " errors=" + str(len(result.errors))
    )
    return result
