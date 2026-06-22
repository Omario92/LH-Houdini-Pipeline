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

print("\n=== summary ===")
if errors:
    print("  "+str(len(errors))+" FAILED"); [print("    - "+l+": "+str(e)) for l,e in errors]; sys.exit(1)
print("  All camera_manager assertions passed."); sys.exit(0)
