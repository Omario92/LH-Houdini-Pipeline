"""
test_asset_ingest.py -- pure assertions for the Asset Ingestion pipeline.

Covers core (classification, name derivation, texture discovery, expansion,
plan_ingest) and the importability of the drag-drop handler. No Houdini.
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, ".")

from lh_houdini_pipeline.tools.asset_ingest import core as IC

_count = 0


def check(label: str, cond: bool) -> None:
    global _count
    _count += 1
    print("  " + label.ljust(48) + ("OK" if cond else "FAIL"))
    assert cond, label


def test_classification() -> None:
    print("=== classification ===")
    check("fbx is geometry", IC.is_geometry_file("a.fbx"))
    check("bgeo.sc is geometry", IC.is_geometry_file("a.bgeo.sc"))
    check("png is not geometry", not IC.is_geometry_file("a.png"))


def test_name_derivation() -> None:
    print("=== derive_asset_name ===")
    check("strip version+date", IC.derive_asset_name("rock_v003_2024-01-12.fbx") == "rock")
    check("spaces -> underscore", IC.derive_asset_name("Tree Trunk.obj") == "Tree_Trunk")
    check("leading digit guarded", IC.derive_asset_name("123mesh.abc") == "a_123mesh")
    check("compound ext stripped", IC.derive_asset_name("smoke.bgeo.sc") == "smoke")
    check("collapse repeats", IC.derive_asset_name("a__b.obj") == "a_b")


def test_textures_and_expand() -> None:
    print("=== textures + expand ===")
    with tempfile.TemporaryDirectory() as d:
        obj = os.path.join(d, "rock_v002.obj")
        open(obj, "w").close()
        open(os.path.join(d, "rock_basecolor.png"), "w").close()
        open(os.path.join(d, "readme.txt"), "w").close()
        # flat layout: textures sit beside the geo
        check("flat tex folder detected", IC.find_texture_folder(obj) == d)
        # expand folder -> only geometry
        files = IC.expand_inputs([d])
        check("expand finds 1 geo", files == [obj])

        # sibling textures/ folder takes precedence
        sub = os.path.join(d, "textures")
        os.makedirs(sub)
        open(os.path.join(sub, "rock.exr"), "w").close()
        check("named tex folder detected", IC.find_texture_folder(obj) == sub)


def test_plan_ingest() -> None:
    print("=== plan_ingest ===")
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "chair_v001.fbx"), "w").close()
        open(os.path.join(d, "table.obj"), "w").close()
        open(os.path.join(d, "notes.txt"), "w").close()
        items = IC.plan_ingest([d])
        names = sorted(it.asset_name for it in items)
        check("two assets planned", names == ["chair", "table"])
        check("items are IngestItem", all(isinstance(it, IC.IngestItem) for it in items))


def test_dragdrop_import() -> None:
    print("=== drag-drop handler ===")
    sys.path.insert(0, "scripts")
    import importlib
    mod = importlib.import_module("externaldragdrop")
    check("dropAccept defined", hasattr(mod, "dropAccept"))
    check("drop_accept alias", mod.drop_accept is mod.dropAccept)
    check("empty list -> False", mod.dropAccept([]) is False)
    check("non-geo -> False", mod.dropAccept(["/tmp/foo.txt"]) is False)


if __name__ == "__main__":
    test_classification()
    test_name_derivation()
    test_textures_and_expand()
    test_plan_ingest()
    test_dragdrop_import()
    print("\nAll " + str(_count) + " Asset Ingestion assertions passed.")
