"""
test_lookdev.py -- pure assertions for the lookdev layer.

Covers lookdev.light_rig (look-at math, 3-point ratios, plan) and
tools.lookdev_builder.core (LookdevConfig). No Houdini.
"""

from __future__ import annotations

import math
import sys

sys.path.insert(0, ".")

from lh_houdini_pipeline.lookdev import light_rig as LR
from lh_houdini_pipeline.lookdev import calibration as CAL
from lh_houdini_pipeline.tools.lookdev_builder.core import LookdevConfig

_count = 0


def check(label: str, cond: bool) -> None:
    global _count
    _count += 1
    print("  " + label.ljust(46) + ("OK" if cond else "FAIL"))
    assert cond, label


def test_look_at() -> None:
    print("=== look_at_rotation ===")
    check("front +Z -> (0,0,0)", LR.look_at_rotation((0, 0, 10), (0, 0, 0)) == (0.0, 0.0, 0.0))
    r = LR.look_at_rotation((0, 10, 0), (0, 0, 0))
    check("straight down -> pitch -90", abs(r[0] + 90.0) < 1e-6)
    r = LR.look_at_rotation((10, 0, 0), (0, 0, 0))
    check("from +X -> yaw +-90", abs(abs(r[1]) - 90.0) < 1e-6)
    check("degenerate -> zeros", LR.look_at_rotation((1, 1, 1), (1, 1, 1)) == (0.0, 0.0, 0.0))


def test_three_point() -> None:
    print("=== three_point_rig ===")
    specs = LR.three_point_rig((0, 0, 0), 2.0)
    check("three lights", len(specs) == 3)
    check("roles ordered", [s.role.value for s in specs] == ["key", "fill", "rim"])
    k, f, rm = specs
    check("fill dimmer than key", f.intensity < k.intensity)
    check("rim between fill and key", f.intensity < rm.intensity < k.intensity)
    check("all sphere lights", all(s.light_type == "UsdLuxSphereLight" for s in specs))
    # distance scales with max_dim
    near = LR.three_point_rig((0, 0, 0), 1.0)[0].position
    far = LR.three_point_rig((0, 0, 0), 10.0)[0].position
    check("distance scales with size",
          math.hypot(*far) > math.hypot(*near))
    # rotations are finite and aim inward (rough: key in +x so yaw negative-ish)
    check("rotations finite", all(math.isfinite(v) for v in k.rotation))


def test_plan_and_config() -> None:
    print("=== plan_rig + LookdevConfig ===")
    plan = LR.plan_rig((0, 0, 0), 2.0, dome_hdri="/x/studio.exr")
    check("plan has 3 lights", len(plan.lights) == 3)
    check("plan carries dome", plan.dome_hdri.endswith(".exr"))

    c_full = LookdevConfig(geo_path="/x/rock.fbx")
    check("full step_count == 4", c_full.step_count() == 4)
    c_asset = LookdevConfig(with_lights=False, with_turntable=False, with_calibration=False)
    check("asset-only step_count == 1", c_asset.step_count() == 1)
    c_mid = LookdevConfig(with_lights=True, with_turntable=False, with_calibration=False)
    check("asset+lights step_count == 2", c_mid.step_count() == 2)


def test_calibration() -> None:
    print("=== calibration plates ===")
    check("24 macbeth swatches", len(CAL.MACBETH_SRGB) == 24)
    lin = CAL.macbeth_linear()
    check("white patch ~1.0 linear", lin[18][0] > 0.85)
    check("black patch low linear", lin[23][0] < 0.06)
    check("srgb_to_linear(0.5)~0.214", abs(CAL.srgb_to_linear(0.5) - 0.2140) < 2e-3)
    layout = CAL.chart_layout(0.3)
    check("24 patches laid out", len(layout) == 24)
    check("grid centered on x", abs(sum(p.x for p in layout) / 24) < 1e-9)
    check("6x4 rows/cols", layout[-1].row == 3 and layout[-1].col == 5)
    plan = CAL.CalibrationPlan(size=2.0, with_chrome=False)
    rt = CAL.CalibrationPlan.from_json(plan.to_json())
    check("plan json round-trip", rt.size == 2.0 and rt.with_chrome is False)


if __name__ == "__main__":
    test_look_at()
    test_three_point()
    test_plan_and_config()
    test_calibration()
    print("\nAll " + str(_count) + " lookdev assertions passed.")
