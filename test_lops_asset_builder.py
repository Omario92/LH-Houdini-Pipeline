"""
Tests for tools.lops_asset_builder (pure planning). Runs OUTSIDE Houdini.

    python test_lops_asset_builder.py
"""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))

PASS="\033[32mOK\033[0m"; FAIL="\033[31mFAIL\033[0m"; errors=[]
def check(label, fn):
    try: fn(); print("  "+label.ljust(50)+" "+PASS)
    except Exception as e: print("  "+label.ljust(50)+" "+FAIL+"  "+str(e)); errors.append((label,e))

def _fixture(files):
    d=tempfile.mkdtemp(prefix="lh_asset_")
    for n in files: open(os.path.join(d,n),"w").close()
    return d

print("\n=== imports (no hou) ===")
def _imp():
    from lh_houdini_pipeline.tools.lops_asset_builder import plan_asset, AssetBuildPlan, MaterialAssignment
    from lh_houdini_pipeline.tools.lops_asset_builder import service  # hou lazy
check("lops_asset_builder imports without hou", _imp)

from lh_houdini_pipeline.tools.lops_asset_builder import plan_asset, MaterialAssignment

print("\n=== planning ===")
def _basic():
    p=plan_asset("Hero Prop 01")
    assert p.asset_name=="Hero_Prop_01", p.asset_name
    assert p.root_prim=="/Hero_Prop_01"
    assert p.output_file is None
    assert p.geo_path is None
    assert p.generate_proxy is False
    assert p.proxy_quality == "Medium"
check("name sanitised, defaults sane", _basic)

def _proxy_planning():
    p = plan_asset("Hero Prop 01", generate_proxy=True, proxy_quality="High")
    assert p.generate_proxy is True
    assert p.proxy_quality == "High"
check("proxy planning configuration", _proxy_planning)

def _output_file():
    p=plan_asset("box", output_dir="/out")
    assert p.output_file.endswith("/out/box.usd"), p.output_file
check("output_file built from output_dir", _output_file)

def _bad_ext():
    raised=False
    try: plan_asset("x", output_ext=".abc")
    except ValueError: raised=True
    assert raised
check("non-USD output_ext rejected", _bad_ext)

_single=_fixture(["hero_BaseColor.exr","hero_Roughness.exr","hero_Normal.exr"])
def _single_material():
    p=plan_asset("hero", tex_folder=_single)
    assert len(p.material_plans)==1, len(p.material_plans)
    assert len(p.assignments)==1
    assert p.assignments[0].primpattern=="%type:Mesh"
    assert p.assignments[0].material_name=="hero"
check("single material -> %type:Mesh binding", _single_material)

_multi=_fixture(["chair_BaseColor.exr","chair_Roughness.exr","cushion_BaseColor.exr"])
def _multi_material():
    p=plan_asset("set", tex_folder=_multi)
    assert len(p.material_plans)==2, [m.name for m in p.material_plans]
    assert len(p.assignments)==2
    pats=sorted(a.primpattern for a in p.assignments)
    assert all("%name:" in x for x in pats), pats
check("multi material -> per-material bindings", _multi_material)

def _explicit_assign():
    binds=[MaterialAssignment("/Hero/geo","hero")]
    p=plan_asset("hero", tex_folder=_single, assignments=binds)
    assert p.assignments==tuple(binds)
check("explicit assignments override default", _explicit_assign)

print("\n=== summary ===")
if errors:
    print("  "+str(len(errors))+" FAILED"); [print("    - "+l+": "+str(e)) for l,e in errors]; sys.exit(1)
print("  All lops_asset_builder assertions passed."); sys.exit(0)
