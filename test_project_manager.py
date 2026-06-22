"""
Tests for tools.project_manager. Runs OUTSIDE Houdini; filesystem creation is
exercised for real against a temp directory.

    python test_project_manager.py
"""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
PASS="\033[32mOK\033[0m"; FAIL="\033[31mFAIL\033[0m"; errors=[]
def check(label, fn):
    try: fn(); print("  "+label.ljust(50)+" "+PASS)
    except Exception as e: print("  "+label.ljust(50)+" "+FAIL+"  "+str(e)); errors.append((label,e))

print("\n=== imports (no hou) ===")
def _imp():
    from lh_houdini_pipeline.tools.project_manager import (
        plan_project, ProjectPlan, ProjectTemplate, create_project,
        scan_projects, next_work_version, set_houdini_job, work_file_template)
    from lh_houdini_pipeline.tools.project_manager import service
check("project_manager imports without hou", _imp)

from lh_houdini_pipeline.tools.project_manager import (
    plan_project, create_project, scan_projects, next_work_version, work_file_template)

print("\n=== planning ===")
def _basic_plan():
    p=plan_project("/jobs","Dark Star", assets=["hero"], shots=["sh0010","sh0020"])
    assert p.project=="Dark_Star", p.project
    assert p.project_root=="/jobs/Dark_Star"
    # project folders present
    assert "/jobs/Dark_Star/houdini/scenes" in p.directories
    # asset folders
    assert "/jobs/Dark_Star/assets/hero/lookdev" in p.directories
    # shot folders for both shots
    assert "/jobs/Dark_Star/shots/sh0010/fx" in p.directories
    assert "/jobs/Dark_Star/shots/sh0020/render" in p.directories
check("plan includes project/asset/shot folders", _basic_plan)

def _dedup_sorted():
    p=plan_project("/jobs","x")
    assert list(p.directories)==sorted(set(p.directories)), "dirs must be sorted+unique"
check("directories sorted and de-duplicated", _dedup_sorted)

def _empty_name():
    raised=False
    try: plan_project("/jobs","___")
    except ValueError: raised=True
    assert raised
check("empty project name rejected", _empty_name)

def _work_tmpl():
    p=plan_project("/jobs","show")
    t=work_file_template(p)
    assert "{entity}" in t and "{department}" in t and "{version:03d}" in t, t
    assert "/jobs/show/houdini/scenes/" in t, t
check("work_file_template partial-resolves root/project", _work_tmpl)

print("\n=== filesystem (real) ===")
_tmp=tempfile.mkdtemp(prefix="lh_pm_")
def _dry_run():
    p=plan_project(_tmp,"proj_dry", assets=["a1"])
    r=create_project(p, dry_run=True)
    assert r.dry_run and len(r.created)>0
    assert not os.path.isdir(os.path.join(_tmp,"proj_dry")), "dry-run must not write"
check("dry-run writes nothing", _dry_run)

def _real_create():
    p=plan_project(_tmp,"proj_real", assets=["hero"], shots=["sh0010"])
    r=create_project(p, dry_run=False)
    assert r.ok and len(r.created)==len(p.directories), r.summary()
    assert os.path.isdir(os.path.join(_tmp,"proj_real","houdini","scenes"))
    assert os.path.isdir(os.path.join(_tmp,"proj_real","assets","hero","tex"))
    assert os.path.isdir(os.path.join(_tmp,"proj_real","shots","sh0010","light"))
    # second run -> all existed, none created
    r2=create_project(p, dry_run=False)
    assert len(r2.created)==0 and len(r2.existed)==len(p.directories)
check("create_project makes dirs; idempotent", _real_create)

def _scan():
    names=scan_projects(_tmp)
    assert "proj_real" in names, names
check("scan_projects lists created project", _scan)

def _next_version():
    work=os.path.join(_tmp,"proj_real","houdini","scenes")
    v=next_work_version(work, pattern="*.hip")
    assert v.number==1, v.number   # nothing saved yet -> v001
check("next_work_version is v1 on empty dir", _next_version)

print("\n=== summary ===")
if errors:
    print("  "+str(len(errors))+" FAILED"); [print("    - "+l+": "+str(e)) for l,e in errors]; sys.exit(1)
print("  All project_manager assertions passed."); sys.exit(0)
