"""
lh_houdini_pipeline.lookdev
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Lighting / LookDev domain layer.

Modules:
    light_rig   -- programmatic 3-point light rig builder (pure math + hou)
    turntable   -- turntable camera / animation helpers
    calibration -- grey ball / chrome ball calibration utilities
"""

from __future__ import annotations

from lh_houdini_pipeline.lookdev.calibration import (
    CalibrationPlan,
    build_calibration,
    chart_layout,
    macbeth_linear,
    srgb_to_linear,
)
from lh_houdini_pipeline.lookdev.light_rig import (
    LightRigPlan,
    LightRole,
    LightSpec,
    build_light_rig,
    look_at_rotation,
    plan_rig,
    three_point_rig,
)

__all__ = [
    "LightRole",
    "LightSpec",
    "LightRigPlan",
    "look_at_rotation",
    "three_point_rig",
    "plan_rig",
    "build_light_rig",
    "CalibrationPlan",
    "build_calibration",
    "chart_layout",
    "macbeth_linear",
    "srgb_to_linear",
]
