"""
Smoke tests for lh_houdini_pipeline core + file layers.
Run from the project root:

    cd "E:\OneDrive\Documents\Claude\Projects\LH Houdini Pipeline"
    python test_smoke.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

PASS = "\033[32mOK\033[0m"
FAIL = "\033[31mFAIL\033[0m"
errors = []


def check(label, fn):
    try:
        fn()
        print("  " + label.ljust(45) + " " + PASS)
    except Exception as e:
        print("  " + label.ljust(45) + " " + FAIL + "  " + str(e))
        errors.append((label, e))


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

print("\n=== Imports ===")

def _import_core_path():
    from lh_houdini_pipeline.core.path import PathTemplate, PathResolver, normalize
check("core.path", _import_core_path)

def _import_core_config():
    from lh_houdini_pipeline.core.config import Config, ConfigManager, ConfigLoader, ConfigError
check("core.config", _import_core_config)

def _import_core_logger():
    from lh_houdini_pipeline.core.logger import get_logger, LogContext, setup_pipeline_logging
check("core.logger", _import_core_logger)

def _import_core_executor():
    from lh_houdini_pipeline.core.executor import Executor, CommandResult, RetryPolicy, ThreadedExecutor
check("core.executor", _import_core_executor)

def _import_core_validators():
    from lh_houdini_pipeline.core.validators import validate_path_exists, validate_extension
check("core.validators", _import_core_validators)

def _import_core_reload():
    from lh_houdini_pipeline.core.reload import reload_package
check("core.reload", _import_core_reload)

def _import_file_texture_parser():
    from lh_houdini_pipeline.file.texture_parser import (
        TextureParser, TextureInfo, TextureChannel, ColorSpace, UDIMMode
    )
check("file.texture_parser", _import_file_texture_parser)

def _import_file_versioning():
    from lh_houdini_pipeline.file.versioning import (
        Version, VersionFormat, VersionedFile, VersionResolver, VersionError
    )
check("file.versioning", _import_file_versioning)

def _import_file_scanner():
    from lh_houdini_pipeline.file.scanner import find_files
check("file.scanner", _import_file_scanner)

def _import_file_cache():
    from lh_houdini_pipeline.file.cache_utils import detect_frame_range
check("file.cache_utils", _import_file_cache)

def _import_mtlx_rules():
    from lh_houdini_pipeline.materialx.rules import get_rule, CHANNEL_RULES
check("materialx.rules", _import_mtlx_rules)

# ---------------------------------------------------------------------------
# PathTemplate
# ---------------------------------------------------------------------------

print("\n=== PathTemplate ===")

from lh_houdini_pipeline.core.path import PathTemplate, PathResolver

def _tmpl_missing():
    t = PathTemplate("/jobs/{show}/{sequence}/sh{shot}/houdini/")
    missing = t.missing_variables({})
    assert missing == ["show", "sequence", "shot"], str(missing)
check("missing_variables", _tmpl_missing)

def _tmpl_format():
    t = PathTemplate("/jobs/{show}/{sequence}/sh{shot}/houdini/")
    result = t.format(show="darkStar", sequence="sq010", shot="0100")
    assert result == "/jobs/darkStar/sq010/sh0100/houdini/", str(result)
check("format (full)", _tmpl_format)

def _tmpl_partial():
    t = PathTemplate("/jobs/{show}/{sequence}/sh{shot}/")
    p = t.format_partial(show="darkStar")
    assert p.is_satisfied_by({"sequence": "sq010", "shot": "0100"})
    assert not p.is_satisfied_by({"sequence": "sq010"})
check("format_partial", _tmpl_partial)

# ---------------------------------------------------------------------------
# PathResolver
# ---------------------------------------------------------------------------

print("\n=== PathResolver ===")

def _resolver_resolve():
    r = PathResolver(show="darkStar", sequence="sq010", shot="0100")
    result = r.resolve("/jobs/{show}/{sequence}/sh{shot}/")
    assert result == "/jobs/darkStar/sq010/sh0100/", str(result)
check("resolve", _resolver_resolve)

def _resolver_overrides_immutable():
    r = PathResolver(show="darkStar", shot="0100")
    copy = r.with_overrides(shot="0200")
    assert copy.get("shot") == "0200"
    assert r.get("shot") == "0100"
check("with_overrides (immutable)", _resolver_overrides_immutable)

def _resolver_try_resolve():
    r = PathResolver(show="darkStar")
    result = r.try_resolve("/jobs/{show}/{missing}/")
    assert result is None
    result2 = r.try_resolve("/jobs/{show}/hip/", default="fallback")
    assert result2 == "/jobs/darkStar/hip/"
check("try_resolve", _resolver_try_resolve)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

print("\n=== Config ===")

from lh_houdini_pipeline.core.config import Config, ConfigError

def _config_get():
    cfg = Config({"project": {"fps": 24, "name": "darkStar"}, "paths": {"root": "/jobs"}})
    assert cfg.get("project.fps") == 24
    assert cfg.get("project.name") == "darkStar"
    assert cfg.get("nonexistent", "fallback") == "fallback"
check("get (dotted key)", _config_get)

def _config_require():
    cfg = Config({"project": {"fps": 24}})
    assert cfg.require("project.fps") == 24
    try:
        cfg.require("project.missing")
        assert False, "should have raised"
    except ConfigError:
        pass
check("require (missing raises)", _config_require)

def _config_merge():
    cfg = Config({"project": {"fps": 24, "name": "darkStar"}})
    cfg2 = cfg.merged_with(Config({"project": {"fps": 48}}))
    assert cfg2.get("project.fps") == 48
    assert cfg2.get("project.name") == "darkStar"
check("merged_with (deep merge)", _config_merge)

def _config_immutable():
    cfg = Config({"a": 1})
    try:
        cfg.a = 2
        assert False, "should have raised"
    except TypeError:
        pass
check("immutable (setattr raises)", _config_immutable)

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

print("\n=== Version ===")

from lh_houdini_pipeline.file.versioning import (
    Version, VersionFormat, VersionResolver, VersionError
)

def _version_parse_v3():
    v = Version.parse("fx_sh0100_v007.hip")
    assert v.number == 7 and v.fmt == VersionFormat.V3 and str(v) == "v007"
check("parse V3", _version_parse_v3)

def _version_parse_v2():
    v = Version.parse("render_v03.exr")
    assert v.number == 3 and v.fmt == VersionFormat.V2 and str(v) == "v03"
check("parse V2", _version_parse_v2)

def _version_parse_v1():
    v = Version.parse("asset_v5.usd")
    assert v.number == 5 and v.fmt == VersionFormat.V1 and str(v) == "v5"
check("parse V1", _version_parse_v1)

def _version_parse_missing():
    try:
        Version.parse("no_version_here.txt")
        assert False, "should have raised"
    except VersionError:
        pass
check("parse missing raises", _version_parse_missing)

def _version_compare():
    assert Version(7, VersionFormat.V3) == Version(7, VersionFormat.V1)
    assert Version(7, VersionFormat.V3) > Version(6, VersionFormat.V3)
    vlist = [Version(3, VersionFormat.V3), Version(1, VersionFormat.V3), Version(2, VersionFormat.V3)]
    expected = [Version(1, VersionFormat.V3), Version(2, VersionFormat.V3), Version(3, VersionFormat.V3)]
    assert sorted(vlist) == expected
check("comparison (format-agnostic)", _version_compare)

def _version_next_prev():
    v = Version(7, VersionFormat.V3)
    assert v.next().number == 8
    assert v.prev().number == 6
    try:
        Version(1, VersionFormat.V3).prev()
        assert False, "should raise"
    except VersionError:
        pass
check("next / prev", _version_next_prev)

def _version_inject():
    result = VersionResolver.inject_version("fx_sh0100_v001.hip", Version(7, VersionFormat.V3))
    assert result == "fx_sh0100_v007.hip", str(result)
check("VersionResolver.inject_version", _version_inject)

def _version_try_parse():
    assert VersionResolver.try_parse("no_version_here.txt") is None
    v = VersionResolver.try_parse("cache_v012.bgeo.sc")
    assert v is not None and v.number == 12
check("VersionResolver.try_parse", _version_try_parse)

# ---------------------------------------------------------------------------
# TextureParser
# ---------------------------------------------------------------------------

print("\n=== TextureParser ===")

from lh_houdini_pipeline.file.texture_parser import (
    TextureParser, TextureChannel, ColorSpace, UDIMMode
)

parser = TextureParser()

def _tp_base_color_udim():
    info = parser.parse("char_hero_BaseColor_1001.png")
    assert info.channel == TextureChannel.BASE_COLOR
    assert info.colorspace == ColorSpace.SRGB
    assert info.udim_mode == UDIMMode.MARI
    assert info.is_tiled
check("BaseColor UDIM (MARI 1001)", _tp_base_color_udim)

def _tp_normal():
    info = parser.parse("rock_Normal_GL.exr")
    assert info.channel == TextureChannel.NORMAL
    assert info.colorspace == ColorSpace.RAW
    assert not info.is_tiled
check("Normal (no UDIM)", _tp_normal)

def _tp_roughness():
    info = parser.parse("metal_Roughness.tx")
    assert info.channel == TextureChannel.ROUGHNESS
    assert info.colorspace == ColorSpace.RAW
check("Roughness", _tp_roughness)

def _tp_udim_hash():
    info = parser.parse("wood_BaseColor_####.exr")
    assert info.is_tiled
    assert info.udim_mode == UDIMMode.HOUDINI
check("BaseColor UDIM (Houdini ####)", _tp_udim_hash)

def _tp_group_by_channel():
    infos = parser.parse_many([
        "char_BaseColor_1001.png",
        "char_Roughness_1001.png",
        "char_Metalness_1001.png",
    ])
    groups = parser.group_by_channel(infos)
    assert TextureChannel.BASE_COLOR in groups
    assert TextureChannel.ROUGHNESS in groups
    assert len(groups[TextureChannel.BASE_COLOR]) == 1
check("group_by_channel", _tp_group_by_channel)

# ---------------------------------------------------------------------------
# MaterialX rules
# ---------------------------------------------------------------------------

print("\n=== MaterialX rules ===")

from lh_houdini_pipeline.materialx.rules import get_rule, CHANNEL_RULES
from lh_houdini_pipeline.file.texture_parser import TextureChannel

def _mtlx_base_color():
    rule = get_rule(TextureChannel.BASE_COLOR)
    assert rule is not None
    assert rule.mtlx_input == "base_color"
    assert rule.colorspace == "srgb_texture"
check("BASE_COLOR rule", _mtlx_base_color)

def _mtlx_normal():
    rule = get_rule(TextureChannel.NORMAL)
    assert rule.mtlx_input == "normal"
    assert rule.colorspace == "raw"
check("NORMAL rule", _mtlx_normal)

def _mtlx_unknown():
    rule = get_rule(TextureChannel.UNKNOWN)
    assert rule is None
check("UNKNOWN returns None", _mtlx_unknown)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print()
if errors:
    print("\033[31m" + str(len(errors)) + " test(s) FAILED:\033[0m")
    for label, exc in errors:
        print("  - " + label + ": " + str(exc))
    sys.exit(1)
else:
    count = 30
    print("\033[32mAll " + str(count) + " smoke tests passed.\033[0m")
