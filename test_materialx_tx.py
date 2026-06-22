"""
Tests for lh_houdini_pipeline.materialx.tx (imaketx integration).

Pure / dry-run -- runs OUTSIDE Houdini; the live imaketx run is verified
separately via the Houdini session.

    python test_materialx_tx.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

PASS = "\033[32mOK\033[0m"
FAIL = "\033[31mFAIL\033[0m"
errors = []


def check(label, fn):
    try:
        fn()
        print("  " + label.ljust(48) + " " + PASS)
    except Exception as e:
        print("  " + label.ljust(48) + " " + FAIL + "  " + str(e))
        errors.append((label, e))


print("\n=== imports (no hou) ===")

def _imp():
    from lh_houdini_pipeline.materialx.tx import (
        TxFormat, TxConversionSpec, MaketxPlanner, MaketxConverter,
        default_imaketx_exe,
    )
check("materialx.tx imports without hou", _imp)

from lh_houdini_pipeline.materialx.tx import (
    TxFormat, TxConversionSpec, MaketxPlanner, MaketxConverter, default_imaketx_exe,
)
from lh_houdini_pipeline.file.texture_parser import ColorSpace, TextureParser


print("\n=== format / exe ===")

def _format_ext():
    assert TxFormat.RAT.extension == "rat"
    assert TxFormat.EXR.extension == "tx"
    assert TxFormat.TIFF.extension == "tif"
check("TxFormat extensions", _format_ext)

def _exe_path():
    p = default_imaketx_exe("C:/HFS")
    assert p.endswith("imaketx.exe") or p.endswith("imaketx"), p
    assert "bin" in p
check("default_imaketx_exe builds bin/imaketx path", _exe_path)


print("\n=== planner ===")

_planner = MaketxPlanner(tx_format=TxFormat.RAT)

def _color_gets_colorconvert():
    spec = _planner.plan_path("/tex/hero_basecolor.exr", ColorSpace.SRGB)
    assert spec.does_colorconvert, "sRGB should colorconvert"
    assert spec.src_colorspace == "srgb_texture"
    assert spec.dst_colorspace == "scene_linear"
    assert spec.output.name == "hero_basecolor.rat", spec.output.name
check("sRGB texture -> colorconvert + .rat output", _color_gets_colorconvert)

def _raw_no_colorconvert():
    spec = _planner.plan_path("/tex/hero_rough.exr", ColorSpace.RAW)
    assert not spec.does_colorconvert
    assert not spec.use_ocio
    assert spec.linearize == 0, spec.linearize
check("raw texture -> no -c, no --ocio, linearize off", _raw_no_colorconvert)

def _png_output_drops_source_extension():
    spec = _planner.plan_path("/tex/hero_normal.png", ColorSpace.RAW)
    assert spec.output.name == "hero_normal.rat", spec.output.name
check("png texture -> .rat output, not .png.rat", _png_output_drops_source_extension)

def _normal_info_is_passthrough():
    parser = TextureParser()
    info = parser.parse("/tex/robot_Normal.png")
    spec = _planner.plan_info(info)
    cmd = spec.build_command("imaketx")
    assert spec.output.name == "robot_Normal.rat", spec.output.name
    assert "-c" not in cmd and "--ocio" not in cmd, cmd
    assert "-l" in cmd and cmd[cmd.index("-l") + 1] == "0", cmd
check("normal map conversion disables linearize", _normal_info_is_passthrough)

def _out_dir_override():
    spec = _planner.plan_path("/tex/a_normal.exr", ColorSpace.RAW, out_dir="/tx")
    assert str(spec.output).replace("\\", "/") == "/tx/a_normal.rat", spec.output
check("out_dir override applied", _out_dir_override)

def _bad_filter_rejected():
    raised = False
    try:
        MaketxPlanner(filter="nope")
    except ValueError:
        raised = True
    assert raised, "invalid filter should raise"
check("invalid filter rejected", _bad_filter_rejected)


print("\n=== command building ===")

def _cmd_color():
    spec = _planner.plan_path("/tex/c_basecolor.exr", ColorSpace.SRGB)
    cmd = spec.build_command("C:/HFS/bin/imaketx.exe")
    # positional infile/outfile come first
    assert cmd[0].endswith("imaketx.exe")
    assert cmd[1].endswith("c_basecolor.exr")
    assert cmd[2].endswith("c_basecolor.rat")
    assert "-f" in cmd and "catrom" in cmd
    assert "-F" in cmd and "RAT" in cmd
    assert "-c" in cmd
    i = cmd.index("-c")
    assert cmd[i + 1] == "srgb_texture" and cmd[i + 2] == "scene_linear"
    assert "--ocio" not in cmd  # -c and --ocio are mutually exclusive here
check("color command: infile/outfile + -c pair", _cmd_color)

def _cmd_raw_ocio():
    spec = _planner.plan_path("/tex/d_rough.exr", ColorSpace.RAW)
    cmd = spec.build_command("imaketx")
    assert "--ocio" not in cmd
    assert "-c" not in cmd
    assert "-l" in cmd and cmd[cmd.index("-l") + 1] == "0", cmd
    assert "--newer" in cmd
check("raw command: no color management, -l 0, --newer", _cmd_raw_ocio)


print("\n=== converter (dry-run, no process) ===")

def _dry_run_converter():
    parser = TextureParser()
    infos = [parser.parse("/tex/hero_BaseColor.exr"),
             parser.parse("/tex/hero_Roughness.exr")]
    specs = MaketxPlanner().plan_many(infos)
    conv = MaketxConverter(exe="imaketx", dry_run=True)
    results = conv.convert_many(specs)
    assert len(results) == 2
    assert all(r.success for r in results), "dry-run should report success"
    assert all(r.result.dry_run for r in results)
check("MaketxConverter dry-run builds 2 specs", _dry_run_converter)

def _on_each_progress_called():
    parser = TextureParser()
    infos = [parser.parse("/tex/a_BaseColor.exr"),
             parser.parse("/tex/a_Roughness.exr"),
             parser.parse("/tex/a_Normal.exr")]
    specs = MaketxPlanner().plan_many(infos)
    conv = MaketxConverter(exe="imaketx", dry_run=True)
    calls = []
    conv.convert_many(specs, on_each=lambda done, total, res: calls.append((done, total)))
    assert calls == [(1, 3), (2, 3), (3, 3)], calls
check("convert_many fires on_each with running count", _on_each_progress_called)


print("\n=== summary ===")
if errors:
    print("  " + str(len(errors)) + " FAILED")
    for label, e in errors:
        print("    - " + label + ": " + str(e))
    sys.exit(1)
print("  All tx assertions passed.")
sys.exit(0)
