"""
Tests for the TexToMtlx tool and the MaterialX planning layer.

Runs OUTSIDE Houdini -- exercises the pure pieces (scanner -> parser ->
planner -> dry-run) against a temporary fixture directory, then guards the
hou / PySide imports so it is informative both in and out of Houdini.

    cd "E:\OneDrive\Documents\Claude\Projects\LH Houdini Pipeline"
    python test_tex_to_mtlx.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

PASS = "\033[32mOK\033[0m"
FAIL = "\033[31mFAIL\033[0m"
SKIP = "\033[33mSKIP\033[0m"
errors = []


def check(label, fn):
    try:
        fn()
        print("  " + label.ljust(50) + " " + PASS)
    except Exception as e:
        print("  " + label.ljust(50) + " " + FAIL + "  " + str(e))
        errors.append((label, e))


def skip(label, reason):
    print("  " + label.ljust(50) + " " + SKIP + "  " + reason)


# ---------------------------------------------------------------------------
# Fixture: a temp folder of fake texture files (content irrelevant)
# ---------------------------------------------------------------------------

_FIXTURE_FILES = [
    # hero_car -- full MVP channel set, base color as two UDIM tiles
    "hero_car_BaseColor_1001.exr",
    "hero_car_BaseColor_1002.exr",
    "hero_car_Roughness_1001.exr",
    "hero_car_Metalness_1001.exr",
    "hero_car_Normal_1001.exr",
    "hero_car_Height_1001.exr",
    # metal_ball -- 'metal' prefix must survive material-name extraction
    "metal_ball_BaseColor.exr",
    "metal_ball_Roughness.exr",
    # an unrecognised map
    "random_lookup_table.exr",
]


def _make_fixture():
    d = tempfile.mkdtemp(prefix="tex2mtlx_")
    for name in _FIXTURE_FILES:
        open(os.path.join(d, name), "w").close()
    return d


FIXTURE = _make_fixture()


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

print("\n=== Imports (pure, no hou) ===")

def _imp_builder():
    from lh_houdini_pipeline.materialx.builder import (
        MaterialPlanner, MaterialBuildPlan, ImageNodeSpec, houdini_texture_path,
    )
check("materialx.builder", _imp_builder)

def _imp_connection():
    # Module import must not pull in hou.
    from lh_houdini_pipeline.materialx import connection
check("materialx.connection (no hou at import)", _imp_connection)

def _imp_tool():
    from lh_houdini_pipeline.tools.tex_to_mtlx import scan_and_plan, format_dry_run
check("tools.tex_to_mtlx (pure surface)", _imp_tool)

def _imp_service():
    # service imports hou lazily -> module import itself must succeed.
    from lh_houdini_pipeline.tools.tex_to_mtlx import service
check("tools.tex_to_mtlx.service (no hou at import)", _imp_service)


# ---------------------------------------------------------------------------
# Parser over the fixture directory
# ---------------------------------------------------------------------------

print("\n=== Parser ===")

from lh_houdini_pipeline.file.texture_parser import TextureParser, TextureChannel

_parser = TextureParser()
_infos = _parser.parse_directory(FIXTURE)

def _parsed_count():
    assert len(_infos) == len(_FIXTURE_FILES), str(len(_infos))
check("parse_directory finds all files", _parsed_count)

def _basecolor_detected():
    bc = [i for i in _infos if i.channel is TextureChannel.BASE_COLOR]
    assert len(bc) == 3, "expected 3 base color files, got " + str(len(bc))
check("base color channel detected", _basecolor_detected)


# ---------------------------------------------------------------------------
# Planner / scan_and_plan
# ---------------------------------------------------------------------------

print("\n=== Planning (dry-run) ===")

from lh_houdini_pipeline.tools.tex_to_mtlx import core as tool_core

_result = tool_core.scan_and_plan(FIXTURE)
_by_name = {p.name: p for p in _result.plans}

def _two_materials():
    assert set(_by_name) == {"hero_car", "metal_ball"}, str(set(_by_name))
check("groups into hero_car + metal_ball", _two_materials)

def _metal_prefix_survives():
    assert "metal_ball" in _by_name, "metal_ball prefix was stripped"
check("'metal' prefix not mistaken for channel", _metal_prefix_survives)

def _hero_channels():
    chans = set(c.value for c in _by_name["hero_car"].channels)
    expected = {"baseColor", "roughness", "metalness", "normal", "displacement"}
    assert chans == expected, str(chans)
check("hero_car covers all 5 MVP channels", _hero_channels)

def _udim_dedup():
    imgs = [i for i in _by_name["hero_car"].images
            if i.channel is TextureChannel.BASE_COLOR]
    assert len(imgs) == 1, "UDIM tiles not collapsed: " + str(len(imgs))
check("UDIM tiles collapse to one image spec", _udim_dedup)

def _udim_token_path():
    img = [i for i in _by_name["hero_car"].images
           if i.channel is TextureChannel.BASE_COLOR][0]
    assert "<UDIM>" in img.file_path, img.file_path
    assert "1001" not in img.file_path and "1002" not in img.file_path, img.file_path
check("UDIM path normalised to <UDIM>", _udim_token_path)

def _basecolor_rule():
    img = [i for i in _by_name["hero_car"].images
           if i.channel is TextureChannel.BASE_COLOR][0]
    assert img.mtlx_input == "base_color", img.mtlx_input
    assert img.colorspace == "srgb_texture", img.colorspace
    assert img.signature == "color3", img.signature
check("base color -> base_color / srgb / color3", _basecolor_rule)

def _roughness_rule():
    img = [i for i in _by_name["hero_car"].images
           if i.channel is TextureChannel.ROUGHNESS][0]
    assert img.mtlx_input == "specular_roughness", img.mtlx_input
    assert img.colorspace == "raw", img.colorspace
    assert img.signature == "default", img.signature
check("roughness -> specular_roughness / raw / default", _roughness_rule)

def _normal_signature():
    img = [i for i in _by_name["hero_car"].images
           if i.channel is TextureChannel.NORMAL][0]
    assert img.signature == "vector3", img.signature
    assert img.mtlx_input == "normal", img.mtlx_input
check("normal -> vector3 signature", _normal_signature)

def _displacement_flag():
    assert _by_name["hero_car"].has_displacement
check("hero_car.has_displacement is True", _displacement_flag)

def _unknown_reported():
    assert any("random_lookup_table" in u for u in _result.unknowns), str(_result.unknowns)
check("unrecognised map reported, not built", _unknown_reported)

def _dry_run_text():
    text = tool_core.format_dry_run(_result)
    assert "hero_car" in text and "base_color" in text
check("format_dry_run renders a report", _dry_run_text)

def _to_dict_serialisable():
    import json
    json.dumps(_by_name["hero_car"].to_dict())
check("plan.to_dict() is JSON-serialisable", _to_dict_serialisable)


# ---------------------------------------------------------------------------
# Houdini-only surfaces (guarded)
# ---------------------------------------------------------------------------

print("\n=== Houdini-only (guarded) ===")

try:
    import hou  # noqa: F401
    _HAS_HOU = True
except ImportError:
    _HAS_HOU = False

if _HAS_HOU:
    def _build_in_stage():
        import hou
        from lh_houdini_pipeline.tools.tex_to_mtlx import service
        stage = hou.node("/stage")
        matlib = stage.createNode("materiallibrary", "test_tex_to_mtlx")
        results = service.build_plans(list(_result.plans), prefer_path=matlib.path())
        assert any(r.created for r in results)
        matlib.destroy()
    check("build into /stage materiallibrary", _build_in_stage)

    def _ui_imports():
        from lh_houdini_pipeline.tools.tex_to_mtlx import ui
        assert hasattr(ui, "TexToMtlxWidget")
    check("ui module imports inside Houdini", _ui_imports)
else:
    skip("build into /stage materiallibrary", "hou not available")
    # UI import is expected to fail without PySide outside Houdini.
    try:
        from lh_houdini_pipeline.tools.tex_to_mtlx import ui  # noqa: F401
        check("ui module imports (PySide present)", lambda: None)
    except ImportError as exc:
        skip("ui module import", "PySide not installed: " + str(exc).split(" (")[0])


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print("\n=== Summary ===")
if errors:
    print("  " + str(len(errors)) + " FAILED")
    for label, e in errors:
        print("    - " + label + ": " + str(e))
    sys.exit(1)
print("  All assertions passed.")
sys.exit(0)
