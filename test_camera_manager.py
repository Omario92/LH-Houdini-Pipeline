"""
Tests for tools.camera_manager (pure spec + parm mapping). Outside Houdini.

    python test_camera_manager.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
PASS="\033[32mOK\033[0m"; FAIL="\033[31mFAIL\033[0m"; errors=[]
def check(label, fn):
    try: fn(); print("  "+label.ljust(50)+" "+PASS)
    except Exception as e: print("  "+label.ljust(50)+" "+FAIL+"  "+str(e)); errors.append((label,e))

print("\n=== imports (no hou) ===")
def _imp():
    from lh_houdini_pipeline.tools.camera_manager import (
        CameraSpec, CameraContext, ResolutionPreset, spec_from_preset,
        create_camera, list_cameras)
    from lh_houdini_pipeline.tools.camera_manager import service
check("camera_manager imports without hou", _imp)

from lh_houdini_pipeline.tools.camera_manager import (
    CameraSpec, CameraContext, ResolutionPreset, spec_from_preset)

print("\n=== presets ===")
def _preset_dims():
    assert ResolutionPreset.HD1080.width==1920 and ResolutionPreset.HD1080.height==1080
    assert abs(ResolutionPreset.HD1080.aspect-0.5625) < 1e-6
check("ResolutionPreset dims/aspect", _preset_dims)

print("\n=== OBJ parm mapping ===")
def _obj_parms():
    spec=spec_from_preset("camA", ResolutionPreset.HD1080, focal_length=35.0, fstop=2.8)
    p=spec.to_parms(CameraContext.OBJ)
    assert p["focal"]==35.0 and p["fstop"]==2.8
    assert p["aperture"]==41.4214
    assert p["resx"]==1920 and p["resy"]==1080
    assert "near" in p and "far" in p and "focus" in p
    # OBJ mapping must NOT use USD parm names
    assert "focalLength" not in p
check("OBJ cam parms (focal/aperture/resx/resy)", _obj_parms)

print("\n=== Stage (USD) parm mapping ===")
def _stage_parms():
    spec=spec_from_preset("camB", ResolutionPreset.HD1080, focal_length=85.0)
    p=spec.to_parms(CameraContext.STAGE)
    assert p["focalLength"]==85.0
    assert p["horizontalAperture"]==41.4214
    assert "clippingRange1" in p and "clippingRange2" in p
    assert "fStop" in p and "focusDistance" in p
    # USD camera carries no resolution
    assert "resx" not in p and "resolution" not in p
check("USD camera parms (focalLength/clippingRange/...)", _stage_parms)

def _vertical_aperture_derived():
    spec=spec_from_preset("camC", ResolutionPreset.HD1080)  # 16:9
    p=spec.to_parms(CameraContext.STAGE)
    # vertical = horizontal * 1080/1920
    expected = 41.4214 * (1080/1920)
    assert abs(p["verticalAperture"]-expected) < 1e-6, p["verticalAperture"]
check("vertical aperture derived from aspect", _vertical_aperture_derived)

def _explicit_vertical():
    spec=CameraSpec(name="x", vertical_aperture=24.0)
    assert spec.effective_vertical_aperture()==24.0
check("explicit vertical aperture honoured", _explicit_vertical)

def _square_default_vertical():
    spec=CameraSpec(name="x")  # no resolution, no vertical
    assert spec.effective_vertical_aperture()==spec.horizontal_aperture
check("no resolution -> vertical == horizontal", _square_default_vertical)
print("\n=== merge planning (pure) ===")
from lh_houdini_pipeline.tools.camera_manager import CameraTiming, plan_merge, TurntableSpec

def _merge_two_animated():
    plan = plan_merge([CameraTiming("A",1,10), CameraTiming("B",5,8)], start_frame=1001)
    segs = {s.name: s for s in plan.segments}
    # A first (start 1): offset 1000, dst 1001..1010
    assert segs["A"].offset==1000 and segs["A"].dst_start==1001 and segs["A"].dst_end==1010, segs["A"]
    # B next: starts at 1011, offset 1011-5=1006, dst 1011..1014
    assert segs["B"].dst_start==1011 and segs["B"].offset==1006 and segs["B"].dst_end==1014, segs["B"]
    assert plan.end_frame==1014, plan.end_frame
check("merge: two animated cams placed end-to-end", _merge_two_animated)

def _merge_static_after_animated():
    plan = plan_merge([CameraTiming("stat"), CameraTiming("anim",1,5)], start_frame=1001)
    segs = {s.name: s for s in plan.segments}
    # animated first (1001..1005), static occupies single frame 1006
    assert segs["anim"].dst_start==1001 and segs["anim"].dst_end==1005
    assert segs["static" if "static" in segs else "stat"].is_static
    assert segs["stat"].dst_start==1006 and segs["stat"].dst_end==1006, segs["stat"]
    assert plan.end_frame==1006
check("merge: static camera placed after animated", _merge_static_after_animated)

def _turntable_angles():
    tt = TurntableSpec(total_frames=120, start_frame=1)
    assert tt.angle_at(0)==0.0
    assert tt.angle_at(60)==180.0
    assert tt.angle_at(120)==360.0
    assert tt.frame_numbers()[0]==1 and tt.frame_numbers()[-1]==120
check("turntable: angle_at sweeps 0..360", _turntable_angles)


print("\n=== summary ===")
if errors:
    print("  "+str(len(errors))+" FAILED"); [print("    - "+l+": "+str(e)) for l,e in errors]; sys.exit(1)
print("  All camera_manager assertions passed."); sys.exit(0)
