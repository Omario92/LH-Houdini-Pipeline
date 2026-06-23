"""
test_tier0.py -- pure-Python assertions for the Tier-0 upgrade modules.

Covers: core.profiling, core.validators, core.config.bootstrap_config,
and the hou-lazy import safety of houdini.{traversal,parm,geometry}.
Runs outside Houdini:  python test_tier0.py
"""

from __future__ import annotations

import sys
import time

sys.path.insert(0, ".")

PASS = "OK"
_count = 0


def check(label: str, cond: bool) -> None:
    global _count
    _count += 1
    status = PASS if cond else "FAIL"
    print("  " + label.ljust(44) + status)
    if not cond:
        raise AssertionError(label)


def test_profiling() -> None:
    print("=== core.profiling ===")
    from lh_houdini_pipeline.core import profiling as P

    sw = P.Stopwatch("t").start()
    time.sleep(0.005)
    e = sw.stop()
    check("stopwatch measures > 0", e > 0)
    check("elapsed_ms frozen after stop", sw.elapsed_ms == e * 1000.0)

    calls = {"n": 0}

    @P.timed("decorated")
    def f(x):
        calls["n"] += 1
        return x * 2

    check("timed preserves return", f(21) == 42)
    check("timed preserves __name__", f.__name__ == "f")
    check("timed actually called fn", calls["n"] == 1)

    with P.timed_block("blk") as b:
        time.sleep(0.001)
    check("timed_block exposes stopwatch", b.elapsed_ms >= 0)

    check("mem_sample returns float or None",
          P.mem_sample() is None or isinstance(P.mem_sample(), float))


def test_validators() -> None:
    print("=== core.validators ===")
    from lh_houdini_pipeline.core import validators as V

    check("v012 is version token", V.is_version_token("v012"))
    check("parse v012 -> 12", V.parse_version_number("v012") == 12)
    check("parse _v3 -> 3", V.parse_version_number("shot_v3") == 3)
    check("parse hero -> None", V.parse_version_number("hero") is None)

    check("valid prim path", V.is_valid_prim_path("/ASSET/geo"))
    check("root '/' is valid", V.is_valid_prim_path("/"))
    check("leading digit invalid", not V.is_valid_prim_path("/ASSET/2bad"))
    check("space invalid", not V.is_valid_prim_path("/has space"))

    check("frame range valid", V.validate_frame_range(1001, 1050))
    check("reversed range invalid", not V.validate_frame_range(50, 1))

    try:
        V.require_extension("a.png", "exr", "tif")
        check("require_extension raises", False)
    except V.ValidationError:
        check("require_extension raises", True)


def test_config() -> None:
    print("=== core.config.bootstrap_config ===")
    from lh_houdini_pipeline.core import config as C

    p = C.default_config_path()
    check("defaults.yaml ships in package", p.exists())

    mgr = C.bootstrap_config()
    cfg = mgr.get("pipeline")
    check("render.engine == karma", cfg.get("render.engine") == "karma")
    check("dotted access works", cfg.get("cache.stale_after_days") == 14)
    check("missing key -> default", cfg.get("nope.nope", "d") == "d")


def test_hou_lazy_imports() -> None:
    print("=== houdini.* hou-lazy import safety ===")
    import importlib

    for mod in ("traversal", "parm", "geometry"):
        m = importlib.import_module("lh_houdini_pipeline.houdini." + mod)
        check(mod + " imports without hou", m is not None)


if __name__ == "__main__":
    test_profiling()
    test_validators()
    test_config()
    test_hou_lazy_imports()
    print("\nAll " + str(_count) + " Tier-0 assertions passed.")
